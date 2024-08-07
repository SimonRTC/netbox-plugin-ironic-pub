from datetime import datetime
from django_tables2 import RequestConfig
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from dcim.models import Device
from netbox.views import generic
from extras.models import ObjectChange, JournalEntry
from utilities.paginator import EnhancedPaginator
from utilities.views import ViewTab, register_model_view
from .core import OpenstackConnector
from .tables import AtelierActionTable, AtelierInterfaceTable
from .models import AtelierAction
from .utils import get_baremetal_node_id
from .exception import AtelierException
from urllib.parse import urlparse
from extras.plugins import get_plugin_config


class AtelierViewTab(ViewTab):
    def render(self, instance):
        """Return the attributes needed to render a tab in HTML."""
        self._instance = instance
        badge_value = self._get_badge_value(instance)
        
        # Condition not to display the tab if info does not exist
        if self.hide_if_empty and get_baremetal_node_id(instance) is None:
            return None
        
        if self.badge and self.hide_if_empty and not badge_value:
            return None
        
        return {
            'label': self.label,
            'badge': badge_value,
            'weight': self.weight,
        }

class AtelierEnhancedPaginator(EnhancedPaginator):
    default_page_lengths = (
        25, 50, 100, 250, 500
    )

@register_model_view(Device, 'atelier', path='atelier')
class AtelierView(generic.ObjectView):
    template_name = 'netbox_ironic/atelier.html'

    queryset = Device.objects.all()

    tab = AtelierViewTab(
        label='Atelier',
        weight=200,
        hide_if_empty=True
    )

    def __init__(self):
        self._os_connector = None
        self._ironic_info = None
        self._baremetal_node_id = None

    @property
    def os_connector(self):
        if self._os_connector is None:
            try:
                self._os_connector = OpenstackConnector()
            except AtelierException as e:
                self._os_connector = None
                raise e
        return self._os_connector
    
    @property
    def ironic_info(self):
        if self._ironic_info is None:
            try:
                self._ironic_info = self.os_connector.get_ironic_info(self._baremetal_node_id)
            except AtelierException as e:
                self._ironic_info = None
                raise e
        return self._ironic_info
    
    def get_extra_context(self, request, instance):
        to_return = {}
        
        # Try for Openstack connector
        try:
            _ = self.os_connector
        except AtelierException as e:
            messages.add_message(request, e.type, e.message)
            to_return['error'] = True
            return to_return
        
        to_return['error'] = False
        atelier_actions = []
        self._baremetal_node_id = get_baremetal_node_id(instance)
        
        # Try for ironic info        
        try:
            to_return['ironic_info'] = self.ironic_info
            instance_uuid = self.ironic_info["instance_uuid"]
            for node_action in self.os_connector.get_node_actions(self.ironic_info):
                action = AtelierAction(time=datetime.strptime(node_action['created_at'], "%Y-%m-%dT%H:%M:%S%z"),
                                       request_id=node_action['uuid'],
                                       action=node_action['severity'].lower(),
                                       message=node_action['event'],
                                       owner='ironic',
                                       source='node')
                atelier_actions.append(action)
        
            atelier_id = settings.PLUGINS_CONFIG['netbox_ironic'].get('ATELIER_PROPERTY_NAME')
            atelier_url = None
            if "properties" in self.ironic_info and atelier_id in self.ironic_info["properties"]:
                atelier_prefix = settings.PLUGINS_CONFIG['netbox_ironic'].get('ATELIER_PREFIX_URL')
                atelier_url = f'{atelier_prefix}{str(self.ironic_info["properties"][atelier_id])}'
            to_return['atelier_url'] = atelier_url
        except AtelierException as e:
            instance_uuid = None
            to_return['ironic_info'] = None
            to_return['atelier_url'] = None
            messages.add_message(request, e.type, e.message)
        
        if instance_uuid is not None:
            
            # Try for nova info
            try:
                nova_info = self.os_connector.get_nova_info(instance_uuid)
                for server_action in self.os_connector.get_server_actions(nova_info):
                    action = AtelierAction(time=datetime.strptime("%s+00:00" % server_action['start_time'], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                           request_id=server_action['request_id'],
                                           action=server_action['action'],
                                           message=server_action['message'],
                                           owner=server_action['user_id'],
                                           source='server')
                    atelier_actions.append(action)
            except AtelierException as e:
                nova_info = None
                messages.add_message(request, e.type, e.message)
            
            # Try for neutron info (port)
            try:
                neutron_info = self.os_connector.get_port_info(instance_uuid)
            except AtelierException as e:
                neutron_info = None
                messages.add_message(request, e.type, e.message)
        
        else:
            nova_info = None
            neutron_info = None
        to_return['nova_info'] = nova_info

        network_names = None
        if neutron_info is not None:
            network_ids = list(set([item.network_id for item in neutron_info]))
            network_names = {}
            for network_id in network_ids:
                try:
                    network_names[network_id] = self.os_connector.get_network_info(network_id)['name']  
                except AtelierException as e:
                    messages.add_message(request, e.type, e.message)

        # Gather all changes for this object (and its related objects)
        content_type = ContentType.objects.get_for_model(instance)
        objectchanges = ObjectChange.objects.restrict(request.user, 'view').prefetch_related(
            'user', 'changed_object_type'
        ).filter(
            Q(changed_object_type=content_type, changed_object_id=instance.pk) |
            Q(related_object_type=content_type, related_object_id=instance.pk)
        )

        journalentries = JournalEntry.objects.restrict(request.user, 'view').prefetch_related('created_by').filter(
            assigned_object_type=content_type,
            assigned_object_id=instance.pk
        )

        for changelog in objectchanges:
            action = AtelierAction(time=changelog.time,
                                   request_id=changelog.request_id,
                                   action=changelog.action,
                                   message="%s %s %s" % (changelog.action, changelog.changed_object_type, changelog.object_repr),
                                   owner=changelog.user_name,
                                   source='Changelog')
            action.get_absolute_url = changelog.get_absolute_url
            atelier_actions.append(action)

        for journal in journalentries:
            action = AtelierAction(time=journal.created,
                                   request_id="",
                                   action=journal.kind,
                                   message=journal.comments,
                                   owner=journal.created_by,
                                   source='journal')
            action.get_absolute_url = journal.get_absolute_url
            atelier_actions.append(action)

        atelier_actions = sorted(atelier_actions, key=lambda d: d.time, reverse=True)
        atelier_actions_table = to_return['history'] = AtelierActionTable(atelier_actions)
        
        paginate = {
            'paginator_class': AtelierEnhancedPaginator,
            'per_page': 25
        }
        RequestConfig(request, paginate=paginate).configure(atelier_actions_table)

        hostname = urlparse(get_plugin_config('netbox_ironic', 'OS_AUTH_URL')).hostname
        horizon_hostname = hostname.replace('keystone', 'horizon')
        to_return['horizon_url'] = f'https://{horizon_hostname}/admin/ironic/{str(self._baremetal_node_id)}'
        
        to_return['interfaces'] = AtelierInterfaceTable(instance.vc_interfaces(if_master=False), neutron_info=neutron_info, network_names=network_names)
        return to_return

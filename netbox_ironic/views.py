from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.conf import settings
from dcim.models import Device
from netbox.views import generic
from extras.models import ObjectChange, JournalEntry
from utilities.views import ViewTab, register_model_view
from .core import OpenstackConnector
from .tables import AtelierActionTable, AtelierInterfaceTable
from .models import AtelierAction
from urllib.parse import urlparse
from extras.plugins import get_plugin_config

class CustomViewTab(ViewTab):
    def render(self, instance):
        """Return the attributes needed to render a tab in HTML."""
        badge_value = self._get_badge_value(instance)
        
        baremetal_node_id = None
        for field, value in dict(instance.get_custom_fields()).items():
            if field.name == "baremetal_node_id":
                baremetal_node_id = value
        
        # Condition not to display the tab if info does not exist
        if self.hide_if_empty and baremetal_node_id == None:
            return None
        
        # Condition not to display the tab if info is not available
        try:
            os_connector = OpenstackConnector()
            os_connector.get_ironic_info(baremetal_node_id)
        except:
            return None
        
        if self.badge and self.hide_if_empty and not badge_value:
            return None
        
        return {
            'label': self.label,
            'badge': badge_value,
            'weight': self.weight,
        }

@register_model_view(Device, 'atelier', path='atelier')
class AtelierView(generic.ObjectView):
    template_name = 'netbox_ironic/atelier.html'

    queryset = Device.objects.all()

    tab = CustomViewTab(
        label='Atelier',
        weight=200,
        hide_if_empty=True
    )

    def get_extra_context(self, request, instance):
        os_connector = OpenstackConnector()
        baremetal_node_id = None
        for field, value in dict(instance.get_custom_fields()).items():
            if field.name == "baremetal_node_id":
                baremetal_node_id = value
        ironic_info = os_connector.get_ironic_info(baremetal_node_id)

        network_names = None
        if ironic_info["instance_uuid"]:
            nova_info = os_connector.get_nova_info(ironic_info["instance_uuid"])
            neutron_info = os_connector.get_port_info(ironic_info["instance_uuid"])
            if neutron_info is not None:
                network_ids = list(set([item.network_id for item in neutron_info]))
                network_names = {}
                for network_id in network_ids:
                    network_names[network_id] = os_connector.get_network_info(network_id)['name']
        else:
            nova_info = None
            neutron_info = None

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

        atelier_actions = []

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

        for server_action in os_connector.get_server_actions(nova_info):
            action = AtelierAction(time=datetime.strptime("%s+00:00" % server_action['start_time'], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                   request_id=server_action['request_id'],
                                   action=server_action['action'],
                                   message=server_action['message'],
                                   owner=server_action['user_id'],
                                   source='server')
            atelier_actions.append(action)

        for node_action in os_connector.get_node_actions(ironic_info):
            action = AtelierAction(time=datetime.strptime(node_action['created_at'], "%Y-%m-%dT%H:%M:%S%z"),
                                   request_id=node_action['uuid'],
                                   action=node_action['severity'].lower(),
                                   message=node_action['event'],
                                   owner='ironic',
                                   source='node')
            atelier_actions.append(action)

        atelier_actions = sorted(atelier_actions, key=lambda d: d.time, reverse=True)
        atelier_actions_table = AtelierActionTable(atelier_actions)

        hostname = urlparse(get_plugin_config('netbox_ironic', 'OS_AUTH_URL')).hostname
        horizon_hostname = hostname.replace('keystone', 'horizon')
        horizon_url = f'https://{horizon_hostname}/admin/ironic/{str(baremetal_node_id)}'
        
        atelier_id = settings.PLUGINS_CONFIG['netbox_ironic'].get('ATELIER_PROPERTY_NAME')
        atelier_url = None
        if "properties" in ironic_info and atelier_id in ironic_info["properties"]:
            atelier_prefix = settings.PLUGINS_CONFIG['netbox_ironic'].get('ATELIER_PREFIX_URL')
            atelier_url = f'{atelier_prefix}{str(ironic_info["properties"][atelier_id])}'
        
        interface_table = AtelierInterfaceTable(instance.vc_interfaces(if_master=False), neutron_info=neutron_info, network_names=network_names)
        return {
            'ironic_info': ironic_info,
            'nova_info': nova_info,
            'history': atelier_actions_table,
            'horizon_url': horizon_url,
            'atelier_url': atelier_url,
            'interfaces': interface_table
        }

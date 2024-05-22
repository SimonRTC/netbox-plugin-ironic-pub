from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from dcim.models import Device
from netbox.views import generic
from extras import tables
from extras.models import ObjectChange, JournalEntry
from utilities.views import ViewTab, register_model_view
from .core import OpenstackConnector
from .tables import AtelierActionTable
from .models import AtelierAction

@register_model_view(Device, 'atelier', path='atelier')
class AtelierView(generic.ObjectView):
    template_name = 'netbox_ironic/atelier.html'

    queryset = Device.objects.all()

    tab = ViewTab(
        label='Atelier',
        weight=1
    )

    def get_extra_context(self, request, instance):
        os_connector = OpenstackConnector()
        baremetal_node_id = None
        for field, value in list(instance.get_custom_fields()):
            if field.name == "baremetal_node_id":
                baremetal_node_id = value
        ironic_info = os_connector.get_ironic_info(baremetal_node_id)

        if ironic_info["instance_uuid"]:
            nova_info = os_connector.get_nova_info(ironic_info["instance_uuid"])
        else:
            nova_info = None

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

        return {
            'ironic_info': ironic_info,
            'nova_info': nova_info,
            'history': atelier_actions_table
        }

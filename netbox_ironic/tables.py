import django_tables2 as tables
from django_tables2.utils import Accessor
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import AtelierAction
from netbox.tables import NetBoxTable, ChoiceFieldColumn

from dcim.tables.devices import InterfaceTable, DeviceComponentTable
from dcim import models

class AtelierActionTable(NetBoxTable):
    source = ChoiceFieldColumn()

    time = tables.DateTimeColumn(attrs={
            "td": {
                "width": "150px"
            },
        },
        linkify=True,
        format=settings.SHORT_DATETIME_FORMAT
    )

    class Meta(NetBoxTable.Meta):
        model = AtelierAction
        fields = ('time', 'request_id', 'action', 'message', 'owner', 'source')
        default_columns = ('time', 'source', 'action', 'message')
        attrs = {"class": "table-sm"}
        row_attrs = {"class": lambda record: record.get_source_color()}

class AtelierInterfaceTable(InterfaceTable):
    def __init__(self, *args, neutron_info=None, network_names, **kwargs):
        super().__init__(*args, **kwargs)
        if neutron_info is not None:
            for item in neutron_info:
                for record in self.data:
                    if record.mac_address == item.mac_address:
                        addresses = []
                        for addr in item.fixed_ips:
                            addresses.append(addr['ip_address'])
                        if len(addresses) <= 3:
                            record.ip_address = {'3first': addresses, 'others': []}
                        else:
                            record.ip_address = {'3first': addresses[:3], 'others': addresses[3:]}
                        record.network_id = item.network_id
                        record.network_name = network_names[item.network_id]
                        record.port_id = item['id']
        
    name = tables.TemplateColumn(
        verbose_name=_('Name'),
        template_code='<i class="mdi mdi-{% if record.mgmt_only %}wrench{% elif record.is_lag %}reorder-horizontal'
                      '{% elif record.is_virtual %}circle{% elif record.is_wireless %}wifi{% else %}ethernet'
                      '{% endif %}"></i> <a href="{{ record.get_absolute_url }}">{{ value }}</a>',
        order_by=Accessor('_name'),
        attrs={'td': {'class': 'text-nowrap'}}
    )
    
    ip_address = tables.TemplateColumn(
        verbose_name=_('IP Address'),
        template_code='{% if record.ip_address.others|length > 0 %}'
                      '    <details>'
                      '        <summary>'
                      '            {% for ip in record.ip_address.3first %}'
                      '            <div>{{ ip }}</div>'
                      '            {% endfor %}'
                      '            ({{ record.ip_address.others|length }} other(s))'
                      '        </summary>'
                      '        <div>'
                      '        {% for ip in record.ip_address.others %}'
                      '        <div>{{ ip }}</div>'
                      '        {% endfor %}'
                      '        </div>'
                      '    </details>'
                      '{% else %}'
                      '{% if record.ip_address.3first|length > 0 %}'
                      '    {% for ip in record.ip_address.3first %}'
                      '    <div>{{ ip }}</div>'
                      '    {% endfor %}'
                      '{% else %}'
                      '—'
                      '{% endif %}'
                      '{% endif %}'
    )

    class Meta(DeviceComponentTable.Meta):
        model = models.Interface
        fields = (
            'pk', 'name', 'enabled', 'type', 'mac_address', 'ip_address', 'network_id', 'network_name', 'port_id', 'connection'
        )
        default_columns = (
            'pk', 'name', 'type', 'mac_address', 'ip_address', 'network_id', 'network_name', 'port_id', 'connection'
        )
        row_attrs = {
            'data-name': lambda record: record.name,
            'data-enabled': lambda record: "enabled" if record.enabled else "disabled",
            'data-virtual': lambda record: "true" if record.is_virtual else "false",
            'data-mark-connected': lambda record: "true" if record.mark_connected else "false",
            'data-cable-status': lambda record: record.cable.status if record.cable else "",
            'data-type': lambda record: record.type,
        }

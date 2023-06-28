import django_tables2 as tables

from .models import AtelierAction
from django.conf import settings
from netbox.tables import NetBoxTable, ChoiceFieldColumn


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

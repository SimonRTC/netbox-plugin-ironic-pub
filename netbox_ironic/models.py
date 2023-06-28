from django.db import models
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet

class SourceChoices(ChoiceSet):

    CHOICES = [
        ('journal', 'Datacenter', 'blue'),
        ('changelog', 'Changelog', 'orange'),
        ('node', 'Operator', 'red'),
        ('server', 'Customer', 'green')
    ]


class AtelierAction(NetBoxModel):
    time = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True
    )

    request_id = models.CharField(
        max_length=100
    )

    action = models.CharField(
        max_length=100
    )

    message = models.CharField(
        max_length=100
    )

    owner = models.CharField(
        max_length=100
    )

    source = models.CharField(
        max_length=100,
        choices=SourceChoices
    )

    def get_absolute_url(self):
        pass
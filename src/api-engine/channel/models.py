from django.db import models

from common.utils import make_uuid
from node.models import Node
from organization.models import Organization


class Channel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of Channel",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    name = models.CharField(help_text="name of channel", max_length=128)
    organizations = models.ManyToManyField(
        to=Organization,
        help_text="the organization of the channel",
        related_name="channels",
        # on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(
        help_text="Create time of Channel", auto_now_add=True
    )
    orderers = models.ManyToManyField(
        to=Node,
        help_text="Orderer list in the channel",
    )

    class Meta:
        ordering = ("-created_at",)

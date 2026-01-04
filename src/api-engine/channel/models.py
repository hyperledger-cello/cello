from django.db import models

from common.utils import make_uuid
from node.models import Node
from organization.models import Organization


class Channel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="Channel ID",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    name = models.CharField(help_text="Channel Name", max_length=128)
    organizations = models.ManyToManyField(
        to=Organization,
        help_text="Channel Organizations",
        related_name="channels",
        # on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(
        help_text="Channel Creation Timestamp", auto_now_add=True
    )
    orderers = models.ManyToManyField(
        to=Node,
        help_text="Channel Orderers",
    )

    class Meta:
        ordering = ("-created_at",)

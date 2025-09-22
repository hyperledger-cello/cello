from django.db import models

from common.utils import make_uuid
from organization.models import Organization


# Create your models here.

class Node(models.Model):
    class Type(models.TextChoices):
        PEER = "PEER", "Peer"
        ORDERER = "ORDERER", "Orderer"

    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        RUNNING = "RUNNING", "Running"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        help_text="Node ID",
        default=make_uuid,
    )
    name = models.CharField(
        help_text="Node Name",
        max_length=64,
    )
    type = models.CharField(
        help_text="Node Type",
        choices=Type.choices,
        max_length=64,
    )
    organization = models.ForeignKey(
        Organization,
        help_text="Organization Nodes",
        related_name="nodes",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        help_text="Node Creation Timestamp", auto_now_add=True
    )
    status = models.CharField(
        help_text="Node Status",
        choices=Status.choices,
        max_length=64,
        default=Status.CREATED,
    )
    config_file = models.TextField(
        help_text="Node Config File",
        null=True,
    )
    msp = models.TextField(
        help_text="Node MSP",
        null=True,
    )
    tls = models.TextField(
        help_text="Node TLS",
        null=True,
    )
    cid = models.CharField(
        help_text="Node Container ID",
        max_length=256,
        default="",
    )

    class Meta:
        ordering = ("-created_at",)

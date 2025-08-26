from django.db import models

from common.utils import make_uuid


class Organization(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of organization",
        default=make_uuid,
    )
    name = models.CharField(
        max_length=64,
        help_text="Name of organization",
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    msp = models.TextField(help_text="msp of organization", null=True)
    tls = models.TextField(help_text="tls of organization", null=True)
    network = models.ForeignKey(
        "Network",
        help_text="Network to which the organization belongs",
        null=True,
        related_name="organization",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("-created_at",)

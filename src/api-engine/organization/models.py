from django.db import models

from common.validators import validate_host
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
        unique=True,
        validators=[validate_host]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    msp = models.TextField(help_text="msp of organization", null=True)
    tls = models.TextField(help_text="tls of organization", null=True)
    class Meta:
        ordering = ("-created_at",)

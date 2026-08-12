from django.db import models

from common.validators import validate_host, validate_url
from common.utils import make_uuid


# Create your models here.

class Organization(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="Organization ID",
        default=make_uuid,
    )
    name = models.CharField(
        help_text="Organization Name",
        max_length=256,
        unique=True,
        validators=[validate_host]
    )
    agent_url = models.CharField(
        help_text="Organization Agent URL",
        max_length=2048,
        unique=True,
        null=True,
        validators=[validate_url],
        default=None,
    )
    msp_id = models.CharField(
        help_text="Fabric MSP ID",
        max_length=256,
        unique=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

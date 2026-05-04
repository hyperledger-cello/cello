from django.db import models

from common.validators import validate_host, validate_url
from common.utils import make_uuid, normalize_agent_url


class Organization(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="Organization ID",
        default=make_uuid,
    )
    name = models.CharField(
        help_text="Organization Name",
        unique=True,
        validators=[validate_host]
    )
    agent_url = models.CharField(
        help_text="Organization Agent URL",
        unique=True,
        validators=[validate_url],
        default=None
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Normalize agent_url before saving to ensure trailing slash is always present."""
        if self.agent_url:
            self.agent_url = normalize_agent_url(self.agent_url)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("-created_at",)

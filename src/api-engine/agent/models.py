from django.db import models

from agent.enums import AgentStatus, AgentType
from agent.validators import validate_url
from common.utils import make_uuid
from organization.models import Organization


# Create your models here.


class Agent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of agent",
        default=make_uuid,
    )
    name = models.CharField(
        help_text="Agent name, can be generated automatically.",
        max_length=64,
    )
    url = models.CharField(
        help_text="Agent URL", null=True, blank=True, validators=[validate_url]
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=models.CASCADE,
        help_text="Organization of agent",
        related_name="agent",
    )
    status = models.CharField(
        help_text="Status of agent",
        choices=AgentStatus.to_choices(True),
        max_length=10,
        default=AgentStatus.Active.name.lower(),
    )
    type = models.CharField(
        help_text="Type of agent",
        choices=AgentType.to_choices(True),
        max_length=32,
        default=AgentType.Docker.name.lower(),
    )
    created_at = models.DateTimeField(
        help_text="Create time of agent", auto_now_add=True
    )

    class Meta:
        ordering = ("-created_at",)

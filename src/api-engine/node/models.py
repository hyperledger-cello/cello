from django.db import models

from agent.models import Agent
from common.utils import make_uuid
from node.enums import NodeType, NodeStatus


# Create your models here.

class Node(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of node",
        default=make_uuid,
    )
    name = models.CharField(
        help_text="Node name",
        max_length=64,
    )
    type = models.CharField(
        help_text="Node type",
        choices=NodeType.to_choices(True),
        max_length=64,
    )
    agent = models.ForeignKey(
        Agent,
        help_text="Agent of node",
        related_name="nodes",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        help_text="Create time of network", auto_now_add=True
    )
    status = models.CharField(
        help_text="Status of node",
        choices=NodeStatus.to_choices(True),
        max_length=64,
        default=NodeStatus.Created.name.lower(),
    )
    config_file = models.TextField(
        help_text="Config file of node",
        null=True,
    )
    msp = models.TextField(
        help_text="msp of node",
        null=True,
    )
    tls = models.TextField(
        help_text="tls of node",
        null=True,
    )
    cid = models.CharField(
        help_text="id used in agent, such as container id",
        max_length=256,
        default="",
    )

    class Meta:
        ordering = ("-created_at",)

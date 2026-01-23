import os.path

from django.core.validators import MinValueValidator
from django.db import models

from channel.models import Channel
from common.utils import make_uuid
from node.models import Node
from user.models import UserProfile

def get_package_path(instance, filename) -> str:
    return str(os.path.join(instance.channel.name, filename))
# Create your models here.


class Chaincode(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        INSTALLED = "INSTALLED", "Installed"
        APPROVED = "APPROVED", "Approved"
        COMMITTED = "COMMITTED", "Committed"

    id = models.UUIDField(
        primary_key=True,
        help_text="Chaincode ID",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    package_id = models.CharField(
        help_text="Chaincode Package ID",
        max_length=128,
        editable=False,
        unique=True,
    )
    package = models.FileField(
        help_text="Chaincode Package",
        upload_to=get_package_path,
    )
    name = models.CharField(
        help_text="Chaincode Name",
        max_length=128,
    )
    version = models.CharField(
        help_text="Chaincode Version",
        max_length=128,
    )
    sequence = models.IntegerField(
        help_text="Chaincode Sequence",
        validators=[MinValueValidator(1)],
    )
    label = models.CharField(
        help_text="Chaincode Label",
        max_length=128,
    )
    creator = models.ForeignKey(
        UserProfile,
        help_text="Chaincode Creator",
        on_delete=models.SET_NULL,
        null=True,
    )
    channel = models.ForeignKey(
        Channel,
        help_text="Chaincode Channel",
        on_delete=models.CASCADE,
        related_name="chaincodes",
    )
    language = models.CharField(
        help_text="Chaincode Language",
        max_length=128,
    )
    init_required = models.BooleanField(
        help_text="Whether Chaincode Initialization Required",
        default=False,
    )
    signature_policy = models.CharField(
        help_text="Chaincode Signature Policy",
        null=True,
        blank=True,
    )
    status = models.CharField(
        help_text="Chaincode Status",
        choices=Status.choices,
        default=Status.CREATED,
        max_length=16,
    )
    peers = models.ManyToManyField(
        to=Node,
        help_text="Chaincode Installed Peers",
    )
    description = models.CharField(
        help_text="Chaincode Description",
        max_length=128,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        help_text="Chaincode Creation Timestamp",
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

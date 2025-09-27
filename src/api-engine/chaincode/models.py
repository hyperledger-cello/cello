from django.db import models

from channel.models import Channel
from common.utils import make_uuid
from user.models import UserProfile


# Create your models here.
class Chaincode(models.Model):
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

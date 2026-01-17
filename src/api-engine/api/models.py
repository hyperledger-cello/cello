#
# SPDX-License-Identifier: Apache-2.0
#
from django.conf import settings
from django.db import models

from api.utils.common import make_uuid

# from user.models import UserProfile

SUPER_USER_TOKEN = getattr(settings, "ADMIN_TOKEN", "")
MAX_CAPACITY = getattr(settings, "MAX_AGENT_CAPACITY", 100)
MAX_NODE_CAPACITY = getattr(settings, "MAX_NODE_CAPACITY", 600)
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT")
LIMIT_K8S_CONFIG_FILE_MB = 100
# Limit file upload size less than 100Mb
LIMIT_FILE_MB = 100
MIN_PORT = 1
MAX_PORT = 65535


class ChainCode(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of ChainCode",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    package_id = models.CharField(
        help_text="package_id of chainCode",
        max_length=128,
        editable=False,
        unique=True,
    )
    label = models.CharField(help_text="label of chainCode", max_length=128)
    creator = models.CharField(
        help_text="creator of chainCode", max_length=128
    )
    language = models.CharField(
        help_text="language of chainCode", max_length=128
    )
    description = models.CharField(
        help_text="description of chainCode",
        max_length=128,
        blank=True,
        null=True,
    )
    create_ts = models.DateTimeField(
        help_text="Create time of chainCode", auto_now_add=True
    )

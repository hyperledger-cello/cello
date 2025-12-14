#
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
import os

from drf_yasg import openapi
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from functools import reduce, partial
from api.common.serializers import BadResponseSerializer
import uuid
from zipfile import ZipFile
from json import loads
import json
import logging

LOG = logging.getLogger(__name__)



def with_common_response(responses=None):
    if responses is None:
        responses = {}

    responses.update(
        {
            status.HTTP_400_BAD_REQUEST: BadResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: "Permission denied",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Error",
            status.HTTP_403_FORBIDDEN: "Authentication credentials "
            "were not provided.",
        }
    )

    return responses


basic_type_info = [
    (serializers.CharField, openapi.TYPE_STRING),
    (serializers.BooleanField, openapi.TYPE_BOOLEAN),
    (serializers.IntegerField, openapi.TYPE_INTEGER),
    (serializers.FloatField, openapi.TYPE_NUMBER),
    (serializers.FileField, openapi.TYPE_FILE),
    (serializers.ImageField, openapi.TYPE_FILE),
]

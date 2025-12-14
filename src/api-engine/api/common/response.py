#
# SPDX-License-Identifier: Apache-2.0
#
"""Class represents response format.
        {
            status, successful/fail
            data,  response
            msg, error messages
        }

    """
import enum
from typing import Type, Dict

from rest_framework import serializers

class Status(enum.Enum):
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"

def make_response_serializer(data_serializer: Type[serializers.Serializer]):
    class _ResponseBody(serializers.Serializer):
        status = serializers.ChoiceField(
            choices=[(s.value, s.name) for s in Status]
        )
        msg = serializers.CharField(required=False, allow_null=True, allow_blank=True)
        data = data_serializer(required=False, allow_null=True)

    _ResponseBody.__name__ = f"ResponseBody[{data_serializer.__name__}]"
    return _ResponseBody


def ok(data: Dict[str, any]) -> Dict[str, any]:
    return {
        "status": Status.SUCCESSFUL.value,
        "msg": None,
        "data": data
    }

def err(msg: str) -> Dict[str, any]:
    return {
        "status": Status.FAILED.value,
        "msg": msg,
        "data": None
    }

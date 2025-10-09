#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, ParseError
from api.common.enums import ErrorCode
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from .common import zip_dir, zip_file
from api.common import ok, err

LOG = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if (
            response.status_code == status.HTTP_400_BAD_REQUEST
            and isinstance(response.data, dict)
            and "code" not in response.data
        ):
            if isinstance(exc, ValidationError):
                response.data["code"] = ErrorCode.ValidationError.value
                response.data["detail"] = (
                    ErrorCode.ValidationError.display_string
                )
            elif isinstance(exc, ParseError):
                response.data["code"] = ErrorCode.ParseError.value
                response.data["detail"] = ErrorCode.ParseError.display_string
            elif isinstance(response.data.get("detail"), ErrorDetail):
                # response.data["code"] = response.data.get("detail").code
                response.data = err(response.data.get("detail"))
            else:
                response.data["code"] = ErrorCode.Unknown.value
                response.data["detail"] = ErrorCode.Unknown.display_string

    return response

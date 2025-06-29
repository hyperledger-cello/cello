from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.exceptions import ValidationError, ParseError
from rest_framework.views import exception_handler

from api.utils.enums import ErrorCode


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        if (
            response.status_code == status.HTTP_400_BAD_REQUEST
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
                response.data["code"] = response.data.get("detail").code
            else:
                response.data["code"] = ErrorCode.Unknown.value
                response.data["detail"] = ErrorCode.Unknown.display_string

    return response

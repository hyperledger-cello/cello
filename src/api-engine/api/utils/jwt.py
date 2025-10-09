import logging

from rest_framework import serializers

from api.models import UserProfile, Organization
from api.common import ok

LOG = logging.getLogger(__name__)


class OrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")


class UserSerializer(serializers.ModelSerializer):
    organization = OrgSerializer(allow_null=True)

    class Meta:
        model = UserProfile
        fields = ("id", "username", "role", "email", "organization")


def jwt_response_payload_handler(token, user=None, request=None):
    """
    Customize response for json web token

    :param token: the token value
    :param user: user object for UserProfile
    :param request: request context
    :return: UserSerializer data
    """
    return ok(
        {
            "token": token,
            "user": UserSerializer(user, context={"request": request}).data,
        }
    )

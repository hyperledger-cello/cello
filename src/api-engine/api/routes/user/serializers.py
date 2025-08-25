#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers
from api.common.serializers import PageQuerySerializer
from api.models import UserProfile
from api.utils.jwt import OrgSerializer


class UserIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of user")


class UserQuerySerializer(PageQuerySerializer, serializers.Serializer):
    username = serializers.CharField(
        help_text="Username to filter", required=False, max_length=64
    )


class UserInfoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(help_text="ID of user")
    organization = OrgSerializer(allow_null=True, required=False)

    class Meta:
        model = UserProfile
        fields = ("id", "username", "role", "organization", "created_at")
        extra_kwargs = {
            "id": {"read_only": False},
            "username": {"validators": []},
        }


class UserListSerializer(serializers.Serializer):
    total = serializers.IntegerField(help_text="Total number of users")
    data = UserInfoSerializer(many=True, help_text="Users list")

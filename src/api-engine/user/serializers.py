#
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, Any

from rest_framework import serializers
from api.common.serializers import PageQuerySerializer
from api.utils.jwt import OrgSerializer
from user.models import UserProfile


class UserCreateBody(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("role", "organization", "password", "email")
        extra_kwargs = {
            "role": {"required": True},
            "organization": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    def create(self, validated_data: Dict[str, Any]) -> UserProfile:
        user = super(UserCreateBody, self).create(validated_data)

        user.set_password(validated_data["password"])
        user.save()
        return user


class UserIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of user")


class UserQuerySerializer(PageQuerySerializer, serializers.Serializer):
    email = serializers.CharField(
        help_text="Email to filter", required=False, max_length=64
    )


class UserInfoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(help_text="ID of user")
    organization = OrgSerializer(allow_null=True, required=False)

    class Meta:
        model = UserProfile
        fields = ("id", "email", "role", "organization", "created_at")


class UserListSerializer(serializers.Serializer):
    total = serializers.IntegerField(help_text="Total number of users")
    data = UserInfoSerializer(many=True, help_text="Users list")


class UserPasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(
        help_text="New password for login", max_length=64
    )

    def update_password(self, user: UserProfile) -> UserProfile:
        password = self.validated_data.get("password")
        user.set_password(password)
        user.save()
        return user


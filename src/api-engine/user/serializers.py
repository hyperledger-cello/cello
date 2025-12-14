#
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, Any

from rest_framework import serializers
from api.common.serializers import ListResponseSerializer
from organization.serializeres import OrganizationID, OrganizationResponse
from user.models import UserProfile


class UserCreateBody(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("role", "password", "email")
        extra_kwargs = {
            "role": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    def create(self, validated_data: Dict[str, Any]) -> UserProfile:
        user = UserProfile(
            username=validated_data["email"],
            email=validated_data["email"],
            role=validated_data["role"],
            organization=self.context["organization"],
        )

        user.set_password(validated_data["password"])
        user.save()
        return user


class UserID(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("id",)


class UserInfo(serializers.ModelSerializer):
    organization = OrganizationResponse()

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "email",
            "role",
            "organization",
            "created_at"
        )


class UserList(ListResponseSerializer):
    data = UserInfo(many=True, help_text="Users list")


class UserPasswordUpdate(serializers.Serializer):
    password = serializers.CharField(
        help_text="New password for login", max_length=64
    )

    def create(self, validated_data: Dict[str, any]) -> UserProfile:
        request = self.context["request"]
        user = request.user
        user.set_password(validated_data["password"])
        user.save()
        return user

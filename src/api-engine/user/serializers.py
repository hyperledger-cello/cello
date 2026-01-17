#
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, Any

from rest_framework import serializers
from api.common.serializers import ListResponseSerializer
from organization.serializeres import OrganizationResponse
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


class UserIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="User ID")


class UserInfoSerializer(UserIDSerializer, serializers.Serializer):
    email = serializers.EmailField(help_text="User Email")
    role = serializers.CharField(help_text="User Role")
    organization = OrganizationResponse(help_text="User Organization")
    created_at = serializers.DateTimeField(help_text="User Creation Timestamp")

    class Meta:
        fields = ("id", "email", "role", "organization", "created_at")


class UserListSerializer(ListResponseSerializer):
    data = UserInfoSerializer(many=True, help_text="Users list")


class UserPasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(
        help_text="New password for login", max_length=64
    )

    def create(self, validated_data: Dict[str, any]) -> UserProfile:
        request = self.context["request"]
        user = request.user
        user.set_password(validated_data["password"])
        user.save()
        return user


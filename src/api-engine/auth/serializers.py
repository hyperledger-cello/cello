from typing import Dict, Any, Optional

from rest_framework import serializers

from common.validators import validate_host
from api.lib.pki import CryptoConfig, CryptoGen
from organization.models import Organization
from user.models import UserProfile
from user.serializers import UserInfoSerializer


class RegisterBody(serializers.Serializer):
    org_name = serializers.CharField(help_text="User Organization Name")
    email = serializers.EmailField(help_text="User Email")
    password = serializers.CharField(help_text="User Password")

    class Meta:
        fields = ("org_name", "email", "password")
        extra_kwargs = {
            "org_name": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    @staticmethod
    def validate_org_name(org_name: str) -> str:
        if Organization.objects.filter(name = org_name).exists():
            raise serializers.ValidationError("Organization already exists!")
        validate_host(org_name)
        return org_name

    def create(self, validated_data: Dict[str, Any]) -> Optional[Organization]:
        org_name = validated_data.get("org_name")

        CryptoConfig(org_name).create()
        CryptoGen(org_name).generate()
        organization = Organization(name=org_name)
        organization.save()

        user = UserProfile(
            email=validated_data["email"],
            username= validated_data["email"],
            role=UserProfile.Role.ADMIN,
            organization=organization,
        )

        password = validated_data.get("password")
        user.set_password(password)
        user.save()
        return organization

class RegisterResponse(serializers.Serializer):
    id = serializers.UUIDField(help_text="Organization ID")
    msg = serializers.CharField(help_text="Organization Name")

class LoginBody(serializers.Serializer):
    email = serializers.CharField(help_text="User Email")
    password = serializers.CharField(help_text="User Password")

class LoginSuccessBody(serializers.Serializer):
    token = serializers.CharField(help_text="access token")
    user = UserInfoSerializer()

class TokenVerifyRequest(serializers.Serializer):
    token = serializers.CharField(help_text="access token")

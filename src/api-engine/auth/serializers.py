from typing import Dict, Any, Optional

from rest_framework import serializers

from common.validators import validate_host, validate_url
from api.lib.pki import CryptoConfig, CryptoGen
from organization.models import Organization
from organization.service import create_organization
from user.models import UserProfile
from user.serializers import UserInfo
from user.service import create_user


class RegisterBody(serializers.Serializer):
    org_name = serializers.CharField(help_text="User Organization Name")
    email = serializers.EmailField(help_text="Admin Email")
    password = serializers.CharField(help_text="Admin Password")
    agent_url = serializers.CharField(help_text="Agent URL")

    class Meta:
        fields = ("org_name", "email", "password")
        extra_kwargs = {
            "org_name": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    @staticmethod
    def validate_org_name(org_name: str) -> str:
        if Organization.objects.filter(name=org_name).exists():
            raise serializers.ValidationError("Organization already exists!")
        validate_host(org_name)
        return org_name

    @staticmethod
    def validate_agent_url(agent_url: str) -> str:
        if Organization.objects.filter(agent_url=agent_url).exists():
            raise serializers.ValidationError("Agent already exists!")
        validate_url(agent_url)

        return agent_url

    def create(self, validated_data: Dict[str, Any]) -> Optional[Organization]:
        organization = create_organization(validated_data.get("org_name"), validated_data.get("agent_url"))
        create_user(organization, validated_data["email"], validated_data["password"], UserProfile.Role.ADMIN)
        return organization


class RegisterResponse(serializers.Serializer):
    id = serializers.UUIDField(help_text="Organization ID")
    msg = serializers.CharField(help_text="Organization Name")


class LoginBody(serializers.Serializer):
    email = serializers.CharField(help_text="User Email")
    password = serializers.CharField(help_text="User Password")


class LoginSuccessBody(serializers.Serializer):
    token = serializers.CharField(help_text="access token")
    user = UserInfo()


class TokenVerifyRequest(serializers.Serializer):
    token = serializers.CharField(help_text="access token")

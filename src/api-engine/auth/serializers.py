from typing import Dict, Any, Optional

from rest_framework import serializers

from api.lib.pki import CryptoConfig, CryptoGen
from api.models import Organization
from user.enums import UserRole
from user.models import UserProfile
from user.serializers import UserInfoSerializer


class RegisterBody(serializers.ModelSerializer):
    org_name = serializers.CharField(help_text="name of Organization")
    email = serializers.EmailField(help_text="email of Administrator")
    password = serializers.CharField(
        help_text="password of Administrator"
    )

    class Meta:
        model = UserProfile
        fields = ("org_name", "email", "password")
        extra_kwargs = {
            "org_name": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    def validated_org_name(self, org_name: str) -> str:
        if Organization.objects.filter(name = org_name).exists():
            raise serializers.ValidationError("Organization already exists!")
        return org_name

    def create(self, validated_data: Dict[str, Any]) -> Optional[Organization]:
        org_name = validated_data.get("org_name")

        CryptoConfig(org_name).create(0, 0)
        CryptoGen(org_name).generate()
        organization = Organization(name=org_name)
        organization.save()

        email = validated_data.get("email")
        user = UserProfile(
            email=email,
            role=UserRole.ADMIN.value,
            organization=organization,
        )

        password = validated_data.get("password")
        user.set_password(password)
        user.save()
        return organization

class RegisterResponse(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of Organization")
    msg = serializers.CharField(help_text="name of Organization")

class LoginBody(serializers.Serializer):
    email = serializers.CharField(help_text="email of user")
    password = serializers.CharField(help_text="password of user")

class LoginSuccessBody(serializers.Serializer):
    token = serializers.CharField(help_text="access token")
    user = UserInfoSerializer()

class TokenVerifyRequest(serializers.Serializer):
    token = serializers.CharField(help_text="access token")

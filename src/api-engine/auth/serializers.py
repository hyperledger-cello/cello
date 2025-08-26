from typing import Dict, Any

from rest_framework import serializers

from api.models import Organization
from user.models import UserProfile


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

    def create(self, validated_data: Dict[str, Any]) -> UserProfile:
        org_name = validated_data.get("org_name")
        if Organization.objects.filter(name = org_name).exists():
            return None
        organization = Organization(name=org_name)
        organization.save()

        user = UserProfile(
            email=email,
            role="admin",
            organization=organization,
        )
        user.set_password(password)
        user.save()
        return user



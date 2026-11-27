#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers

from api.common.serializers import ListResponseSerializer
from common.validators import validate_host, validate_url
from organization.models import Organization


class OrganizationID(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id",)


class OrganizationBrief(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")


class OrganizationResponse(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "agent_url",
            "msp_id",
            "created_at",
        )


class OrganizationList(ListResponseSerializer):
    data = OrganizationResponse(many=True, help_text="Organizations list")


class OrganizationCreateBody(serializers.Serializer):
    name = serializers.CharField(max_length=256, validators=[validate_host])
    agent_url = serializers.CharField(
        max_length=2048,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    msp_id = serializers.CharField(
        max_length=256, required=False, allow_blank=True
    )

    def _unique_queryset(self):
        instance = self.context.get("organization")
        if instance is not None:
            return Organization.objects.exclude(pk=instance.pk)
        return Organization.objects.all()

    def validate_name(self, value):
        if self._unique_queryset().filter(name=value).exists():
            raise serializers.ValidationError(
                "An organization with this name already exists."
            )
        return value

    def validate_agent_url(self, value):
        if value:
            try:
                validate_url(value)
            except Exception:
                raise serializers.ValidationError(
                    "Invalid URL format. Must start with http:// or https://"
                )
            if self._unique_queryset().filter(agent_url=value).exists():
                raise serializers.ValidationError(
                    "An organization with this agent URL already exists."
                )
        return value

    def validate_msp_id(self, value):
        if value and self._unique_queryset().filter(msp_id=value).exists():
            raise serializers.ValidationError(
                "An organization with this MSP ID already exists."
            )
        return value

    def create(self, validated_data):
        if not validated_data.get("agent_url"):
            validated_data["agent_url"] = None
        return Organization.objects.create(**validated_data)


class OrganizationUpdateBody(OrganizationCreateBody):
    agent_url = serializers.CharField(
        max_length=2048,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def create(self, validated_data):
        instance = self.context["organization"]
        for attr, val in validated_data.items():
            if attr == "agent_url" and not val:
                val = None
            setattr(instance, attr, val)
        instance.save()
        return instance

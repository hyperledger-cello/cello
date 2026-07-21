from rest_framework import serializers

from api.common.serializers import ListResponseSerializer
from common.validators import validate_host, validate_url
from organization.models import Organization


class OrganizationID(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id",)


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
        max_length=2048, required=False, allow_blank=True, default=""
    )
    msp_id = serializers.CharField(max_length=256, required=False, allow_blank=True)

    def validate_name(self, value):
        if Organization.objects.filter(name=value).exists():
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
            if Organization.objects.filter(agent_url=value).exists():
                raise serializers.ValidationError(
                    "An organization with this agent URL already exists."
                )
        return value

    def validate_msp_id(self, value):
        if value and Organization.objects.filter(msp_id=value).exists():
            raise serializers.ValidationError(
                "An organization with this MSP ID already exists."
            )
        return value

    def create(self, validated_data):
        return Organization.objects.create(**validated_data)


class OrganizationUpdateBody(OrganizationCreateBody):
    def create(self, validated_data):
        instance = self.context["organization"]
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance

    def validate(self, attrs):
        instance = self.context["organization"]
        name = attrs.get("name")
        agent_url = attrs.get("agent_url")
        msp_id = attrs.get("msp_id")

        if name and name != instance.name:
            if Organization.objects.exclude(pk=instance.pk).filter(name=name).exists():
                raise serializers.ValidationError(
                    {"name": "An organization with this name already exists."}
                )

        if agent_url and agent_url != instance.agent_url:
            if Organization.objects.exclude(pk=instance.pk).filter(agent_url=agent_url).exists():
                raise serializers.ValidationError(
                    {"agent_url": "An organization with this agent URL already exists."}
                )

        if msp_id and msp_id != instance.msp_id:
            if Organization.objects.exclude(pk=instance.pk).filter(msp_id=msp_id).exists():
                raise serializers.ValidationError(
                    {"msp_id": "An organization with this MSP ID already exists."}
                )

        return attrs

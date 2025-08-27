from rest_framework import serializers

from agent.models import Agent
from api.common.serializers import PageQuerySerializer, ListResponseSerializer

IDHelpText = "ID of Agent"

class AgentQuery(PageQuerySerializer, serializers.Serializer):
    class Meta:
        fields = ("page", "per_page")


class AgentIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=IDHelpText)


class AgentResponseSerializer(AgentIDSerializer, serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "id",
            "name",
            "status",
            "created_at",
            "type",
            "urls",
            "organization",
        )


class AgentListResponse(ListResponseSerializer):
    data = AgentResponseSerializer(many=True, help_text="Agents data")


class AgentCreateBody(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "name",
            "type",
            "urls",
        )
        extra_kwargs = {
            "type": {"required": True},
            "urls": {"required": True},
            "name": {"required": True},
        }

    def validate(self, data):
        if self.context.get("request").user.organization.agent:
            raise serializers.ValidationError("Agent Exists for the Organization")
        return data

    def create(self, validated_data):
        validated_data["organization"] = self.context.get("request").user.organization
        return Agent.objects.create(**validated_data)



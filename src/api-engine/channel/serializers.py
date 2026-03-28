from typing import Dict, Any

from rest_framework import serializers

from channel.models import Channel
from channel.service import create
from common.serializers import ListResponseSerializer
from node.service import organization_orderer_exists, organization_peer_exists
from organization.serializers import OrganizationID


class ChannelID(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ("id",)


class ChannelResponse(serializers.ModelSerializer):
    organizations = OrganizationID(many=True)

    class Meta:
        model = Channel
        fields = (
            "id",
            "name",
            "organizations",
            "created_at"
        )


class ChannelList(ListResponseSerializer):
    data = ChannelResponse(many=True, help_text="Channel data")


class ChannelCreateBody(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        organization = self.context["organization"]
        if not organization_peer_exists(organization):
            raise serializers.ValidationError("You must have at least one peer for a channel.")
        if not organization_orderer_exists(organization):
            raise serializers.ValidationError("You must have at least one orderer for a channel.")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> ChannelID:
        return ChannelID(create(
            self.context["organization"],
            validated_data["name"]))

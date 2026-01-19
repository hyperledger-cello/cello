from typing import Dict, Any

from rest_framework import serializers

from channel.models import Channel
from channel.service import create
from common.serializers import ListResponseSerializer
from node.models import Node
from node.service import get_node
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
    peer_ids = serializers.ListField(
        child=serializers.UUIDField(help_text="ID of Peer Nodes")
    )
    orderer_ids = serializers.ListField(
        child=serializers.UUIDField(help_text="ID of Orderer Nodes")
    )

    @staticmethod
    def validate_peer_ids(value):
        if len(value) < 1:
            raise serializers.ValidationError("You must specify at least one peer for a channel.")

        for peer_id in value:
            node = get_node(peer_id)
            if node is None:
                raise serializers.ValidationError("Peer {} not found.".format(peer_id))
            if node.type != Node.Type.PEER:
                raise serializers.ValidationError(
                    "Node {} is not a peer but {} instead.".format(peer_id, node.type))
            if node.status != Node.Status.RUNNING:
                raise serializers.ValidationError("Peer {} is not running.".format(peer_id))

        return value

    @staticmethod
    def validate_orderer_ids(value):
        if len(value) < 1:
            raise serializers.ValidationError("You must specify at least one orderer for a channel.")

        for orderer_id in value:
            node = get_node(orderer_id)
            if node is None:
                raise serializers.ValidationError("Orderer {} not found.".format(orderer_id))
            if node.type != Node.Type.ORDERER:
                raise serializers.ValidationError(
                    "Node {} is not an orderer but {} instead.".format(orderer_id, node.type))
            if node.status != Node.Status.RUNNING:
                raise serializers.ValidationError("Orderer {} is not running.".format(orderer_id))

        return value

    def create(self, validated_data: Dict[str, Any]) -> ChannelID:
        return ChannelID(create(
            self.context["organization"],
            validated_data["name"],
            validated_data["peer_ids"],
            validated_data["orderer_ids"]))

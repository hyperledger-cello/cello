from rest_framework import serializers

from channel.models import Channel
from common.serializers import ListResponseSerializer
from node.enums import NodeStatus
from node.models import Node


class ChannelID(serializers.Serializer):
    id = serializers.UUIDField(help_text="Channel ID")


class ChannelResponse(
    ChannelID, serializers.ModelSerializer
):
    class Meta:
        model = Channel
        fields = ("id", "name", "organizations", "create_ts")


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

    def validate(self, data):
        peer_ids = data["peer_ids"]
        orderer_ids = data["orderer_ids"]

        if len(peer_ids) < 1:
            raise serializers.ValidationError("Invalid peers")
        if len(orderer_ids) < 1:
            raise serializers.ValidationError("Invalid orderers")

        for node in Node.objects.filter(id__in=(peer_ids + orderer_ids)):
            if node.status != NodeStatus.Running:
                raise serializers.ValidationError("Node {} is not running".format(node.name))

        return data

#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers

from api.models import Channel
from api.common.serializers import ListResponseSerializer


class ChannelCreateBody(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=True)
    peers = serializers.ListField(
        child=serializers.UUIDField(help_text="ID of Peer Nodes")
    )
    orderers = serializers.ListField(
        child=serializers.UUIDField(help_text="ID of Orderer Nodes")
    )

    def validate(self, attrs):
        if len(attrs["peers"]) < 1:
            raise serializers.ValidationError("Invalid peers")
        if len(attrs["orderers"]) < 1:
            raise serializers.ValidationError("Invalid orderers")

        return super().validate(attrs)


class ChannelIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Channel ID")


ORG_CHOICES = (
    ("Application", "Application"),
    ("Orderer", "Orderer"),
)


class ChannelUpdateSerializer(serializers.Serializer):
    msp_id = serializers.CharField(
        max_length=128, help_text="MSP ID of Organization"
    )
    data = serializers.FileField(help_text="Channel config file")
    org_type = serializers.ChoiceField(
        help_text="Organization type", choices=ORG_CHOICES
    )


class ChannelOrgListSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Organization ID")
    name = serializers.CharField(
        max_length=128, help_text="name of Organization"
    )


class ChannelNetworkSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Network ID")
    name = serializers.CharField(max_length=128, help_text="name of Network")


class ChannelResponseSerializer(
    ChannelIDSerializer, serializers.ModelSerializer
):
    id = serializers.UUIDField(help_text="ID of Channel")
    network = ChannelNetworkSerializer()
    organizations = ChannelOrgListSerializer(many=True)

    class Meta:
        model = Channel
        fields = ("id", "name", "network", "organizations", "create_ts")


class ChannelListResponse(ListResponseSerializer):
    data = ChannelResponseSerializer(many=True, help_text="Channel data")

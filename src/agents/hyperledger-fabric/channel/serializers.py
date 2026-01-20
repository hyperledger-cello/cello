from rest_framework import serializers

from channel.service import create_channel

class ChannelSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Channel Name")
    orderers = serializers.ListField(help_text="Orderer Names", child=serializers.CharField())
    peers = serializers.ListField(help_text="Peer Names", child=serializers.CharField())

    def create(self, validated_data):
        create_channel(validated_data["name"], validated_data["orderers"], validated_data["peers"])
        return self

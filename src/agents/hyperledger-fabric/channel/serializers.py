from rest_framework import serializers

from channel.service import create_channel

class ChannelSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Channel Name")

    def create(self, validated_data):
        create_channel(validated_data["name"])
        return self

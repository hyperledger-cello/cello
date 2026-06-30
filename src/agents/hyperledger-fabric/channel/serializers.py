from rest_framework import serializers

from channel.service import create_channel, generate_invitation_definition

class ChannelSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Channel Name")

    def create(self, validated_data):
        create_channel(validated_data["name"])
        return self


class InvitationDefinitionSerializer(serializers.Serializer):
    organization_msp_ids = serializers.ListField(
        child=serializers.CharField(help_text="Organization MSP ID"),
        help_text="List of MSP IDs for invited organizations",
    )

    def create(self, validated_data):
        channel_name = self.context["channel_name"]
        artifact = generate_invitation_definition(
            channel_name,
            validated_data["organization_msp_ids"],
        )
        validated_data["artifact"] = artifact
        return validated_data

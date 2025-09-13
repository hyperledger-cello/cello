from rest_framework import serializers

from api.common.serializers import ListResponseSerializer


class OrganizationResponse(serializers.Serializer):
    id = serializers.CharField(help_text="Organization ID")
    name = serializers.CharField(help_text="Organization Name")
    created_at = serializers.DateTimeField(help_text="Organization Creation Timestamp")

    class Meta:
        fields = ("id", "name", "created_at")
        extra_kwargs = {
            "name": {"required": True},
            "created_at": {"required": True, "read_only": True},
            "id": {"required": True, "read_only": True},
        }


class OrganizationList(ListResponseSerializer):
    data = OrganizationResponse(many=True, help_text="Organizations list")



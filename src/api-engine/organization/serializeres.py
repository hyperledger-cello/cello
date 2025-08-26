from rest_framework import serializers

from api.common.serializers import PageQuerySerializer, ListResponseSerializer


class OrganizationQuery(PageQuerySerializer, serializers.Serializer):
    class Meta:
        fields = ("page", "per_page")


class OrganizationResponse(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of Organization")
    network = serializers.UUIDField(help_text="ID of Network", allow_null=True)
    agents = serializers.UUIDField(help_text="ID of Agent", allow_null=True)

    class Meta:
        fields = ("id", "name", "created_at", "agents", "network")
        extra_kwargs = {
            "name": {"required": True},
            "created_at": {"required": True, "read_only": True},
            "id": {"required": True, "read_only": True},
        }


class OrganizationList(ListResponseSerializer):
    data = OrganizationResponse(many=True, help_text="Organizations list")



from rest_framework import serializers

from api.common.serializers import ListResponseSerializer
from organization.models import Organization


class OrganizationID(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id",)


class OrganizationResponse(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "created_at"
        )


class OrganizationList(ListResponseSerializer):
    data = OrganizationResponse(many=True, help_text="Organizations list")

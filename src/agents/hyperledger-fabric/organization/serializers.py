from rest_framework import serializers

import organization.service as organization_service


class OrganizationSerializer(serializers.Serializer):
    name = serializers.CharField()

    def create(self, validated_data):
        organization_service.create(validated_data["name"])
        return self

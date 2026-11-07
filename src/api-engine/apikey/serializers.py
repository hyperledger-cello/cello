#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers

from apikey.models import ApiKey


class ApiKeySerializer(serializers.ModelSerializer):
    """Read-only view of a key. Never includes the secret or the hash."""

    class Meta:
        model = ApiKey
        fields = (
            "id",
            "name",
            "prefix",
            "scope",
            "expires_at",
            "revoked_at",
            "last_used_at",
            "created_at",
        )
        read_only_fields = fields


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64)
    scope = serializers.ChoiceField(
        choices=ApiKey.Scope.choices,
        default=ApiKey.Scope.READ,
    )
    expires_in_days = serializers.IntegerField(
        min_value=1,
        max_value=365,
        default=90,
    )

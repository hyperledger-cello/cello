#
# SPDX-License-Identifier: Apache-2.0
#
from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apikey.models import ApiKey
from apikey.serializers import ApiKeyCreateSerializer, ApiKeySerializer


class ApiKeyViewSet(viewsets.GenericViewSet):
    """Create, list and revoke the caller's own API keys.

    JWT only: an API key can never manage keys.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ApiKeySerializer

    def get_queryset(self):
        return ApiKey.objects.filter(user=self.request.user)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request):
        body = ApiKeyCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        expires_at = timezone.now() + timedelta(days=data["expires_in_days"])
        key, raw = ApiKey.issue(
            user=request.user,
            name=data["name"],
            scope=data["scope"],
            expires_at=expires_at,
        )
        out = self.get_serializer(key).data
        # The plaintext key is only ever returned here, once.
        return Response({**out, "key": raw}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        key = self.get_object()
        if key.revoked_at is None:
            key.revoked_at = timezone.now()
            key.save(update_fields=["revoked_at"])
        return Response(self.get_serializer(key).data)

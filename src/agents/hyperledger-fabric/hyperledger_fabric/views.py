from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.response import Response


class HealthCheckViewSet(viewsets.ViewSet):
    @extend_schema(
        summary="Health check",
        responses={200: None},
    )
    def list(self, request):
        return Response()

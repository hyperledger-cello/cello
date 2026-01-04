import logging

from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from organization.serializers import OrganizationSerializer

# Create your views here.
LOG = logging.getLogger(__name__)

class OrganizationViewSet(viewsets.ViewSet):
    @extend_schema(
        request=OrganizationSerializer,
        responses={201: OrganizationSerializer}
    )
    def create(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.validated_data, status=status.HTTP_201_CREATED)



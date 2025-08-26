import os
import shutil

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from api.common import ok
from api.config import CELLO_HOME
from api.utils.common import with_common_response
from organization.models import Organization
from organization.serializeres import OrganizationQuery, OrganizationList


class OrganizationViewSet(viewsets.ViewSet):
    """Class represents organization related operations."""

    @swagger_auto_schema(
        query_serializer=OrganizationQuery(),
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: OrganizationList})
        ),
    )
    def list(self, request):
        serializer = OrganizationQuery(data=request.GET)
        serializer.is_valid(raise_exception=True)
        page = serializer.validated_data.get("page", 1)
        per_page = serializer.validated_data.get("per_page", 10)
        organizations = Organization.objects.all()
        p = Paginator(organizations, per_page)
        organizations = [
            {
                "id": str(organization.id),
                "name": organization.name,
                "network": (
                    str(organization.network.id)
                    if organization.network
                    else None
                ),
                "agents": (
                    organization.agent.id if organization.agent else None
                ),
                "created_at": organization.created_at,
            }
            for organization in p.page(page)
        ]
        response = OrganizationList(
            data={"total": p.count, "data": organizations}
        )
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.validated_data), status=status.HTTP_200_OK
        )


from typing import Optional

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.common import ok
from api.exceptions import CustomError
from api.utils.common import with_common_response
from common.responses import err
from common.serializers import PageQuerySerializer
from organization.models import Organization
from organization.serializeres import OrganizationList, OrganizationResponse


class OrganizationViewSet(viewsets.ViewSet):
    """Class represents organization related operations."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Organizations",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: OrganizationList})
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        page = serializer.validated_data.get("page", 1)
        per_page = serializer.validated_data.get("per_page", 10)
        organizations = Organization.objects.all()
        p = Paginator(organizations, per_page)
        if page > p.num_pages:
            return Response(
                err(f"Page {page} doesn't exist."), status=status.HTTP_400_BAD_REQUEST
            )
        response = OrganizationList(
            data={
                "total": p.count,
                "data": OrganizationResponse(p.page(page).object_list, many=True).data
            }
        )
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.validated_data), status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete Organizations",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request: Request, pk: Optional[str] = None) -> Response:
        try:
            Organization.objects.get(id=pk).delete()
        except Exception as e:
            raise CustomError(detail=str(e))
        return Response(status=status.HTTP_204_NO_CONTENT)

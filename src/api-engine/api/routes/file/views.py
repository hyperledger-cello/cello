# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.auth import IsOperatorAuthenticated, IsAdminAuthenticated
from api.exceptions import CustomError
from api.routes.file.serializers import (
    FileQuerySerializer,
    FileListSerializer,
    FileIDSerializer,
    FileCreateSerializer,
)
from api.utils.common import any_of, with_common_response
from api.models import File

LOG = logging.getLogger(__name__)


class FileViewSet(viewsets.ViewSet):
    permission_classes = (
        IsAuthenticated,
        any_of(IsAdminAuthenticated, IsOperatorAuthenticated),
    )

    @staticmethod
    def _validate_organization(request):
        if not request.user.is_operator and request.user.organization is None:
            raise CustomError(detail="Need join in organization.")

    @swagger_auto_schema(
        query_serializer=FileQuerySerializer,
        responses=with_common_response(
            {status.HTTP_200_OK: FileListSerializer}
        ),
    )
    def list(self, request):
        """
        List Files

        Filter files with query parameters,
        """
        serializer = FileQuerySerializer(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            name = serializer.validated_data.get("name")
            file_type = serializer.validated_data.get("type")
            organization = serializer.validated_data.get("organization")
            page = serializer.validated_data.get("page")
            per_page = serializer.validated_data.get("per_page")

            if organization is not None and not request.user.is_operator:
                raise PermissionDenied("Non-Operator Request Denied")
            query_filter = {}
            if name:
                query_filter.update({"name__icontains": name})
            if file_type:
                query_filter.update({"type": file_type})
            if organization:
                query_filter.update({"organization": organization})

            files = File.objects.filter(**query_filter)
            p = Paginator(files, per_page)
            files = p.page(page)
            files = [
                {
                    "id": str(file.id),
                    "name": file.name,
                    "type": file.type,
                    "url": request.build_absolute_uri(file.file.url),
                    "organization": file.organization.id,
                }
                for file in files
            ]

            response = FileListSerializer(
                data={"data": files, "total": p.count}
            )
            if response.is_valid(raise_exception=True):
                return Response(
                    response.validated_data, status=status.HTTP_200_OK
                )

    @swagger_auto_schema(
        request_body=FileCreateSerializer,
        responses=with_common_response(
            {status.HTTP_201_CREATED: FileIDSerializer}
        ),
    )
    def create(self, request):
        """
        Create new file

        Create new file
        """
        serializer = FileCreateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            name = serializer.validated_data.get("name")
            file_type = serializer.validated_data.get("type")
            file = serializer.validated_data.get("file")

            self._validate_organization(request)

            file = File(
                name=name,
                type=file_type,
                file=file,
                organization=request.user.organization,
            )
            file.save()
            response = FileIDSerializer(data=file.__dict__)
            if response.is_valid(raise_exception=True):
                return Response(
                    response.validated_data, status=status.HTTP_201_CREATED
                )

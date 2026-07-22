from typing import Optional

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.common import ok
from api.common.response import make_response_serializer
from api.exceptions import CustomError
from api.utils.common import with_common_response
from common.responses import err
from common.serializers import PageQuerySerializer
from organization.models import Organization
from organization.serializers import (
    OrganizationList,
    OrganizationResponse,
    OrganizationCreateBody,
    OrganizationUpdateBody,
)


class OrganizationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Organization",
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(OrganizationResponse)}
        ),
    )
    def retrieve(self, request, pk=None):
        try:
            res = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Organization not found")
            )
        return Response(
            status=status.HTTP_200_OK,
            data=ok(OrganizationResponse(res).data)
        )

    @swagger_auto_schema(
        operation_summary="Get Organizations",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(OrganizationList)}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(Organization.objects.all())
        return Response(
            status=status.HTTP_200_OK,
            data=ok(OrganizationList({
                "total": p.count,
                "data": OrganizationResponse(
                    p.page(serializer.data["page"]).object_list,
                    many=True
                ).data
            }).data)
        )

    @swagger_auto_schema(
        operation_summary="Create Organization",
        request_body=OrganizationCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(OrganizationResponse)}
        ),
    )
    def create(self, request):
        if not request.user.is_admin:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data=err("Admin role required."),
            )
        serializer = OrganizationCreateBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save()
        return Response(
            status=status.HTTP_201_CREATED,
            data=ok(OrganizationResponse(org).data),
        )

    @swagger_auto_schema(
        operation_summary="Update Organization",
        request_body=OrganizationUpdateBody,
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(OrganizationResponse)}
        ),
    )
    def update(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data=err("Admin role required."),
            )
        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Organization not found"),
            )
        serializer = OrganizationUpdateBody(
            data=request.data,
            context={"organization": org},
        )
        serializer.is_valid(raise_exception=True)
        org = serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=ok(OrganizationResponse(org).data),
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

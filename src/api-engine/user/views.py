# Create your views here.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Optional

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.common import ok
from api.common.response import make_response_serializer

from api.exceptions import CustomError
from common.serializers import PageQuerySerializer
from user.serializers import (
    UserCreateBody,
    UserIDSerializer,
    UserListSerializer,
    UserPasswordUpdateSerializer, UserInfoSerializer,
)
from api.utils.common import with_common_response
from user.models import UserProfile

LOG = logging.getLogger(__name__)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List users in the current organization",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(UserListSerializer)}
        ),
    )
    def list(self, request: Request) -> Response:
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(UserProfile.objects.filter(organization=request.user.organization))

        response = UserListSerializer(
            data = {
                "total": p.count,
                "data": UserInfoSerializer(
                    p.page(serializer.data.page).object_list,
                    many=True
                ).data,
            })
        response.is_valid(raise_exception=True)
        return Response(
            status = status.HTTP_200_OK,
            data = ok(response.data),
        )

    @swagger_auto_schema(
        operation_summary="Create a user in the current organization",
        request_body=UserCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(UserIDSerializer)}
        ),
    )
    def create(self, request: Request) -> Response:
        serializer = UserCreateBody(data=request.data, context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        response = UserIDSerializer(data={"id": serializer.save().id})
        response.is_valid(raise_exception=True)
        return Response(
            status = status.HTTP_201_CREATED,
            data = ok(response.data),
        )

    @swagger_auto_schema(
        operation_summary="Delete a user in the current organization",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request: Request, pk: Optional[str] = None) -> Response:
        try:
            UserProfile.objects.get(organzation=request.user.organization, id=pk).delete()
        except Exception as e:
            raise CustomError(detail=str(e))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method="PUT",
        operation_summary="Update the current user's password",
        request_body=UserPasswordUpdateSerializer,
        responses=with_common_response({status.HTTP_204_NO_CONTENT: "No Content"}),
    )
    @action(
        methods=["PUT"],
        detail=False,
        url_path="password",
    )
    def password(self, request: Request) -> Response:
        serializer = UserPasswordUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status = status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method="GET",
        operation_summary="Get the current user",
        responses=with_common_response({status.HTTP_200_OK: make_response_serializer(UserInfoSerializer)}),
    )
    @action(
        methods=["GET"],
        detail=False,
        url_path="profile",
    )
    def profile(self, request: Request) -> Response:
        return Response(
            status = status.HTTP_200_OK,
            data=ok(UserInfoSerializer(request.user).data),
        )

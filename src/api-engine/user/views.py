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

from api.exceptions import CustomError
from serializers import (
    UserCreateBody,
    UserIDSerializer,
    UserQuerySerializer,
    UserListSerializer,
    UserPasswordUpdateSerializer,
)
from api.utils.common import with_common_response
from user.models import UserProfile

LOG = logging.getLogger(__name__)


class UserViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        query_serializer=UserQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: UserListSerializer}
        ),
    )
    def list(self, request: Request) -> Response:
        """
        List Users

        List user through query parameter
        """
        serializer = UserQuerySerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        page = serializer.validated_data.get("page")
        per_page = serializer.validated_data.get("per_page")
        query_params = {}
        if email:
            query_params.update({"email__icontains": email})

        users = UserProfile.objects.filter(**query_params)
        p = Paginator(users, per_page)
        return Response(
            data = UserListSerializer(
                data = {
                    "total": p.count,
                    "data": list(p.page(page).object_list)
                }).data,
            status = status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=UserCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: UserIDSerializer}
        ),
    )
    def create(self, request: Request) -> Response:
        """
        Create User

        Create new user
        """
        serializer = UserCreateBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = UserIDSerializer(data={"id": serializer.save().id})
        response.is_valid(raise_exception=True)
        return Response(
            data = response.validated_data,
            status = status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Delete User

        Delete user
        """
        try:
            UserProfile.objects.get(id=pk).delete()
        except Exception as e:
            raise CustomError(detail=str(e))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method="post",
        request_body=UserPasswordUpdateSerializer,
        responses=with_common_response({status.HTTP_204_NO_CONTENT: "No Content"}),
    )
    @action(
        methods=["post"],
        detail=False,
        url_path="password",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def password(self, request: Request) -> Response:
        """
        post:
        Update/Reset Password

        Update/Reset password for user
        """
        serializer = UserPasswordUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update_password(request.user)
        return Response(
            status = status.HTTP_204_NO_CONTENT
        )

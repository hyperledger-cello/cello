#
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os

from django.core.paginator import Paginator
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.exceptions import ResourceExists, CustomError
from api.models import UserProfile
from api.routes.user.serializers import (
    UserCreateBody,
    UserIDSerializer,
    UserQuerySerializer,
    UserListSerializer,
    UserUpdateSerializer,
)
from api.utils.common import with_common_response

LOG = logging.getLogger(__name__)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")


class UserViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        query_serializer=UserQuerySerializer,
        responses=with_common_response(
            {status.HTTP_200_OK: UserListSerializer}
        ),
    )
    def list(self, request, *args, **kwargs):
        """
        List Users

        List user through query parameter
        """
        serializer = UserQuerySerializer(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get("username")
            page = serializer.validated_data.get("page")
            per_page = serializer.validated_data.get("per_page")
            query_params = {}
            if username:
                query_params.update({"username__icontains": username})

            users = UserProfile.objects.filter(**query_params).exclude(
                username=ADMIN_USERNAME
            )
            p = Paginator(users, per_page)
            users = p.page(page)
            # users = [user for user in users]

            response = UserListSerializer(
                {"total": p.count, "data": list(users.object_list)}
            ).data
            return Response(data=response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=UserCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: UserIDSerializer}
        ),
    )
    def create(self, request):
        """
        Create User

        Create new user
        """
        serializer = UserCreateBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get("username")
            role = serializer.validated_data.get("role")
            organization = serializer.validated_data.get("organization")
            password = serializer.validated_data.get("password")
            email = serializer.validated_data.get("email")

            user_count = UserProfile.objects.filter(
                Q(username=username) | Q(email=email)
            ).count()
            if user_count > 0:
                raise ResourceExists(
                    detail="User name or email already exists"
                )

            user = UserProfile(
                username=username,
                role=role,
                email=email,
                organization=organization,
            )
            user.set_password(password)
            user.save()
            response = UserIDSerializer(data={"id": user.id})
            if response.is_valid(raise_exception=True):
                return Response(
                    response.validated_data, status=status.HTTP_201_CREATED
                )

    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request, pk=None):
        """
        Delete User

        Delete user
        """
        try:
            UserProfile.objects.get(id=pk).delete()
        except Exception as e:
            raise CustomError(detail=str(e))
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get", "post", "put", "delete"],
        detail=True,
        url_path="attributes",
    )
    def attributes(self, request, pk=None):
        """
        get:
        Get User Attributes

        Get attributes of user
        post:
        Create Attributes

        Create attribute for user
        put:
        Update Attribute

        Update attribute of user
        delete:
        Delete Attribute

        Delete attribute of user
        """
        pass

    @swagger_auto_schema(
        method="post",
        request_body=UserUpdateSerializer,
        responses=with_common_response({status.HTTP_200_OK: "OK"}),
    )
    @action(
        methods=["post"],
        detail=True,
        url_path="password",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def password(self, request, pk=None):
        """
        post:
        Update/Reset Password

        Update/Reset password for user
        """
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password = serializer.validated_data.get("password")
            user = request.user
            user.set_password(password)
            user.save()
            response = UserIDSerializer(data={"id": user.id})
            if response.is_valid(raise_exception=True):
                return Response(
                    response.validated_data, status=status.HTTP_200_OK
                )

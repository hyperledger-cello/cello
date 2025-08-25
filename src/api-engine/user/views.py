# Create your views here.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.exceptions import CustomError
from api.models import UserProfile
from serializers import (
    UserCreateBody,
    UserIDSerializer,
    UserQuerySerializer,
    UserListSerializer,
    UserUpdateSerializer,
)
from api.utils.common import with_common_response

LOG = logging.getLogger(__name__)


class UserViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        query_serializer=UserQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: UserListSerializer}
        ),
    )
    def list(self, request):
        """
        List Users

        List user through query parameter
        """
        serializer = UserQuerySerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username")
        page = serializer.validated_data.get("page")
        per_page = serializer.validated_data.get("per_page")
        query_params = {}
        if username:
            query_params.update({"username__icontains": username})

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
    def create(self, request):
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
    def destroy(self, request, pk=None):
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
        request_body=UserUpdateSerializer,
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
    def password(self, request):
        """
        post:
        Update/Reset Password

        Update/Reset password for user
        """
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get("password")
        user = request.user
        user.set_password(password)
        user.save()
        return Response(
            status = status.HTTP_204_NO_CONTENT
        )

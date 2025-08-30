import logging
from typing import Union

from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView

from api.common import err, ok
from api.utils.common import with_common_response
from auth.serializers import RegisterBody, RegisterResponse, LoginBody, LoginSuccessBody, TokenVerifyRequest
from user.models import UserProfile

LOG = logging.getLogger(__name__)


class RegisterViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=RegisterBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: RegisterResponse}
        ),
    )
    def create(self, request: Request) -> Response:
        serializer = RegisterBody(data=request.data)
        if not serializer.is_valid():
            return Response(err(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        organization = serializer.save()
        response = RegisterResponse(data={
            "id": organization.id,
            "msg": organization.name
        })
        response.is_valid(raise_exception=True)
        return Response(
            data=ok(response.validated_data),
            status=status.HTTP_201_CREATED,
        )


class CelloTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        request_body=LoginBody,
        responses=with_common_response(
            {status.HTTP_200_OK: LoginSuccessBody}
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = LoginSuccessBody(
            data={
                "token": str(AccessToken.for_user(user).token),
                "user": user,
            })
        response.is_valid(raise_exception=True)
        return Response(
            data=ok(response.validated_data),
            status=status.HTTP_200_OK,
        )


class CelloTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        request_body=TokenVerifyRequest,
        responses=with_common_response(
            {status.HTTP_200_OK: LoginSuccessBody}
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = TokenVerifyRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            access_token = AccessToken(
                token=serializer.validated_data["token"],
            )
            user = UserProfile.objects.get(pk=access_token["user_id"])
        except Union[TokenError, UserProfile.DoesNotExist]:
            LOG.exception("invalid token error")
            return Response(
                data=err(msg="invalid token"),
                status=status.HTTP_400_BAD_REQUEST)

        response = LoginSuccessBody(
            data={
                "token": str(access_token.token),
                "user": user,
            })
        response.is_valid(raise_exception=True)
        return Response(
            data=ok(response.data),
            status=status.HTTP_200_OK,
        )

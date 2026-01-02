from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.response import make_response_serializer
from chaincode.models import Chaincode
from chaincode.serializers import ChaincodeCommitBody, ChaincodeList, ChaincodeCreateBody, ChaincodeID, ChaincodeRequestBody, ChaincodeResponse, \
    ChaincodeInstallBody, ChaincodeApproveBody
from common.responses import with_common_response, ok
from common.serializers import PageQuerySerializer


# Create your views here.
class ChaincodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_parsers(self):
        if getattr(self, 'action', None) == "create" or getattr(getattr(self, 'request', None), "FILES", None) is not None:
            return [MultiPartParser]
        return [JSONParser]

    @swagger_auto_schema(
        operation_summary="List all chaincodes of the current organization",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChaincodeList)}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(
            Chaincode.objects.filter(channel__organizations__id__contains=request.user.organization.id),
        )
        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChaincodeList({
                "total": p.count,
                "data": ChaincodeResponse(
                    p.get_page(serializer.data["page"])
                    .object_list,
                    many=True
                ).data,
            }).data),
        )

    @swagger_auto_schema(
        operation_summary="Create (Install and Approve) a chaincode for the current organization",
        request_body=ChaincodeCreateBody(),
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(ChaincodeID)}
        ),
    )
    def create(self, request):
        serializer = ChaincodeCreateBody(data=request.data, context={
            "user": request.user,
            "organization": request.user.organization,
        })
        serializer.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_201_CREATED,
            data=ok(serializer.save().data)
        )

    @swagger_auto_schema(
        operation_summary="Install a chaincode for the current organization",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: None}
        ),
    )
    @action(detail=True, methods=["PUT"])
    def install(self, request, pk=None):
        serializer = ChaincodeInstallBody(
            data={
                "id": pk
            },
            context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        operation_summary="Approve a chaincode for the current organization",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: None}
        ),
    )
    @action(detail=True, methods=["PUT"])
    def approve(self, request, pk=None):
        serializer = ChaincodeApproveBody(
            data={
                "id": pk
            },
            context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        operation_summary="Commit a chaincode to its channel",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: None}
        ),
    )
    @action(detail=True, methods=["PUT"])
    def commit(self, request, pk=None):
        serializer = ChaincodeCommitBody(
            data={
                "id": pk
            },
            context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        operation_summary="Invoke/Query a chaincode for the current organization",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: None}
        ),
    )
    @action(detail=True, methods=["PUT"])
    def transact(self, request, pk=None):
        serializer = ChaincodeRequestBody(
            data={
                "id": pk
            },
            context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

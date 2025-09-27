from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.response import make_response_serializer
from chaincode.models import Chaincode
from chaincode.serializers import ChaincodeList
from channel.serializers import ChannelResponse
from common.responses import with_common_response, ok
from common.serializers import PageQuerySerializer


# Create your views here.
class ChaincodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

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
                "data": ChannelResponse(
                    p.get_page(serializer.data["page"]).object_list,
                    many=True
                ).data,
            }).data),
        )


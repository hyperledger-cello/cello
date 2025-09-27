from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok
from api.common.response import make_response_serializer
from channel.models import Channel
from channel.serializers import ChannelList, ChannelID, ChannelResponse, ChannelCreateBody
from common.responses import with_common_response
from common.serializers import PageQuerySerializer


# Create your views here.

class ChannelViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        operation_summary="List all channels of the current organization",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelList)}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(Channel.objects.filter(organizations__id__contains=request.user.organization.id))
        response = ChannelList({
            "total": p.count,
            "data": ChannelResponse(p.page(serializer.data["page"]).object_list, many=True).data,
        })
        return Response(
            status=status.HTTP_200_OK,
            data=ok(response.data),
        )

    @swagger_auto_schema(
        operation_summary="Create a channel of the current organization",
        request_body=ChannelCreateBody(),
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(ChannelID)}
        ),
    )
    def create(self, request):
        serializer = ChannelCreateBody(data=request.data, context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_201_CREATED,
            data=serializer.save().data)

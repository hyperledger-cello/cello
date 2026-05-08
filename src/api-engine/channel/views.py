from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok
from api.common.response import make_response_serializer
from channel.models import Channel
from channel.serializers import (
    ChannelList, ChannelID, ChannelResponse, ChannelCreateBody,
    AddOrganizationBody,
)
from common.responses import with_common_response, err
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
        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelList({
                "total": p.count,
                "data": ChannelResponse(p.page(serializer.data["page"]).object_list, many=True).data,
            }).data),
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
            data=ok(serializer.save().data)
        )

    @swagger_auto_schema(
        operation_summary="Get details of a specific channel",
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelResponse)}
        ),
    )
    def retrieve(self, request, pk=None):
        try:
            channel = Channel.objects.get(
                pk=pk,
                organizations__id__contains=request.user.organization.id,
            )
        except Channel.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Channel not found"),
            )
        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelResponse(channel).data),
        )

    @swagger_auto_schema(
        operation_summary="Add an organization to an existing channel",
        request_body=AddOrganizationBody(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelResponse)}
        ),
    )
    @action(detail=True, methods=["POST"])
    def add_organization(self, request, pk=None):
        try:
            channel = Channel.objects.get(
                pk=pk,
                organizations__id__contains=request.user.organization.id,
            )
        except Channel.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Channel not found"),
            )

        serializer = AddOrganizationBody(
            data=request.data,
            context={"channel": channel},
        )
        serializer.is_valid(raise_exception=True)
        updated_channel = serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelResponse(updated_channel).data),
        )


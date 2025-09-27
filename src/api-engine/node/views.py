from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok
from api.common.response import make_response_serializer
from api.utils.common import with_common_response
from common.serializers import PageQuerySerializer
from node.models import Node
from node.serializers import NodeListSerializer, NodeCreateBody, NodeIDSerializer, NodeResponseSerializer


class NodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        operation_summary="List all nodes of the current organization",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(NodeListSerializer)}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(Node.objects.filter(organization=request.user.organization))
        response = NodeListSerializer({
            "total": p.count,
            "data": NodeResponseSerializer(p.page(serializer.data['page']).object_list, many=True).data
        })
        return Response(
            status=status.HTTP_200_OK,
            data=ok(response.data),
        )

    @swagger_auto_schema(
        operation_summary="Create a new node of the current organization",
        request_body=NodeCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(NodeIDSerializer)}
        ),
    )
    def create(self, request):
        serializer = NodeCreateBody(data=request.data, context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        response = NodeIDSerializer(serializer.save().__dict__)
        return Response(
            status=status.HTTP_201_CREATED,
            data=ok(response.data),
        )


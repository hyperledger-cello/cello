from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok
from api.utils.common import with_common_response
from common.serializers import PageQuerySerializer
from node.models import Node
from node.serializers import NodeListSerializer, NodeCreateBody, NodeIDSerializer


class NodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: NodeListSerializer})
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        page = serializer.validated_data.get("page")
        per_page = serializer.validated_data.get("per_page")
        p = Paginator(Node.objects.filter(organization=request.user.organization), per_page)
        response = NodeListSerializer({
            "total": p.count,
            "data": p.page(page).object_list
        })
        response.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_200_OK,
            data=response.data,
        )

    @swagger_auto_schema(
        request_body=NodeCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: NodeIDSerializer}
        ),
    )
    def create(self, request):
        serializer = NodeCreateBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = NodeIDSerializer(data=serializer.save().__dict__)
        response.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_201_CREATED,
            data=ok(response.validated_data),
        )


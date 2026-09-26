import docker
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from node.serializers import NodeLogsRequestSerializer, NodeLogsResponseSerializer, NodeRequestSerializer, \
    NodeResponseSerializer, NodeStatusRequestSerializer, NodeStatusSerializer


# Create your views here.
class NodeViewSet(viewsets.ViewSet):
    @extend_schema(
        parameters=[NodeStatusRequestSerializer],
        responses={200: NodeStatusSerializer}
    )
    @action(detail=False, methods=['get'])
    def status(self, request):
        serializer = NodeStatusRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response(
            data=serializer.save().data,
            status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[NodeLogsRequestSerializer],
        responses={200: NodeLogsResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='logs')
    def logs(self, request):
        serializer = NodeLogsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            data = serializer.save().data
        except docker.errors.NotFound as exc:
            return Response(data={"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(data=data, status=status.HTTP_200_OK)


    @extend_schema(
        request=NodeRequestSerializer,
        responses={201: NodeResponseSerializer}
    )
    def create(self, request):
        serializer = NodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            data=serializer.save().data,
            status=status.HTTP_201_CREATED)

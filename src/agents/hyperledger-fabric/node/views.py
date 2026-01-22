from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from node.serializers import NodeRequestSerializer, NodeResponseSerializer


# Create your views here.
class NodeViewSet(viewsets.ViewSet):
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

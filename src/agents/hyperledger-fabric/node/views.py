from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from node.serializers import NodeSerializer


# Create your views here.
class NodeViewSet(viewsets.ViewSet):
    @extend_schema(
        request=NodeSerializer,
        responses={201: NodeSerializer}
    )
    def create(self, request):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.validated_data, status=status.HTTP_201_CREATED)

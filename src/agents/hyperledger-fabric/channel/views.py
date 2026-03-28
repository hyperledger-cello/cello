from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from channel.serializers import ChannelSerializer

# Create your views here.
class ChannelViewSet(viewsets.ViewSet):
    @extend_schema(
        request=ChannelSerializer,
        responses={201: ChannelSerializer}
    )
    def create(self, request):
        serializer = ChannelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.validated_data, status=status.HTTP_201_CREATED)

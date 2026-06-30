from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from channel.serializers import ChannelSerializer, InvitationDefinitionSerializer


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

    @action(detail=True, methods=["post"], url_path="invitations/definition")
    @extend_schema(
        request=InvitationDefinitionSerializer,
        responses={200: None},
    )
    def invitation_definition(self, request, pk=None):
        serializer = InvitationDefinitionSerializer(
            data=request.data,
            context={"channel_name": pk},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return HttpResponse(
            result["artifact"],
            content_type="application/octet-stream",
            status=status.HTTP_200_OK,
        )

from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok
from channel.models import Channel
from channel.serializers import ChannelList, ChannelID
from common.responses import with_common_response
from common.serializers import PageQuerySerializer


# Create your views here.

class ChannelViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: ChannelList}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        page = serializer.validated_data.get("page")
        per_page = serializer.validated_data.get("per_page")
        p = Paginator(Channel.objects.filter(organizations=request.user.organization), per_page)
        response = ChannelList(
            data={
                "total": p.count,
                "data": list(p.page(page).object_list),
            }
        )
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.validated_data), status=status.HTTP_200_OK
        )

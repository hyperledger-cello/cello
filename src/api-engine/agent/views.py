from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agent.models import Agent
from agent.serializers import AgentListResponse, AgentCreateBody, AgentIDSerializer, AgentResponseSerializer
from api.common import ok
from api.utils.common import with_common_response
from common.serializers import PageQuerySerializer


# Create your views here.
class AgentViewSet(viewsets.ViewSet):
    """Class represents agent related operations."""

    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: AgentListResponse})
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)

        p = serializer.get_paginator(Agent.objects.filter(organization=request.user.organization))
        response = AgentListResponse(
            data={
                "total": p.count,
                "data": AgentResponseSerializer(p.page(serializer.data.page).object_list, many=True).data,
            }
        )
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.data),
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        request_body=AgentCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: AgentIDSerializer}
        ),
    )
    def create(self, request):
        serializer = AgentCreateBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.save()
        response = AgentIDSerializer(data=agent.__dict__)
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.validated_data),
            status=status.HTTP_201_CREATED,
        )

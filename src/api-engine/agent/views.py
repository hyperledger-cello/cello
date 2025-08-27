from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agent.models import Agent
from agent.serializers import AgentQuery, AgentListResponse, AgentCreateBody, AgentIDSerializer
from api.common import ok
from api.utils.common import with_common_response


# Create your views here.
class AgentViewSet(viewsets.ViewSet):
    """Class represents agent related operations."""

    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(
        query_serializer=AgentQuery(),
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: AgentListResponse})
        ),
    )
    def list(self, request):
        serializer = AgentQuery(data=request.GET)
        serializer.is_valid(raise_exception=True)
        page = serializer.validated_data.get("page")
        per_page = serializer.validated_data.get("per_page")

        p = Paginator(Agent.objects.filter(organization=request.user.organization), per_page)
        response = AgentListResponse(
            data={
                "data": list(p.page(page).object_list),
                "total": p.count}
        )
        response.is_valid(raise_exception=True)
        return Response(
            ok(response.validated_data),
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

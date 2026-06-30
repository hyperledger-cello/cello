from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common import ok, err
from api.common.response import make_response_serializer
from channel.models import Channel, ChannelInvitation, ChannelInvitationInvitee
from channel.serializers import (
    ChannelList,
    ChannelID,
    ChannelResponse,
    ChannelCreateBody,
    ChannelInvitationCreateBody,
    ChannelInvitationResponse,
    ChannelInvitationList,
    ChannelInvitationCancelSerializer,
)
from common.responses import with_common_response
from common.serializers import PageQuerySerializer


class ChannelViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    def _get_channel(self, pk):
        return get_object_or_404(Channel, pk=pk)

    def _get_invitation(self, invitation_pk):
        return get_object_or_404(
            ChannelInvitation.objects.visible_to_organization(
                self.request.user.organization
            ),
            pk=invitation_pk,
        )

    def _can_admin(self, org, channel):
        return self.request.user.is_admin and channel.organizations.filter(
            pk=org.pk
        ).exists()

    def _is_invitee(self, org, invitation):
        return ChannelInvitationInvitee.objects.filter(
            invitation=invitation,
            organization=org,
            status=ChannelInvitationInvitee.Status.PENDING,
        ).exists()

    def _is_invited(self, org, invitation):
        return ChannelInvitationInvitee.objects.filter(
            invitation=invitation,
            organization=org,
        ).exists()

    @swagger_auto_schema(
        operation_summary="List all channels of the current organization",
        query_serializer=PageQuerySerializer(),
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelList)}
        ),
    )
    def list(self, request):
        serializer = PageQuerySerializer(data=request.GET)
        p = serializer.get_paginator(Channel.objects.filter(organizations__id__contains=request.user.organization.id))
        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelList({
                "total": p.count,
                "data": ChannelResponse(p.page(serializer.data["page"]).object_list, many=True).data,
            }).data),
        )

    @swagger_auto_schema(
        operation_summary="Create a channel of the current organization",
        request_body=ChannelCreateBody(),
        responses=with_common_response(
            {status.HTTP_201_CREATED: make_response_serializer(ChannelID)}
        ),
    )
    def create(self, request):
        serializer = ChannelCreateBody(data=request.data, context={"organization": request.user.organization})
        serializer.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_201_CREATED,
            data=ok(serializer.save().data)
        )

    @action(detail=True, methods=["get", "post"], url_path="invitations")
    @swagger_auto_schema(
        operation_summary="List or create channel invitations",
        query_serializer=PageQuerySerializer(),
        request_body=ChannelInvitationCreateBody,
        responses=with_common_response(
            {
                status.HTTP_200_OK: make_response_serializer(ChannelInvitationList),
                status.HTTP_201_CREATED: make_response_serializer(ChannelInvitationResponse),
            }
        ),
    )
    def invitations(self, request, pk=None):
        channel = self._get_channel(pk)

        if request.method == "GET":
            invitations = ChannelInvitation.objects.visible_to_organization(
                request.user.organization
            ).filter(channel=channel)
            page_serializer = PageQuerySerializer(data=request.GET)
            p = page_serializer.get_paginator(invitations)
            return Response(
                status=status.HTTP_200_OK,
                data=ok(ChannelInvitationList({
                    "total": p.count,
                    "data": ChannelInvitationResponse(
                        p.page(page_serializer.data["page"]).object_list, many=True
                    ).data,
                }).data),
            )

        elif request.method == "POST":
            serializer = ChannelInvitationCreateBody(
                data=request.data,
                context={
                    "channel": channel,
                    "organization": request.user.organization,
                },
            )
            serializer.is_valid(raise_exception=True)
            if not request.user.is_admin:
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data=err("Admin role required."),
                )
            try:
                invitation = serializer.save()
            except Exception as e:
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    data=err(str(e)),
                )
            return Response(
                status=status.HTTP_201_CREATED,
                data=ok(ChannelInvitationResponse(invitation).data),
            )

    @action(detail=True, methods=["get"], url_path=r"invitations/(?P<invitation_pk>[^/.]+)")
    @swagger_auto_schema(
        operation_summary="Retrieve a single channel invitation",
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelInvitationResponse)}
        ),
    )
    def invitation_detail(self, request, pk=None, invitation_pk=None):
        channel = self._get_channel(pk)
        invitation = self._get_invitation(invitation_pk)

        if str(invitation.channel_id) != str(channel.id):
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Not found."),
            )

        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelInvitationResponse(invitation).data),
        )

    @action(
        detail=True,
        methods=["post"],
        url_path=r"invitations/(?P<invitation_pk>[^/.]+)/cancel",
    )
    @swagger_auto_schema(
        operation_summary="Cancel a channel invitation",
        responses=with_common_response(
            {status.HTTP_200_OK: make_response_serializer(ChannelInvitationResponse)}
        ),
    )
    def cancel_invitation(self, request, pk=None, invitation_pk=None):
        channel = self._get_channel(pk)

        invitation = ChannelInvitation.objects.filter(
            pk=invitation_pk, channel=channel
        ).first()
        if not invitation:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Not found."),
            )

        org = request.user.organization
        is_member = channel.organizations.filter(pk=org.pk).exists()
        is_invited = self._is_invited(org, invitation)
        can_cancel_as_invitee = self._is_invitee(org, invitation)

        if not is_member and not is_invited:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=err("Not found."),
            )

        if not self._can_admin(org, channel) and not can_cancel_as_invitee:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data=err("Permission denied."),
            )

        serializer = ChannelInvitationCancelSerializer(
            data=request.data,
            context={"invitation": invitation},
        )
        serializer.is_valid(raise_exception=True)

        invitation.status = ChannelInvitation.Status.CANCELED
        invitation.save()

        return Response(
            status=status.HTTP_200_OK,
            data=ok(ChannelInvitationResponse(invitation).data),
        )

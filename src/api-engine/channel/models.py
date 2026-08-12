# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
from django.db import models
from django.db.models import Q

from common.utils import make_uuid
from organization.models import Organization


class Channel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="Channel ID",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    name = models.CharField(help_text="Channel Name", max_length=128)
    organizations = models.ManyToManyField(
        to=Organization,
        help_text="Channel Organizations",
        related_name="channels",
        # on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(
        help_text="Channel Creation Timestamp", auto_now_add=True
    )

    class Meta:
        ordering = ("-created_at",)


class ChannelInvitationQuerySet(models.QuerySet):
    def visible_to_organization(self, organization: Organization):
        return self.filter(
            Q(channel__organizations=organization)
            | Q(
                status__in=("READY", "ACCEPTED", "REJECTED", "FAILED"),
                invitees__organization=organization,
            )
        ).distinct()


class ChannelInvitation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SIGNING = "SIGNING", "Signing"
        READY = "READY", "Ready"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        FAILED = "FAILED", "Failed"
        CANCELED = "CANCELED", "Canceled"

    id = models.UUIDField(
        primary_key=True,
        help_text="Channel Invitation ID",
        default=make_uuid,
    )
    channel = models.ForeignKey(
        Channel,
        help_text="Invitation Channel",
        related_name="invitations",
        on_delete=models.CASCADE,
    )
    creator_organization = models.ForeignKey(
        Organization,
        help_text="Creator Organization",
        related_name="created_invitations",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        help_text="Channel invitation status",
        choices=Status.choices,
        default=Status.DRAFT,
        max_length=32,
        db_index=True,
    )
    artifact = models.FileField(
        help_text="Update Artifact",
        upload_to="channel_invitations/",
        null=True,
        blank=True,
    )
    artifact_hash = models.CharField(
        help_text="Artifact Hash",
        max_length=64,
        blank=True,
        default="",
    )
    required_signatures = models.PositiveSmallIntegerField(
        help_text="Required Signatures",
        default=1,
    )
    error_message = models.TextField(
        help_text="Error Message",
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = ChannelInvitationQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)


class ChannelInvitationInvitee(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        help_text="Channel Invitation Invitee ID",
        default=make_uuid,
    )
    invitation = models.ForeignKey(
        ChannelInvitation,
        help_text="Invitation",
        related_name="invitees",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        help_text="Invited Organization",
        related_name="invitee_invitations",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        help_text="Invitee Status",
        choices=Status.choices,
        default=Status.PENDING,
        max_length=32,
        db_index=True,
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("invitation", "organization"),
                name="unique_channel_invitation_invitee",
            )
        ]


class ChannelInvitationSignature(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="Channel Invitation Signature ID",
        default=make_uuid,
    )
    invitation = models.ForeignKey(
        ChannelInvitation,
        help_text="Invitation",
        related_name="signatures",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        help_text="Signing Organization",
        related_name="invitation_signatures",
        on_delete=models.CASCADE,
    )
    artifact_hash = models.CharField(
        help_text="Artifact Hash",
        max_length=64,
    )
    signed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("signed_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("invitation", "organization"),
                name="unique_channel_invitation_signature",
            )
        ]

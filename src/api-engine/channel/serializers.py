# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
from typing import Dict, Any

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from channel.models import (
    Channel,
    ChannelInvitation,
    ChannelInvitationInvitee,
    ChannelInvitationSignature,
)
from channel.service import create, create_invitation_artifact, sign_invitation_artifact, accept_invitation
from common.serializers import ListResponseSerializer
from node.service import organization_orderer_exists, organization_peer_exists
from organization.models import Organization
from organization.serializers import OrganizationID


class ChannelID(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ("id",)


class ChannelResponse(serializers.ModelSerializer):
    organizations = OrganizationID(many=True)

    class Meta:
        model = Channel
        fields = (
            "id",
            "name",
            "organizations",
            "created_at"
        )


class ChannelList(ListResponseSerializer):
    data = ChannelResponse(many=True, help_text="Channel data")


class ChannelCreateBody(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        organization = self.context["organization"]
        if not organization_peer_exists(organization):
            raise serializers.ValidationError("You must have at least one peer for a channel.")
        if not organization_orderer_exists(organization):
            raise serializers.ValidationError("You must have at least one orderer for a channel.")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> ChannelID:
        return ChannelID(create(
            self.context["organization"],
            validated_data["name"]))


class ChannelInvitationInviteeResponse(serializers.ModelSerializer):
    organization = OrganizationID()

    class Meta:
        model = ChannelInvitationInvitee
        fields = (
            "id",
            "organization",
            "status",
            "responded_at",
        )
        read_only_fields = fields


class ChannelInvitationSignatureResponse(serializers.ModelSerializer):
    organization = OrganizationID()

    class Meta:
        model = ChannelInvitationSignature
        fields = (
            "id",
            "organization",
            "artifact_hash",
            "signed_at",
        )
        read_only_fields = fields


class ChannelInvitationResponse(serializers.ModelSerializer):
    channel = ChannelID()
    creator_organization = OrganizationID()
    invitees = ChannelInvitationInviteeResponse(many=True)
    signatures = ChannelInvitationSignatureResponse(many=True)

    class Meta:
        model = ChannelInvitation
        fields = (
            "id",
            "channel",
            "creator_organization",
            "status",
            "artifact_hash",
            "required_signatures",
            "error_message",
            "invitees",
            "signatures",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ChannelInvitationList(ListResponseSerializer):
    data = ChannelInvitationResponse(many=True)


class ChannelInvitationCreateBody(serializers.Serializer):
    organization_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
    )
    organization_names = serializers.ListField(
        child=serializers.CharField(max_length=256),
        required=False,
        allow_empty=False,
    )
    required_signatures = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    def validate_organization_ids(self, value):
        seen = {}
        for oid in value:
            if oid in seen:
                raise serializers.ValidationError(
                    "Duplicated organizations are not allowed."
                )
            seen[oid] = True
        return value

    def validate_organization_names(self, value):
        seen = {}
        for name in value:
            if name in seen:
                raise serializers.ValidationError(
                    "Duplicated organizations are not allowed."
                )
            seen[name] = True
        return value

    def validate(self, attrs):
        channel = self.context["channel"]
        creator = self.context["organization"]

        if not channel.organizations.filter(pk=creator.pk).exists():
            raise serializers.ValidationError(
                "Not a channel member."
            )

        org_ids = attrs.get("organization_ids")
        org_names = attrs.get("organization_names")
        if bool(org_ids) == bool(org_names):
            raise serializers.ValidationError(
                "Provide organization_ids or organization_names."
            )

        if org_names:
            field_key = "organization_names"
            names = list(dict.fromkeys(org_names))
            existing_by_name = {
                o.name: o
                for o in Organization.objects.filter(name__in=names)
            }
            missing = [n for n in names if n not in existing_by_name]
            if missing:
                raise serializers.ValidationError({
                    field_key: [
                        f"Organization does not exist: {n}" for n in missing
                    ]
                })
            orgs = [existing_by_name[n] for n in names]
        else:
            field_key = "organization_ids"
            org_ids = list(dict.fromkeys(org_ids))
            existing = {
                o.id: o
                for o in Organization.objects.filter(pk__in=org_ids)
            }
            missing = [str(oid) for oid in org_ids if oid not in existing]
            if missing:
                raise serializers.ValidationError({
                    field_key: [
                        f"Organization does not exist: {oid}" for oid in missing
                    ]
                })
            orgs = [existing[oid] for oid in org_ids]

        member_ids = set(channel.organizations.values_list("id", flat=True))
        already_members = [o.name for o in orgs if o.id in member_ids]
        if already_members:
            raise serializers.ValidationError({
                field_key: [
                    f"Already a member: {name}" for name in already_members
                ]
            })

        org_pks = [o.pk for o in orgs]
        active_invitees = ChannelInvitationInvitee.objects.filter(
            organization__in=org_pks,
            status=ChannelInvitationInvitee.Status.PENDING,
            invitation__channel=channel,
            invitation__status__in=(
                ChannelInvitation.Status.DRAFT,
                ChannelInvitation.Status.SIGNING,
                ChannelInvitation.Status.READY,
            ),
        )
        if active_invitees.exists():
            raise serializers.ValidationError(
                "An active invitation already exists for one or more "
                "of the specified organizations."
            )

        member_count = channel.organizations.count()
        required = attrs.get("required_signatures", (member_count // 2) + 1)
        if required > member_count:
            raise serializers.ValidationError({
                "required_signatures": "Cannot exceed member count."
            })

        attrs["organizations"] = orgs
        attrs["required_signatures"] = required
        return attrs

    def create(self, validated_data):
        orgs = validated_data.pop("organizations")
        validated_data.pop("organization_ids", None)
        validated_data.pop("organization_names", None)
        channel = self.context["channel"]
        creator = self.context["organization"]
        artifact_bytes, artifact_hash = create_invitation_artifact(
            agent_url=creator.agent_url,
            channel_name=channel.name,
            msp_ids=[o.msp_id for o in orgs],
        )
        with transaction.atomic():
            invitation = ChannelInvitation.objects.create(
                channel=channel,
                creator_organization=creator,
                required_signatures=validated_data["required_signatures"],
                artifact_hash=artifact_hash,
            )
            invitation.artifact.save(
                f"channel_update_{channel.name}.bin",
                ContentFile(artifact_bytes),
            )
            ChannelInvitationInvitee.objects.bulk_create([
                ChannelInvitationInvitee(
                    invitation=invitation, organization=o
                ) for o in orgs
            ])
        return invitation


class ChannelInvitationCancelSerializer(serializers.Serializer):
    def validate(self, attrs):
        invitation = self.context["invitation"]

        if invitation.status not in (
            ChannelInvitation.Status.DRAFT,
            ChannelInvitation.Status.SIGNING,
            ChannelInvitation.Status.FAILED,
            ChannelInvitation.Status.READY,
        ):
            raise serializers.ValidationError(
                "Only DRAFT, SIGNING, FAILED, or READY invitations can be canceled."
            )

        return attrs

    def create(self, validated_data):
        invitation = self.context["invitation"]
        invitation.status = ChannelInvitation.Status.CANCELED
        invitation.save(update_fields=["status"])
        return invitation


class ChannelInvitationAcceptSerializer(serializers.Serializer):
    def validate(self, attrs):
        invitation = self.context["invitation"]
        org = self.context["organization"]

        if invitation.status != ChannelInvitation.Status.READY:
            raise serializers.ValidationError(
                "Only READY invitations can be accepted."
            )

        invitee = ChannelInvitationInvitee.objects.filter(
            invitation=invitation,
            organization=org,
            status=ChannelInvitationInvitee.Status.PENDING,
        ).first()
        if not invitee:
            raise serializers.ValidationError(
                "This organization is not a pending invitee for this invitation."
            )

        attrs["invitee"] = invitee
        return attrs

    def create(self, validated_data):
        invitation = self.context["invitation"]
        org = self.context["organization"]
        invitee = validated_data["invitee"]
        channel = invitation.channel

        try:
            with open(invitation.artifact.path, "rb") as f:
                artifact_bytes = f.read()

            with transaction.atomic():
                invitation = ChannelInvitation.objects.select_for_update().get(
                    pk=invitation.pk
                )
                accept_invitation(org.agent_url, channel.name, artifact_bytes)
                channel.organizations.add(org)
                invitee.status = ChannelInvitationInvitee.Status.ACCEPTED
                invitee.responded_at = timezone.now()
                invitee.save(update_fields=["status", "responded_at"])

                all_done = not ChannelInvitationInvitee.objects.filter(
                    invitation=invitation,
                    status=ChannelInvitationInvitee.Status.PENDING,
                ).exists()
                if all_done:
                    invitation.status = ChannelInvitation.Status.ACCEPTED
                    invitation.save(update_fields=["status"])

        except Exception:
            invitation.refresh_from_db()
            if invitation.status != ChannelInvitation.Status.FAILED:
                invitation.status = ChannelInvitation.Status.FAILED
                invitation.error_message = "Accept operation failed."
                invitation.save(update_fields=["status", "error_message"])
            raise

        return invitation


class ChannelInvitationRejectSerializer(serializers.Serializer):
    def validate(self, attrs):
        invitation = self.context["invitation"]
        org = self.context["organization"]

        if invitation.status != ChannelInvitation.Status.READY:
            raise serializers.ValidationError(
                "Only READY invitations can be rejected."
            )

        invitee = ChannelInvitationInvitee.objects.filter(
            invitation=invitation,
            organization=org,
            status=ChannelInvitationInvitee.Status.PENDING,
        ).first()
        if not invitee:
            raise serializers.ValidationError(
                "This organization is not a pending invitee for this invitation."
            )

        attrs["invitee"] = invitee
        return attrs

    def create(self, validated_data):
        invitee = validated_data["invitee"]
        invitee.status = ChannelInvitationInvitee.Status.REJECTED
        invitee.responded_at = timezone.now()
        invitee.save(update_fields=["status", "responded_at"])
        return self.context["invitation"]


class ChannelInvitationSignSerializer(serializers.Serializer):
    def validate(self, attrs):
        invitation = self.context["invitation"]
        org = self.context["organization"]

        if invitation.status not in (
            ChannelInvitation.Status.DRAFT,
            ChannelInvitation.Status.SIGNING,
        ):
            raise serializers.ValidationError(
                "Only DRAFT or SIGNING invitations can be signed."
            )

        channel = invitation.channel
        if not channel.organizations.filter(pk=org.pk).exists():
            raise serializers.ValidationError(
                "Only channel members can sign."
            )

        if ChannelInvitationSignature.objects.filter(
            invitation=invitation, organization=org
        ).exists():
            raise serializers.ValidationError(
                "This organization has already signed."
            )

        return attrs

    def create(self, validated_data):
        invitation = self.context["invitation"]
        org = self.context["organization"]
        channel = invitation.channel
        agent_url = org.agent_url

        try:
            with open(invitation.artifact.path, "rb") as f:
                artifact_bytes = f.read()

            signed_bytes = sign_invitation_artifact(
                agent_url, channel.name, artifact_bytes
            )
        except Exception:
            invitation.status = ChannelInvitation.Status.FAILED
            invitation.error_message = "Signing operation failed."
            invitation.save(update_fields=["status", "error_message"])
            raise

        new_hash = hashlib.sha256(signed_bytes).hexdigest()

        with transaction.atomic():
            invitation = ChannelInvitation.objects.select_for_update().get(
                pk=invitation.pk
            )
            invitation.artifact.save(
                f"channel_update_{channel.name}.bin",
                ContentFile(signed_bytes),
            )
            invitation.artifact_hash = new_hash

            if invitation.status == ChannelInvitation.Status.DRAFT:
                invitation.status = ChannelInvitation.Status.SIGNING

            sig_count = invitation.signatures.count() + 1
            if sig_count >= invitation.required_signatures:
                invitation.status = ChannelInvitation.Status.READY

            invitation.save(update_fields=["artifact_hash", "status"])

            ChannelInvitationSignature.objects.create(
                invitation=invitation,
                organization=org,
                artifact_hash=new_hash,
            )

        return invitation

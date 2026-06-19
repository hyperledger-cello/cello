import hashlib
from typing import Dict, Any

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from channel.models import (
    Channel,
    ChannelInvitation,
    ChannelInvitationInvitee,
    ChannelInvitationSignature,
)
from channel.service import create, create_invitation_artifact, sign_invitation_artifact
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
        allow_empty=False,
    )
    required_signatures = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    def validate_organization_ids(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError(
                "Duplicated organizations are not allowed."
            )
        return value

    def validate(self, attrs):
        channel = self.context["channel"]
        creator = self.context["organization"]

        if not channel.organizations.filter(pk=creator.pk).exists():
            raise serializers.ValidationError(
                "Not a channel member."
            )

        org_ids = set(attrs["organization_ids"])
        existing = {
            o.id: o.name
            for o in Organization.objects.filter(pk__in=org_ids)
        }
        missing = [str(oid) for oid in org_ids if oid not in existing]
        if missing:
            raise serializers.ValidationError({
                "organization_ids": [
                    f"Organization does not exist: {oid}" for oid in missing
                ]
            })

        member_ids = set(channel.organizations.values_list("id", flat=True))
        already_members = [
            existing[oid] for oid in org_ids if oid in member_ids
        ]
        if already_members:
            raise serializers.ValidationError({
                "organization_ids": [
                    f"Already a member: {name}" for name in already_members
                ]
            })

        active_invitees = ChannelInvitationInvitee.objects.filter(
            organization__in=org_ids,
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
        required = attrs.get("required_signatures", member_count)
        if required > member_count:
            raise serializers.ValidationError({
                "required_signatures": "Cannot exceed member count."
            })

        attrs["organizations"] = Organization.objects.filter(
            pk__in=org_ids
        )
        attrs["required_signatures"] = required
        return attrs

    def create(self, validated_data):
        orgs = validated_data.pop("organizations")
        validated_data.pop("organization_ids")
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
        except Exception as e:
            invitation.status = ChannelInvitation.Status.FAILED
            invitation.error_message = str(e)
            invitation.save(update_fields=["status", "error_message"])
            raise

        new_hash = hashlib.sha256(signed_bytes).hexdigest()

        with transaction.atomic():
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

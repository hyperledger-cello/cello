from django.db import IntegrityError, transaction
from django.test import TestCase

from channel.models import (
    Channel,
    ChannelInvitation,
    ChannelInvitationInvitee,
    ChannelInvitationSignature,
)
from channel.serializers import ChannelInvitationCreateBody
from organization.models import Organization


class ChannelInvitationTestCase(TestCase):
    def setUp(self):
        self.member_org = Organization.objects.create(
            name="member.example.com",
            agent_url="http://member-agent.example.com",
        )
        self.second_member_org = Organization.objects.create(
            name="second.example.com",
            agent_url="http://second-agent.example.com",
        )
        self.invited_org = Organization.objects.create(
            name="invited.example.com",
            agent_url="http://invited-agent.example.com",
        )
        self.other_org = Organization.objects.create(
            name="other.example.com",
            agent_url="http://other-agent.example.com",
        )
        self.channel = Channel.objects.create(name="testchannel")
        self.channel.organizations.add(
            self.member_org,
            self.second_member_org,
        )

    def create_invitation(self, status=ChannelInvitation.Status.DRAFT):
        invitation = ChannelInvitation.objects.create(
            channel=self.channel,
            creator_organization=self.member_org,
            status=status,
            required_signatures=2,
        )
        ChannelInvitationInvitee.objects.create(
            invitation=invitation,
            organization=self.invited_org,
        )
        return invitation

    def test_invitation_defaults_to_draft(self):
        invitation = ChannelInvitation.objects.create(
            channel=self.channel,
            creator_organization=self.member_org,
        )

        self.assertEqual(invitation.status, ChannelInvitation.Status.DRAFT)
        self.assertEqual(invitation.artifact_hash, "")
        self.assertEqual(invitation.required_signatures, 0)

    def test_invitee_is_unique_per_invitation(self):
        invitation = self.create_invitation()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ChannelInvitationInvitee.objects.create(
                    invitation=invitation,
                    organization=self.invited_org,
                )

    def test_signature_is_unique_per_invitation(self):
        invitation = self.create_invitation()
        ChannelInvitationSignature.objects.create(
            invitation=invitation,
            organization=self.member_org,
            artifact_hash="a" * 64,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ChannelInvitationSignature.objects.create(
                    invitation=invitation,
                    organization=self.member_org,
                    artifact_hash="b" * 64,
                )

    def test_member_organization_can_see_draft_invitation(self):
        invitation = self.create_invitation()

        visible = ChannelInvitation.objects.visible_to_organization(
            self.member_org
        )

        self.assertIn(invitation, visible)

    def test_invited_organization_cannot_see_draft_invitation(self):
        invitation = self.create_invitation()

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertNotIn(invitation, visible)

    def test_invited_organization_can_see_ready_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.READY
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertIn(invitation, visible)

    def test_unrelated_organization_cannot_see_ready_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.READY
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.other_org
        )

        self.assertNotIn(invitation, visible)

    def test_member_organization_can_see_canceled_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.CANCELED
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.member_org
        )

        self.assertIn(invitation, visible)

    def test_invited_organization_cannot_see_canceled_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.CANCELED
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertNotIn(invitation, visible)

    def test_create_serializer_rejects_non_member_creator(self):
        serializer = ChannelInvitationCreateBody(
            data={"organization_ids": [self.invited_org.id]},
            context={
                "channel": self.channel,
                "organization": self.other_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_serializer_rejects_existing_member_invitee(self):
        serializer = ChannelInvitationCreateBody(
            data={"organization_ids": [self.second_member_org.id]},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("organization_ids", serializer.errors)

    def test_create_serializer_rejects_duplicate_invitees(self):
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_ids": [
                    self.invited_org.id,
                    self.invited_org.id,
                ]
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("organization_ids", serializer.errors)

    def test_create_serializer_rejects_too_many_required_signatures(self):
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_ids": [self.invited_org.id],
                "required_signatures": 3,
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("required_signatures", serializer.errors)

    def test_create_serializer_defaults_required_signatures(self):
        serializer = ChannelInvitationCreateBody(
            data={"organization_ids": [self.invited_org.id]},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        invitation = serializer.save()

        self.assertEqual(invitation.required_signatures, 2)

    def test_create_serializer_creates_invitation_and_invitees(self):
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_ids": [self.invited_org.id],
                "required_signatures": 1,
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        invitation = serializer.save()

        self.assertEqual(invitation.channel, self.channel)
        self.assertEqual(invitation.creator_organization, self.member_org)
        self.assertEqual(invitation.required_signatures, 1)
        self.assertEqual(invitation.invitees.count(), 1)
        self.assertEqual(
            invitation.invitees.get().organization,
            self.invited_org,
        )

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from channel.models import (
    Channel,
    ChannelInvitation,
    ChannelInvitationInvitee,
    ChannelInvitationSignature,
)
from channel.serializers import ChannelInvitationCreateBody
from organization.models import Organization
from user.models import UserProfile


class ChannelInvitationTestCase(TestCase):
    def setUp(self):
        self.member_org = Organization.objects.create(
            name="member.example.com",
            agent_url="http://member-agent.example.com",
            msp_id="MemberMSP",
        )
        self.second_member_org = Organization.objects.create(
            name="second.example.com",
            agent_url="http://second-agent.example.com",
            msp_id="SecondMSP",
        )
        self.invited_org = Organization.objects.create(
            name="invited.example.com",
            agent_url="http://invited-agent.example.com",
            msp_id="InvitedMSP",
        )
        self.other_org = Organization.objects.create(
            name="other.example.com",
            agent_url="http://other-agent.example.com",
            msp_id="OtherMSP",
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
        self.assertEqual(invitation.required_signatures, 1)

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

        self.assertIn(str(invitation.pk), [str(i.pk) for i in visible])

    def test_invited_organization_cannot_see_draft_invitation(self):
        invitation = self.create_invitation()

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertNotIn(str(invitation.pk), [str(i.pk) for i in visible])

    def test_invited_organization_can_see_ready_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.READY
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertIn(str(invitation.pk), [str(i.pk) for i in visible])

    def test_unrelated_organization_cannot_see_ready_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.READY
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.other_org
        )

        self.assertNotIn(str(invitation.pk), [str(i.pk) for i in visible])

    def test_member_organization_can_see_canceled_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.CANCELED
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.member_org
        )

        self.assertIn(str(invitation.pk), [str(i.pk) for i in visible])

    def test_invited_organization_cannot_see_canceled_invitation(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.CANCELED
        )

        visible = ChannelInvitation.objects.visible_to_organization(
            self.invited_org
        )

        self.assertNotIn(str(invitation.pk), [str(i.pk) for i in visible])

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

    def test_create_serializer_rejects_missing_org_selector(self):
        serializer = ChannelInvitationCreateBody(
            data={},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_serializer_rejects_both_org_selectors(self):
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_ids": [self.invited_org.id],
                "organization_names": [self.invited_org.name],
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_serializer_rejects_unknown_organization_name(self):
        serializer = ChannelInvitationCreateBody(
            data={"organization_names": ["missing.example.com"]},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("organization_names", serializer.errors)

    def test_create_serializer_rejects_duplicate_organization_names(self):
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_names": [
                    self.invited_org.name,
                    self.invited_org.name,
                ]
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("organization_names", serializer.errors)

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

    @patch("channel.serializers.create_invitation_artifact")
    def test_create_serializer_defaults_required_signatures(
        self, mock_create_artifact
    ):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        serializer = ChannelInvitationCreateBody(
            data={"organization_ids": [self.invited_org.id]},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        invitation = serializer.save()

        # 2 members → majority is 2
        self.assertEqual(invitation.required_signatures, 2)

    @patch("channel.serializers.create_invitation_artifact")
    def test_create_serializer_defaults_majority_with_three_members(
        self, mock_create_artifact
    ):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        third_member = Organization.objects.create(
            name="third.example.com",
            agent_url="http://third-agent.example.com",
            msp_id="ThirdMSP",
        )
        self.channel.organizations.add(third_member)

        serializer = ChannelInvitationCreateBody(
            data={"organization_names": [self.invited_org.name]},
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        invitation = serializer.save()

        # 3 members → majority is 2
        self.assertEqual(invitation.required_signatures, 2)

    @patch("channel.serializers.create_invitation_artifact")
    def test_create_serializer_creates_invitation_by_organization_names(
        self, mock_create_artifact
    ):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        serializer = ChannelInvitationCreateBody(
            data={
                "organization_names": [self.invited_org.name],
                "required_signatures": 1,
            },
            context={
                "channel": self.channel,
                "organization": self.member_org,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        invitation = serializer.save()

        self.assertEqual(invitation.invitees.count(), 1)
        self.assertEqual(
            str(invitation.invitees.get().organization.pk),
            str(self.invited_org.pk),
        )

    @patch("channel.serializers.create_invitation_artifact")
    def test_create_serializer_creates_invitation_and_invitees(
        self, mock_create_artifact
    ):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
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
            str(invitation.invitees.get().organization.pk),
            str(self.invited_org.pk),
        )


class ChannelInvitationEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.member_org = Organization.objects.create(
            name="member.example.com",
            agent_url="http://member-agent.example.com",
            msp_id="MemberMSP",
        )
        self.second_member_org = Organization.objects.create(
            name="second-member.example.com",
            agent_url="http://second-agent.example.com",
            msp_id="Second-memberMSP",
        )
        self.other_org = Organization.objects.create(
            name="other.example.com",
            agent_url="http://other-agent.example.com",
            msp_id="OtherMSP",
        )
        self.invited_org = Organization.objects.create(
            name="invited.example.com",
            agent_url="http://invited-agent.example.com",
            msp_id="InvitedMSP",
        )

        self.channel = Channel.objects.create(name="testchannel")
        self.channel.organizations.add(self.member_org, self.second_member_org)

        self.admin_user = UserProfile.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            organization=self.member_org,
            role=UserProfile.Role.ADMIN,
        )
        self.non_admin_user = UserProfile.objects.create_user(
            username="user",
            email="user@example.com",
            password="testpass123",
            organization=self.member_org,
            role=UserProfile.Role.USER,
        )
        self.second_admin_user = UserProfile.objects.create_user(
            username="second_admin",
            email="second@example.com",
            password="testpass123",
            organization=self.second_member_org,
            role=UserProfile.Role.ADMIN,
        )
        self.other_user = UserProfile.objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123",
            organization=self.other_org,
        )

        self.admin_token = str(
            RefreshToken.for_user(self.admin_user).access_token
        )
        self.user_token = str(
            RefreshToken.for_user(self.non_admin_user).access_token
        )
        self.second_admin_token = str(
            RefreshToken.for_user(self.second_admin_user).access_token
        )
        self.other_token = str(
            RefreshToken.for_user(self.other_user).access_token
        )

        self.invited_user = UserProfile.objects.create_user(
            username="invited",
            email="invited@example.com",
            password="testpass123",
            organization=self.invited_org,
        )
        self.invited_token = str(
            RefreshToken.for_user(self.invited_user).access_token
        )

    def _url(self, path=""):
        return f"/api/v1/channels/{self.channel.id}/{path}"

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    def create_invitation(self, status=ChannelInvitation.Status.DRAFT):
        invitation = ChannelInvitation.objects.create(
            channel=self.channel,
            creator_organization=self.member_org,
            status=status,
            required_signatures=1,
        )
        ChannelInvitationInvitee.objects.create(
            invitation=invitation,
            organization=self.invited_org,
        )
        return invitation

    def test_member_lists_invitations(self):
        self.create_invitation()
        self._auth(self.admin_token)

        resp = self.client.get(self._url("invitations"))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]["data"]), 1)

    def test_invitee_does_not_see_draft(self):
        self.create_invitation()
        self._auth(self.other_token)

        resp = self.client.get(self._url("invitations"))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]["data"]), 0)

    def test_invitee_sees_ready(self):
        self.create_invitation(status=ChannelInvitation.Status.READY)
        self._auth(self.invited_token)

        resp = self.client.get(self._url("invitations"))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]["data"]), 1)

    @patch("channel.serializers.create_invitation_artifact")
    def test_admin_creates_invitation(self, mock_create_artifact):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        self._auth(self.admin_token)

        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ChannelInvitation.objects.count(), 1
        )
        invitation = ChannelInvitation.objects.get()
        self.assertEqual(invitation.artifact_hash, "a" * 64)
        self.assertTrue(invitation.artifact)

    @patch("channel.serializers.create_invitation_artifact")
    def test_member_user_creates_invitation_by_name(self, mock_create_artifact):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        self._auth(self.user_token)

        resp = self.client.post(
            self._url("invitations"),
            {"organization_names": [self.invited_org.name]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChannelInvitation.objects.count(), 1)

    def test_non_member_cannot_create(self):
        self._auth(self.other_token)

        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_invitation(self):
        invitation = self.create_invitation()
        self._auth(self.admin_token)

        resp = self.client.get(
            self._url(f"invitations/{invitation.id}")
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data["data"]["id"], str(invitation.id)
        )

    def test_cancel_draft_invitation(self):
        invitation = self.create_invitation()
        self._auth(self.admin_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.status, ChannelInvitation.Status.CANCELED
        )

    def test_cancel_already_canceled_fails(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.CANCELED
        )
        self._auth(self.admin_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_admin_cancels_ready(self):
        invitation = self.create_invitation(
            status=ChannelInvitation.Status.READY,
        )
        self._auth(self.admin_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.status, ChannelInvitation.Status.CANCELED,
        )

    def test_member_admin_non_creator_cancels(self):
        invitation = self.create_invitation()
        self._auth(self.second_admin_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.status, ChannelInvitation.Status.CANCELED,
        )

    def test_non_admin_member_can_cancel(self):
        invitation = self.create_invitation()
        self._auth(self.user_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.status, ChannelInvitation.Status.CANCELED,
        )

    def test_unrelated_org_cannot_cancel(self):
        invitation = self.create_invitation()
        self._auth(self.other_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_invited_org_can_cancel(self):
        invitation = self.create_invitation()
        self._auth(self.invited_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.CANCELED)

    def test_invited_org_non_pending_cannot_cancel(self):
        invitation = self.create_invitation()
        invitee = invitation.invitees.get()
        invitee.status = ChannelInvitationInvitee.Status.ACCEPTED
        invitee.save()
        self._auth(self.invited_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch("channel.serializers.create_invitation_artifact")
    def test_reinvite_after_cancel(self, mock_create_artifact):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        invitation = self.create_invitation()
        self._auth(self.admin_token)

        self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @patch("channel.serializers.create_invitation_artifact")
    def test_reinvite_after_reject(self, mock_create_artifact):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        invitation = self.create_invitation()
        invitee = invitation.invitees.get()
        invitee.status = ChannelInvitationInvitee.Status.REJECTED
        invitee.save()

        self._auth(self.admin_token)
        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @patch("channel.serializers.create_invitation_artifact")
    def test_duplicate_active_invitation_blocked(self, mock_create_artifact):
        mock_create_artifact.return_value = (b"artifact", "a" * 64)
        self._auth(self.admin_token)

        self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("channel.serializers.create_invitation_artifact")
    def test_agent_failure_no_partial_state(self, mock_create_artifact):
        mock_create_artifact.side_effect = RuntimeError("Agent error")
        self._auth(self.admin_token)

        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invited_org.id]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(ChannelInvitation.objects.count(), 0)

    def _create_draft_invitation(self, required_signatures=1):
        resp = self.client.post(
            self._url("invitations"),
            {
                "organization_ids": [self.invited_org.id],
                "required_signatures": required_signatures,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return ChannelInvitation.objects.get()

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_admin_signs_draft_invitation(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.artifact_hash, "c630a95966de219529d790cf9274097eda29e25744f1674d720c908d9b52dbb4")
        self.assertEqual(ChannelInvitationSignature.objects.count(), 1)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_member_user_can_sign(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()
        self._auth(self.user_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(ChannelInvitationSignature.objects.count(), 1)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_sign_moves_draft_to_signing(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation(required_signatures=2)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.SIGNING)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_sign_moves_to_ready_when_threshold_met(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation(required_signatures=1)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.READY)

    @patch("channel.serializers.create_invitation_artifact")
    def test_non_member_cannot_sign(self, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()
        self._auth(self.other_token)

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_duplicate_sign_rejected(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation(required_signatures=2)

        self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_canceled_invitation_cannot_be_signed(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.return_value = b"signed-artifact"
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()

        self.client.post(
            self._url(f"invitations/{invitation.id}/cancel"),
            format="json",
        )

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("channel.serializers.create_invitation_artifact")
    @patch("channel.serializers.sign_invitation_artifact")
    def test_agent_failure_sets_failed_status(self, mock_sign, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        mock_sign.side_effect = RuntimeError("Agent unreachable")
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/sign"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.FAILED)
        self.assertEqual(invitation.error_message, "Signing operation failed.")

    def _create_ready_invitation(self, required_signatures=1):
        invitation = ChannelInvitation.objects.create(
            channel=self.channel,
            creator_organization=self.member_org,
            status=ChannelInvitation.Status.READY,
            required_signatures=required_signatures,
            artifact_hash="a" * 64,
        )
        invitation.artifact.save(
            "test_artifact.bin",
            ContentFile(b"test-artifact-data"),
        )
        ChannelInvitationInvitee.objects.create(
            invitation=invitation,
            organization=self.invited_org,
        )
        return invitation

    @patch("channel.serializers.accept_invitation")
    def test_invitee_accepts_ready_invitation(self, mock_accept):
        mock_accept.return_value = None
        self._auth(self.invited_token)
        invitation = self._create_ready_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/accept"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        invitee = ChannelInvitationInvitee.objects.get(
            invitation=invitation, organization=self.invited_org
        )
        self.assertEqual(invitee.status, ChannelInvitationInvitee.Status.ACCEPTED)
        org_ids = [str(pk) for pk in self.channel.organizations.values_list("pk", flat=True)]
        self.assertIn(str(self.invited_org.pk), org_ids)

    @patch("channel.serializers.create_invitation_artifact")
    def test_invitee_cannot_accept_before_ready(self, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()

        self._auth(self.invited_token)
        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/accept"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unrelated_org_cannot_accept(self):
        self._auth(self.other_token)
        invitation = self._create_ready_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/accept"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch("channel.serializers.accept_invitation")
    def test_agent_failure_on_accept_sets_failed(self, mock_accept):
        mock_accept.side_effect = RuntimeError("Agent unreachable")
        self._auth(self.invited_token)
        invitation = self._create_ready_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/accept"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.FAILED)
        self.assertEqual(invitation.error_message, "Accept operation failed.")
        invited_org_ids = [str(pk) for pk in self.channel.organizations.values_list("pk", flat=True)]
        self.assertNotIn(str(self.invited_org.pk), invited_org_ids)

    def test_invitee_rejects_ready_invitation(self):
        self._auth(self.invited_token)
        invitation = self._create_ready_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/reject"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        invitee = ChannelInvitationInvitee.objects.get(
            invitation=invitation, organization=self.invited_org
        )
        self.assertEqual(invitee.status, ChannelInvitationInvitee.Status.REJECTED)
        self.assertIsNotNone(invitee.responded_at)
        invited_org_ids = [str(pk) for pk in self.channel.organizations.values_list("pk", flat=True)]
        self.assertNotIn(str(self.invited_org.pk), invited_org_ids)

    @patch("channel.serializers.create_invitation_artifact")
    def test_invitee_cannot_reject_before_ready(self, mock_create):
        mock_create.return_value = (b"artifact", "a" * 64)
        self._auth(self.admin_token)
        invitation = self._create_draft_invitation()

        self._auth(self.invited_token)
        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/reject"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unrelated_org_cannot_reject(self):
        self._auth(self.other_token)
        invitation = self._create_ready_invitation()

        resp = self.client.post(
            self._url(f"invitations/{invitation.id}/reject"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

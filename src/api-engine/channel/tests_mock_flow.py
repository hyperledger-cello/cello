# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
"""
End-to-end mock flow tests for the channel invitation workflow.

These tests mock the AGENT HTTP layer (channel.service.requests) so the
full lifecycle runs without a real Fabric agent: create -> sign -> sign
-> accept. They verify context passing between each stage:

- URL construction for various agent_url formats
- artifact byte chaining across signatures (paper-contract semantics)
- artifact hash tracking
- state machine transitions (DRAFT -> SIGNING -> READY -> ACCEPTED)
- channel membership updates on accept
"""
import hashlib
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from channel.models import Channel, ChannelInvitation, ChannelInvitationInvitee
from organization.models import Organization
from user.models import UserProfile


class FakeResponse:
    def __init__(self, content=b"", status_code=200, json_data=None):
        self.content = content
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError("Unexpected HTTP {}".format(self.status_code))

    def json(self):
        return self._json


class FakeRequests:
    """Records all agent calls and returns deterministic artifacts.

    Simulates the agent: definition returns the raw artifact; sign returns
    the artifact with a signature marker appended (chain preserved); join
    succeeds.
    """

    def __init__(self):
        self.calls = []

    def _record(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})

    def get(self, url, **kwargs):
        self._record("GET", url, **kwargs)
        return FakeResponse()

    def post(self, url, **kwargs):
        self._record("POST", url, **kwargs)
        if url.endswith("/invitations/definition"):
            return FakeResponse(content=b"def-artifact")
        if url.endswith("/invitations/sign"):
            # chain semantics: keep prior bytes, append this signer marker
            signed = kwargs.get("data", b"") + b"+sig"
            return FakeResponse(content=signed)
        if url.endswith("/invitations/join"):
            return FakeResponse(content=kwargs.get("data", b""))
        return FakeResponse(content=b"{}")


class MockedInvitationFlowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.fake_requests = FakeRequests()

        self.creator_org = Organization.objects.create(
            name="creator.example.com",
            agent_url="http://creator-agent:8080",
            msp_id="CreatorMSP",
        )
        self.member2_org = Organization.objects.create(
            name="member2.example.com",
            agent_url="http://member2-agent:8080/api/v1",
            msp_id="Member2MSP",
        )
        self.invitee_org = Organization.objects.create(
            name="invitee.example.com",
            agent_url="http://invitee-agent:8080/api/v1/",
            msp_id="InviteeMSP",
        )
        self.other_org = Organization.objects.create(
            name="other.example.com",
            agent_url="http://other-agent:8080",
            msp_id="OtherMSP",
        )

        self.channel = Channel.objects.create(name="testchannel")
        self.channel.organizations.add(self.creator_org, self.member2_org)

        self.creator_admin = UserProfile.objects.create_user(
            username="creator-admin",
            email="creator@example.com",
            password="testpass123",
            organization=self.creator_org,
            role=UserProfile.Role.ADMIN,
        )
        self.member2_user = UserProfile.objects.create_user(
            username="member2-user",
            email="member2@example.com",
            password="testpass123",
            organization=self.member2_org,
        )
        self.invitee_user = UserProfile.objects.create_user(
            username="invitee-user",
            email="invitee@example.com",
            password="testpass123",
            organization=self.invitee_org,
        )
        self.other_user = UserProfile.objects.create_user(
            username="other-user",
            email="other@example.com",
            password="testpass123",
            organization=self.other_org,
        )

        self.creator_token = str(RefreshToken.for_user(self.creator_admin).access_token)
        self.member2_token = str(RefreshToken.for_user(self.member2_user).access_token)
        self.invitee_token = str(RefreshToken.for_user(self.invitee_user).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="JWT {}".format(token))

    def _url(self, path=""):
        return "/api/v1/channels/{}/{}".format(self.channel.id, path)

    def _agent_calls_to(self, endpoint_suffix):
        return [
            c for c in self.fake_requests.calls
            if c["url"].endswith(endpoint_suffix)
        ]

    @patch("channel.service.requests", autospec=True)
    def test_full_lifecycle_context_passing(self, mock_requests):
        mock_requests.get.side_effect = self.fake_requests.get
        mock_requests.post.side_effect = self.fake_requests.post

        # --- Stage 1: creator (admin) creates the invitation ---
        self._auth(self.creator_token)
        resp = self.client.post(
            self._url("invitations"),
            {"organization_names": [self.invitee_org.name]},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        invitation = ChannelInvitation.objects.get()
        self.assertEqual(invitation.status, ChannelInvitation.Status.DRAFT)
        # majority of 2 members = 2 required signatures
        self.assertEqual(invitation.required_signatures, 2)
        self.assertEqual(invitation.artifact_hash, hashlib.sha256(b"def-artifact").hexdigest())
        self.assertEqual(invitation.invitees.count(), 1)
        self.assertEqual(
            str(invitation.invitees.get().organization.pk),
            str(self.invitee_org.pk),
        )

        # definition call: creator's agent, channel name as pk, msp ids payload
        def_calls = self._agent_calls_to("/invitations/definition")
        self.assertEqual(len(def_calls), 1)
        self.assertTrue(
            def_calls[0]["url"].startswith("http://creator-agent:8080/api/v1/channels/"),
            def_calls[0]["url"],
        )
        self.assertEqual(
            def_calls[0]["json"], {"organization_msp_ids": ["InviteeMSP"]}
        )

        # --- Stage 2: creator signs -> DRAFT -> SIGNING ---
        with open(invitation.artifact.path, "rb") as f:
            draft_bytes = f.read()
        self.assertEqual(draft_bytes, b"def-artifact")

        resp = self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.SIGNING)
        self.assertEqual(invitation.signatures.count(), 1)
        self.assertEqual(
            invitation.artifact_hash, hashlib.sha256(b"def-artifact+sig").hexdigest()
        )

        # sign call: creator's agent, exact artifact bytes passed through
        sign_calls = self._agent_calls_to("/invitations/sign")
        self.assertEqual(len(sign_calls), 1)
        self.assertTrue(sign_calls[0]["url"].startswith("http://creator-agent:8080/"))
        self.assertEqual(sign_calls[0]["data"], b"def-artifact")

        # --- Stage 3: second member signs -> SIGNING -> READY ---
        self._auth(self.member2_token)
        resp = self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.READY)
        self.assertEqual(invitation.signatures.count(), 2)
        self.assertEqual(
            invitation.artifact_hash, hashlib.sha256(b"def-artifact+sig+sig").hexdigest()
        )

        # chain semantics: second signer received the FIRST signed artifact
        sign_calls = self._agent_calls_to("/invitations/sign")
        self.assertEqual(len(sign_calls), 2)
        self.assertTrue(sign_calls[1]["url"].startswith("http://member2-agent:8080/"))
        self.assertEqual(sign_calls[1]["data"], b"def-artifact+sig")

        # --- Stage 4: invitee sees the READY invitation and accepts ---
        self._auth(self.invitee_token)
        list_resp = self.client.get(self._url("invitations"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.data["data"]["data"]), 1)
        self.assertEqual(list_resp.data["data"]["data"][0]["status"], "READY")

        resp = self.client.post(
            self._url("invitations/{}/accept".format(invitation.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.ACCEPTED)
        invitee = invitation.invitees.get()
        self.assertEqual(invitee.status, ChannelInvitationInvitee.Status.ACCEPTED)
        self.assertIsNotNone(invitee.responded_at)
        self.assertTrue(
            self.channel.organizations.filter(pk=self.invitee_org.pk).exists()
        )

        # join call: invitee's agent, final signed artifact
        join_calls = self._agent_calls_to("/invitations/join")
        self.assertEqual(len(join_calls), 1)
        self.assertTrue(join_calls[0]["url"].startswith("http://invitee-agent:8080/"))
        self.assertEqual(join_calls[0]["data"], b"def-artifact+sig+sig")

        # --- Stage 5: unrelated org cannot see or act on the invitation ---
        self._auth(self.other_token)
        list_resp = self.client.get(self._url("invitations"))
        self.assertEqual(len(list_resp.data["data"]["data"]), 0)
        resp = self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    @patch("channel.service.requests", autospec=True)
    def test_agent_url_formats_all_resolve_to_api_v1(self, mock_requests):
        """agent_url with/without trailing slash or /api/v1 suffix must work."""
        mock_requests.get.side_effect = self.fake_requests.get
        mock_requests.post.side_effect = self.fake_requests.post

        self._auth(self.creator_token)
        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invitee_org.id]},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

        def_call = self._agent_calls_to("/invitations/definition")[0]
        # creator agent_url has no path: http://creator-agent:8080
        self.assertTrue(
            def_call["url"].startswith("http://creator-agent:8080/api/v1/"),
            def_call["url"],
        )

    @patch("channel.service.requests", autospec=True)
    def test_all_invitations_endpoint_visible_to_invitee(self, mock_requests):
        """Invitee discovers READY invitations via the non-nested endpoint."""
        mock_requests.get.side_effect = self.fake_requests.get
        mock_requests.post.side_effect = self.fake_requests.post

        self._auth(self.creator_token)
        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invitee_org.id]},
            format="json",
        )
        invitation = ChannelInvitation.objects.get()

        # DRAFT is not visible to the invitee yet
        self._auth(self.invitee_token)
        resp = self.client.get("/api/v1/invitations")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]["data"]), 0)

        # creator signs twice (required=2) -> READY, now visible
        self._auth(self.creator_token)
        self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)), format="json"
        )
        self._auth(self.member2_token)
        self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)), format="json"
        )
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.READY)

        self._auth(self.invitee_token)
        resp = self.client.get("/api/v1/invitations")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]["data"]
        self.assertEqual(len(data), 1)
        # channel name is included for display in the all-channels view
        self.assertEqual(data[0]["channel"]["name"], "testchannel")
        self.assertEqual(data[0]["invitees"][0]["organization"]["name"], "invitee.example.com")

    @patch("channel.service.requests", autospec=True)
    def test_reject_flow_marks_invitee_rejected(self, mock_requests):
        mock_requests.get.side_effect = self.fake_requests.get
        mock_requests.post.side_effect = self.fake_requests.post

        self._auth(self.creator_token)
        resp = self.client.post(
            self._url("invitations"),
            {"organization_ids": [self.invitee_org.id]},
            format="json",
        )
        invitation = ChannelInvitation.objects.get()

        # both members sign (required=2) -> READY
        self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)), format="json"
        )
        self._auth(self.member2_token)
        self.client.post(
            self._url("invitations/{}/sign".format(invitation.id)), format="json"
        )
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.READY)

        self._auth(self.invitee_token)
        resp = self.client.post(
            self._url("invitations/{}/reject".format(invitation.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.invitees.get().status, ChannelInvitationInvitee.Status.REJECTED
        )
        self.assertFalse(
            self.channel.organizations.filter(pk=self.invitee_org.pk).exists()
        )

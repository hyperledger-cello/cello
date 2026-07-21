# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
import os
import unittest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from channel.models import Channel, ChannelInvitation
from organization.models import Organization
from user.models import UserProfile


@unittest.skipIf(
    os.getenv("RUN_INTEGRATION_TESTS", "false").lower() != "true",
    "Skipping integration tests. Set RUN_INTEGRATION_TESTS=true to run."
)
class ChannelInvitationIntegrationTestCase(TestCase):
    """
    End-to-End integration tests for the Channel Invitation Workflow.
    These tests DO NOT mock the agent service calls. They require a real, 
    running Hyperledger Fabric agent container.
    """
    def setUp(self):
        # We assume the agent is reachable via the environment variable or defaults to localhost
        agent_host = os.getenv("AGENT_HOST", "localhost")
        agent_port = os.getenv("AGENT_PORT", "8080")
        agent_url = f"http://{agent_host}:{agent_port}/"

        self.org1 = Organization.objects.create(
            name="Org1",
            agent_url=f"{agent_url}org1",
            msp_id="Org1MSP",
        )
        self.org2 = Organization.objects.create(
            name="Org2",
            agent_url=f"{agent_url}org2",
            msp_id="Org2MSP",
        )
        self.org3 = Organization.objects.create(
            name="Org3",
            agent_url=f"{agent_url}org3",
            msp_id="Org3MSP",
        )

        self.channel = Channel.objects.create(name="mychannel")
        self.channel.organizations.add(self.org1, self.org2)

        self.admin_user = UserProfile.objects.create_user(
            username="admin1",
            email="admin1@test.cello.org",
            password="password",
            organization=self.org1,
            role=UserProfile.Role.ADMIN,
        )
        
        self.org2_admin = UserProfile.objects.create_user(
            username="admin2",
            email="admin2@test.cello.org",
            password="password",
            organization=self.org2,
            role=UserProfile.Role.ADMIN,
        )

        self.org3_admin = UserProfile.objects.create_user(
            username="admin3",
            email="admin3@test.cello.org",
            password="password",
            organization=self.org3,
            role=UserProfile.Role.ADMIN,
        )

        self.client = APIClient()

    def _authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_end_to_end_invitation_lifecycle(self):
        # 1. Org1 creates an invitation for Org3
        self._authenticate(self.admin_user)
        response = self.client.post(
            f"/api/v1/channels/{self.channel.id}/invitations",
            {
                "organization_names": ["Org3"],
                "required_signatures": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, f"Failed to create invitation: {response.data}")
        invitation_id = response.data["data"]["id"]
        
        invitation = ChannelInvitation.objects.get(id=invitation_id)
        self.assertEqual(invitation.status, ChannelInvitation.Status.DRAFT)
        self.assertTrue(bool(invitation.artifact))

        # 2. Org1 signs the invitation
        response = self.client.post(
            f"/api/v1/channels/{self.channel.id}/invitations/{invitation_id}/sign"
        )
        self.assertEqual(response.status_code, 200, f"Failed to sign invitation: {response.data}")
        
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.SIGNING)
        self.assertEqual(invitation.signatures.count(), 1)

        # 3. Org2 signs the invitation (reaches threshold)
        self._authenticate(self.org2_admin)
        response = self.client.post(
            f"/api/v1/channels/{self.channel.id}/invitations/{invitation_id}/sign"
        )
        self.assertEqual(response.status_code, 200)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.READY)
        self.assertEqual(invitation.signatures.count(), 2)

        # 4. Org3 accepts the invitation and joins the channel
        self._authenticate(self.org3_admin)
        response = self.client.post(
            f"/api/v1/channels/{self.channel.id}/invitations/{invitation_id}/accept"
        )
        self.assertEqual(response.status_code, 200, f"Failed to accept invitation: {response.data}")

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelInvitation.Status.ACCEPTED)
        
        # Verify Org3 is now a member of the channel
        self.assertTrue(self.channel.organizations.filter(id=self.org3.id).exists())

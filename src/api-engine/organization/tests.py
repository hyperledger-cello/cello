#
# SPDX-License-Identifier: Apache-2.0
#
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Organization
from user.models import UserProfile


class OrganizationDeletePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="target.example.com",
            agent_url="http://target-agent.example.com",
            msp_id="TargetMSP",
        )
        self.user_organization = Organization.objects.create(
            name="member.example.com",
            agent_url="http://member-agent.example.com",
            msp_id="MemberMSP",
        )
        self.admin_user = UserProfile.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            organization=self.organization,
            role=UserProfile.Role.ADMIN,
        )
        self.member_user = UserProfile.objects.create_user(
            username="member",
            email="member@example.com",
            password="testpass123",
            organization=self.user_organization,
            role=UserProfile.Role.USER,
        )
        self.admin_token = str(
            RefreshToken.for_user(self.admin_user).access_token
        )
        self.member_token = str(
            RefreshToken.for_user(self.member_user).access_token
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    def _url(self, organization=None):
        organization = organization or self.organization
        return f"/api/v1/organizations/{organization.id}"

    def test_non_admin_cannot_delete_organization(self):
        self._auth(self.member_token)

        response = self.client.delete(self._url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Organization.objects.filter(pk=self.organization.pk).exists()
        )

    def test_admin_can_delete_organization(self):
        self._auth(self.admin_token)

        response = self.client.delete(self._url())

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Organization.objects.filter(pk=self.organization.pk).exists()
        )

    def test_admin_gets_404_for_missing_organization(self):
        self._auth(self.admin_token)

        response = self.client.delete(
            "/api/v1/organizations/00000000-0000-0000-0000-000000000000"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_delete_organization(self):
        response = self.client.delete(self._url())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            Organization.objects.filter(pk=self.organization.pk).exists()
        )

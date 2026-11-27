#
# SPDX-License-Identifier: Apache-2.0
#
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Organization
from organization.serializers import OrganizationUpdateBody
from user.models import UserProfile


class OrganizationUpdateBodyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="org.example.com",
            agent_url="https://agent.example.com",
            msp_id="Org1MSP",
        )
        self.other_organization = Organization.objects.create(
            name="other.example.com",
            agent_url="https://other-agent.example.com",
            msp_id="OtherMSP",
        )

    def update_organization(self, data):
        serializer = OrganizationUpdateBody(
            data=data,
            context={"organization": self.organization},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_can_clear_agent_url(self):
        self.update_organization({
            "name": self.organization.name,
            "agent_url": "",
        })

        self.organization.refresh_from_db()
        self.assertIsNone(self.organization.agent_url)
        self.assertEqual(self.organization.msp_id, "Org1MSP")

    def test_can_clear_agent_url_with_explicit_null(self):
        self.update_organization({
            "name": self.organization.name,
            "agent_url": None,
        })

        self.organization.refresh_from_db()
        self.assertIsNone(self.organization.agent_url)
        self.assertEqual(self.organization.msp_id, "Org1MSP")

    def test_can_clear_msp_id(self):
        self.update_organization({
            "name": self.organization.name,
            "msp_id": "",
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.msp_id, "")
        self.assertEqual(self.organization.agent_url, "https://agent.example.com")

    def test_explicit_null_msp_id_is_rejected(self):
        serializer = OrganizationUpdateBody(
            data={
                "name": self.organization.name,
                "msp_id": None,
            },
            context={"organization": self.organization},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("msp_id", serializer.errors)

    def test_omitted_optional_fields_are_preserved(self):
        self.update_organization({
            "name": "updated.example.com",
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "updated.example.com")
        self.assertEqual(self.organization.agent_url, "https://agent.example.com")
        self.assertEqual(self.organization.msp_id, "Org1MSP")

    def test_can_update_both_optional_fields_together(self):
        self.update_organization({
            "name": self.organization.name,
            "agent_url": "https://new-agent.example.com",
            "msp_id": "UpdatedOrg1MSP",
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "org.example.com")
        self.assertEqual(
            self.organization.agent_url, "https://new-agent.example.com"
        )
        self.assertEqual(self.organization.msp_id, "UpdatedOrg1MSP")

    def test_valid_update_with_unchanged_and_changed_values(self):
        self.update_organization({
            "name": "renamed.example.com",
            "agent_url": self.organization.agent_url,
            "msp_id": self.organization.msp_id,
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "renamed.example.com")
        self.assertEqual(self.organization.agent_url, "https://agent.example.com")
        self.assertEqual(self.organization.msp_id, "Org1MSP")

    def test_invalid_agent_url_is_rejected(self):
        for bad_url in ("not-a-url", "http://", "ws://agent.example.com"):
            with self.subTest(agent_url=bad_url):
                serializer = OrganizationUpdateBody(
                    data={
                        "name": self.organization.name,
                        "agent_url": bad_url,
                    },
                    context={"organization": self.organization},
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("agent_url", serializer.errors)

    def test_duplicate_values_from_other_organization_are_rejected(self):
        for field, value in (
            ("name", self.other_organization.name),
            ("agent_url", self.other_organization.agent_url),
            ("msp_id", self.other_organization.msp_id),
        ):
            with self.subTest(field=field):
                payload = {
                    "name": self.organization.name,
                    "agent_url": self.organization.agent_url,
                    "msp_id": self.organization.msp_id,
                    field: value,
                }
                serializer = OrganizationUpdateBody(
                    data=payload,
                    context={"organization": self.organization},
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)


class OrganizationUpdateEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="org.example.com",
            agent_url="https://agent.example.com",
            msp_id="Org1MSP",
        )
        self.other_organization = Organization.objects.create(
            name="other.example.com",
            agent_url="https://other-agent.example.com",
            msp_id="OtherMSP",
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
            organization=self.organization,
            role=UserProfile.Role.USER,
        )
        self.admin_token = str(
            RefreshToken.for_user(self.admin_user).access_token
        )
        self.member_token = str(
            RefreshToken.for_user(self.member_user).access_token
        )
        self.url = f"/api/v1/organizations/{self.organization.id}"

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    def test_put_clears_optional_fields_and_preserves_omitted(self):
        self._auth(self.admin_token)

        res = self.client.put(
            self.url,
            {"name": self.organization.name, "agent_url": ""},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "SUCCESSFUL")
        self.assertIsNone(res.data["data"]["agent_url"])
        self.assertEqual(res.data["data"]["msp_id"], "Org1MSP")

        res = self.client.put(
            self.url,
            {"name": "updated.example.com", "msp_id": ""},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["data"]["name"], "updated.example.com")
        self.assertIsNone(res.data["data"]["agent_url"])
        self.assertEqual(res.data["data"]["msp_id"], "")

    def test_put_rejects_invalid_url_and_duplicates(self):
        self._auth(self.admin_token)

        res = self.client.put(
            self.url,
            {"name": self.organization.name, "agent_url": "not-a-url"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.put(
            self.url,
            {"name": self.other_organization.name},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_requires_admin_role(self):
        self._auth(self.member_token)

        res = self.client.put(
            self.url,
            {"name": "blocked.example.com"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

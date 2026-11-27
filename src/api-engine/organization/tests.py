#
# SPDX-License-Identifier: Apache-2.0
#
from django.test import TestCase

from organization.models import Organization
from organization.serializers import OrganizationUpdateBody


class OrganizationUpdateBodyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="org.example.com",
            agent_url="https://agent.example.com",
            msp_id="Org1MSP",
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

    def test_can_clear_msp_id(self):
        self.update_organization({
            "name": self.organization.name,
            "msp_id": "",
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.msp_id, "")

    def test_omitted_optional_fields_are_preserved(self):
        self.update_organization({
            "name": "updated.example.com",
        })

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "updated.example.com")
        self.assertEqual(self.organization.agent_url, "https://agent.example.com")
        self.assertEqual(self.organization.msp_id, "Org1MSP")

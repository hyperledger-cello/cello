from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from chaincode.models import Chaincode
from chaincode.serializers import ChaincodeCreateBody
from channel.models import Channel
from organization.models import Organization
from user.models import UserProfile


class ChaincodeSequenceTestCase(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="org.example.com",
            agent_url="http://org-agent.example.com",
        )
        self.user = UserProfile.objects.create_user(
            username="ccuser",
            email="ccuser@example.com",
            password="password",
            organization=self.organization,
        )
        self.channel = Channel.objects.create(name="mychannel")
        self.channel.organizations.add(self.organization)
        self.context = {
            "user": self.user,
            "organization": self.organization,
        }

    def _package(self):
        return SimpleUploadedFile(
            "basic.tar.gz",
            b"fake-package-content",
            content_type="application/gzip",
        )

    def _base_data(self, **overrides):
        data = {
            "name": "basic",
            "version": "1.0",
            "package": self._package(),
            "channel": self.channel.id,
        }
        data.update(overrides)
        return data

    @patch("chaincode.serializers.metadata_exists", return_value=True)
    def test_omitted_sequence_defaults_to_one(self, _mock_metadata):
        serializer = ChaincodeCreateBody(
            data=self._base_data(),
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["sequence"], 1)

    @patch("chaincode.serializers.metadata_exists", return_value=True)
    def test_explicit_sequence_is_preserved(self, _mock_metadata):
        serializer = ChaincodeCreateBody(
            data=self._base_data(sequence=3),
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["sequence"], 3)

    @patch("chaincode.serializers.metadata_exists", return_value=True)
    def test_invalid_sequence_is_rejected(self, _mock_metadata):
        for invalid_sequence in (0, -1):
            with self.subTest(sequence=invalid_sequence):
                serializer = ChaincodeCreateBody(
                    data=self._base_data(sequence=invalid_sequence),
                    context=self.context,
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn("sequence", serializer.errors)

    @patch("chaincode.serializers.metadata_exists", return_value=True)
    @patch("chaincode.serializers.create_chaincode")
    def test_upgrade_sequence_is_accepted(
        self,
        mock_create_chaincode,
        _mock_metadata,
    ):
        # Fabric requires sequence to increment on definition upgrades.
        created_id = uuid4()
        mock_create_chaincode.return_value = Chaincode(id=created_id)

        serializer = ChaincodeCreateBody(
            data=self._base_data(version="2.0", sequence=2),
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["sequence"], 2)

        result = serializer.save()
        self.assertEqual(str(result.data["id"]), str(created_id))
        mock_create_chaincode.assert_called_once()
        self.assertEqual(
            mock_create_chaincode.call_args.kwargs["sequence"],
            2,
        )

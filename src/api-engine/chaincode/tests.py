#
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from chaincode.models import Chaincode
from chaincode.serializers import ChaincodeCreateBody
from chaincode.service import ChaincodeAction, get_chaincode
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


class ChaincodeLifecycleValidationAndAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.member_org = Organization.objects.create(
            name="org1.example.com",
            agent_url="http://org1-agent.example.com",
            msp_id="Org1MSP",
        )
        self.other_org = Organization.objects.create(
            name="org2.example.com",
            agent_url="http://org2-agent.example.com",
            msp_id="Org2MSP",
        )
        self.member_user = UserProfile.objects.create_user(
            username="org1user",
            email="org1user@example.com",
            password="password",
            organization=self.member_org,
        )
        self.other_user = UserProfile.objects.create_user(
            username="org2user",
            email="org2user@example.com",
            password="password",
            organization=self.other_org,
        )
        self.member_token = str(
            RefreshToken.for_user(self.member_user).access_token
        )
        self.other_token = str(
            RefreshToken.for_user(self.other_user).access_token
        )

        self.channel = Channel.objects.create(name="mychannel")
        self.channel.organizations.add(self.member_org)

        self.other_channel = Channel.objects.create(name="otherchannel")
        self.other_channel.organizations.add(self.other_org)

        self.chaincode = Chaincode.objects.create(
            package_id="basic_1.0:abc123",
            package=SimpleUploadedFile(
                "basic.tar.gz",
                b"fake-package-content",
                content_type="application/gzip",
            ),
            name="basic",
            version="1.0",
            sequence=1,
            label="basic_1.0",
            creator=self.member_user,
            channel=self.channel,
            language="golang",
        )
        self.other_chaincode = Chaincode.objects.create(
            package_id="other_1.0:def456",
            package=SimpleUploadedFile(
                "other.tar.gz",
                b"fake-other-content",
                content_type="application/gzip",
            ),
            name="other",
            version="1.0",
            sequence=1,
            label="other_1.0",
            creator=self.other_user,
            channel=self.other_channel,
            language="golang",
        )
        self.member_org.refresh_from_db()
        self.chaincode.refresh_from_db()
        self.other_chaincode.refresh_from_db()

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    def _action_url(self, chaincode_id, action_name):
        return f"/api/v1/chaincodes/{chaincode_id}/{action_name}"

    def test_get_chaincode_returns_none_when_missing(self):
        self.assertIsNone(get_chaincode(uuid4()))

    def test_get_chaincode_returns_instance_when_present(self):
        found = get_chaincode(self.chaincode.id)
        self.assertEqual(found, self.chaincode)

    def test_lifecycle_actions_return_400_for_nonexistent_chaincode(self):
        self._auth(self.member_token)
        missing_id = uuid4()
        for action_name, payload in (
            ("install", None),
            ("approve", None),
            ("commit", None),
            ("transact", {"action": "EVALUATE", "function": "GetAllAssets"}),
        ):
            with self.subTest(action=action_name):
                res = self.client.put(
                    self._action_url(missing_id, action_name),
                    payload,
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lifecycle_actions_return_400_for_invalid_uuid(self):
        self._auth(self.member_token)
        for action_name, payload in (
            ("install", None),
            ("approve", None),
            ("commit", None),
            ("transact", {"action": "EVALUATE", "function": "GetAllAssets"}),
        ):
            with self.subTest(action=action_name):
                res = self.client.put(
                    self._action_url("not-a-uuid", action_name),
                    payload,
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lifecycle_actions_require_authentication(self):
        for action_name, payload in (
            ("install", None),
            ("approve", None),
            ("commit", None),
            ("transact", {"action": "EVALUATE", "function": "GetAllAssets"}),
        ):
            with self.subTest(action=action_name):
                res = self.client.put(
                    self._action_url(self.chaincode.id, action_name),
                    payload,
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("chaincode.serializers.send_chaincode_request")
    @patch("chaincode.serializers.commit_chaincode")
    @patch("chaincode.serializers.approve_chaincode")
    @patch("chaincode.serializers.install_chaincode")
    def test_non_member_organization_cannot_operate_on_chaincode(
        self,
        mock_install,
        mock_approve,
        mock_commit,
        mock_transact,
    ):
        self._auth(self.other_token)
        for action_name, payload in (
            ("install", None),
            ("approve", None),
            ("commit", None),
            ("transact", {"action": "EVALUATE", "function": "GetAllAssets"}),
        ):
            with self.subTest(action=action_name):
                res = self.client.put(
                    self._action_url(self.chaincode.id, action_name),
                    payload,
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        mock_install.assert_not_called()
        mock_approve.assert_not_called()
        mock_commit.assert_not_called()
        mock_transact.assert_not_called()

    @patch("chaincode.serializers.send_chaincode_request")
    @patch("chaincode.serializers.commit_chaincode")
    @patch("chaincode.serializers.approve_chaincode")
    @patch("chaincode.serializers.install_chaincode")
    def test_member_organization_can_operate_on_chaincode(
        self,
        mock_install,
        mock_approve,
        mock_commit,
        mock_transact,
    ):
        self._auth(self.member_token)

        res = self.client.put(
            self._action_url(self.chaincode.id, "install"),
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_install.assert_called_once_with(self.member_org, self.chaincode)

        res = self.client.put(
            self._action_url(self.chaincode.id, "approve"),
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_approve.assert_called_once_with(self.member_org, self.chaincode)

        res = self.client.put(
            self._action_url(self.chaincode.id, "commit"),
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_commit.assert_called_once_with(self.member_org, self.chaincode)

        res = self.client.put(
            self._action_url(self.chaincode.id, "transact"),
            {
                "action": "SUBMIT",
                "function": "CreateAsset",
                "arguments": ["asset1", "blue"],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_transact.assert_called_once_with(
            self.member_org,
            self.chaincode,
            ChaincodeAction.SUBMIT,
            "CreateAsset",
            "asset1",
            "blue",
        )

    @patch("chaincode.serializers.send_chaincode_request")
    def test_transact_rejects_non_object_body_with_400(self, mock_transact):
        self._auth(self.member_token)
        res = self.client.put(
            self._action_url(self.chaincode.id, "transact"),
            ["unexpected", "list"],
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_transact.assert_not_called()

    @patch("chaincode.serializers.send_chaincode_request")
    def test_transact_url_pk_cannot_be_overridden_by_body_id(self, mock_transact):
        self._auth(self.member_token)
        res = self.client.put(
            self._action_url(self.chaincode.id, "transact"),
            {
                "id": str(self.other_chaincode.id),
                "action": "EVALUATE",
                "function": "GetAllAssets",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_transact.assert_called_once_with(
            self.member_org,
            self.chaincode,
            ChaincodeAction.EVALUATE,
            "GetAllAssets",
        )

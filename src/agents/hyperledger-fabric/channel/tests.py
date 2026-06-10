import json
import os
import subprocess
from unittest.mock import MagicMock, call, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from channel.serializers import InvitationDefinitionSerializer
from channel.service import generate_invitation_definition


FAKE_CRYPTO_CONFIG = {
    "PeerOrgs": [
        {
            "Name": "Org1",
            "Domain": "org1.example.com",
            "Specs": [{"Hostname": "peer0"}],
        },
        {
            "Name": "Org2",
            "Domain": "org2.example.com",
            "Specs": [{"Hostname": "peer0"}],
        },
    ],
    "OrdererOrgs": [
        {
            "Name": "Orderer",
            "Domain": "example.com",
            "Specs": [{"Hostname": "orderer"}],
        }
    ],
}

FAKE_CONFIG_BLOCK = {
    "data": {
        "data": [
            {
                "payload": {
                    "data": {
                        "config": {
                            "channel_group": {
                                "groups": {
                                    "Application": {
                                        "groups": {
                                            "Org1": {
                                                "values": {"MSP": {"version": 0}},
                                                "policies": {},
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    }
}

FAKE_CONFIG_UPDATE = {
    "read_set": {},
    "write_set": {},
    "type": 0,
}


class InvitationDefinitionSerializerTest(TestCase):
    def test_serializer_accepts_valid_data(self):
        serializer = InvitationDefinitionSerializer(
            data={"organization_msp_ids": ["Org1MSP", "Org2MSP"]},
            context={"channel_name": "testchannel"},
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_requires_msp_ids(self):
        serializer = InvitationDefinitionSerializer(
            data={},
            context={"channel_name": "testchannel"},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("organization_msp_ids", serializer.errors)


class GenerateInvitationDefinitionTest(TestCase):
    def setUp(self):
        self.channel_name = "testchannel"
        self.org_msp_ids = ["Org2MSP"]

    @patch("channel.service.CRYPTO_CONFIG", "/fake/crypto-config.yaml")
    @patch("channel.service.CELLO_HOME", "/fake/cello")
    @patch("channel.service.FABRIC_TOOL", "/fake/bin")
    @patch("channel.service._read_crypto_config", return_value=FAKE_CRYPTO_CONFIG)
    @patch("channel.service._read_b64", return_value="ZmFrZQ==")
    @patch("channel.service.subprocess.run")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.remove")
    @patch("os.makedirs")
    def test_generates_artifact(self, mock_makedirs, mock_remove, mock_open,
                                mock_subprocess, mock_read_b64, mock_read_crypto):
        read_values = [
            json.dumps(FAKE_CONFIG_BLOCK).encode(),
            json.dumps(FAKE_CONFIG_UPDATE).encode(),
            b"artifact-data",
        ]
        mock_fp = MagicMock()
        mock_fp.__enter__.return_value = mock_fp
        mock_fp.read.side_effect = read_values
        mock_open.return_value = mock_fp

        artifact = generate_invitation_definition(self.channel_name, self.org_msp_ids)

        self.assertIsNotNone(artifact)
        self.assertGreater(len(artifact), 0)

    @patch("channel.service.CRYPTO_CONFIG", "/fake/crypto-config.yaml")
    @patch("channel.service.CELLO_HOME", "/fake/cello")
    @patch("channel.service.FABRIC_TOOL", "/fake/bin")
    @patch("channel.service._read_crypto_config", return_value=FAKE_CRYPTO_CONFIG)
    @patch("channel.service._read_b64", return_value="ZmFrZQ==")
    @patch("channel.service.subprocess.run")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.remove")
    @patch("os.makedirs")
    def test_cleans_up_temp_files(self, mock_makedirs, mock_remove, mock_open,
                                  mock_subprocess, mock_read_b64, mock_read_crypto):
        mock_fp = MagicMock()
        mock_fp.__enter__.return_value = mock_fp
        mock_fp.read.side_effect = [
            json.dumps(FAKE_CONFIG_BLOCK).encode(),
            json.dumps(FAKE_CONFIG_UPDATE).encode(),
            b"artifact-data",
        ]
        mock_open.return_value = mock_fp

        generate_invitation_definition(self.channel_name, self.org_msp_ids)

        mock_remove.assert_called()

    @patch("channel.service.CRYPTO_CONFIG", "/fake/crypto-config.yaml")
    @patch("channel.service.CELLO_HOME", "/fake/cello")
    @patch("channel.service.FABRIC_TOOL", "/fake/bin")
    @patch("channel.service._read_crypto_config", return_value=FAKE_CRYPTO_CONFIG)
    @patch("channel.service._read_b64", return_value="ZmFrZQ==")
    @patch("channel.service.subprocess.run",
           side_effect=subprocess.CalledProcessError(1, "peer"))
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.remove")
    @patch("os.makedirs")
    def test_subprocess_failure_surfaces_error(self, mock_makedirs, mock_remove,
                                                mock_open, mock_subprocess,
                                                mock_read_b64, mock_read_crypto):
        mock_fp = MagicMock()
        mock_fp.__enter__.return_value = mock_fp
        mock_open.return_value = mock_fp

        with self.assertRaises(subprocess.CalledProcessError):
            generate_invitation_definition(self.channel_name, self.org_msp_ids)


class InvitationDefinitionEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.channel_name = "testchannel"
        self.url = f"/api/v1/channels/{self.channel_name}/invitations/definition"

    @patch("channel.views.InvitationDefinitionSerializer")
    def test_endpoint_returns_200_with_binary(self, mock_serializer_cls):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = {"artifact": b"fake-artifact-data"}
        mock_serializer_cls.return_value = mock_serializer

        resp = self.client.post(
            self.url,
            {"organization_msp_ids": ["Org2MSP"]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/octet-stream")
        self.assertEqual(resp.content, b"fake-artifact-data")

    def test_endpoint_returns_400_for_invalid_input(self):
        resp = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

from unittest.mock import MagicMock, mock_open, patch

import docker
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from node.serializers import NodeLogsRequestSerializer
from node.views import NodeViewSet

CRYPTO_YAML = "PeerOrgs:\n  - Domain: org1.example.com\nOrdererOrgs:\n  - Domain: orderer.example.com\n"


class NodeLogsServiceTests(TestCase):
    @patch("node.service.open", new_callable=mock_open, read_data=CRYPTO_YAML)
    @patch("node.service.docker_client")
    def test_get_node_logs_returns_decoded_string(self, mock_docker, _mock_open):
        mock_container = MagicMock()
        mock_container.logs.return_value = b"line1\nline2\n"
        mock_docker.containers.get.return_value = mock_container

        from node.service import get_node_logs

        logs = get_node_logs("PEER", "peer0", tail=10)
        self.assertEqual(logs, "line1\nline2\n")
        mock_docker.containers.get.assert_called_once_with("peer0.org1.example.com")
        mock_container.logs.assert_called_once_with(tail=10, timestamps=False)

    @patch("node.service.open", new_callable=mock_open, read_data=CRYPTO_YAML)
    @patch("node.service.docker_client")
    def test_get_node_logs_orderer_domain(self, mock_docker, _mock_open):
        mock_container = MagicMock()
        mock_container.logs.return_value = b"orderer log"
        mock_docker.containers.get.return_value = mock_container

        from node.service import get_node_logs

        logs = get_node_logs("ORDERER", "orderer0")
        self.assertEqual(logs, "orderer log")
        mock_docker.containers.get.assert_called_once_with("orderer0.orderer.example.com")


class NodeLogsSerializerTests(TestCase):
    def test_valid_with_defaults(self):
        s = NodeLogsRequestSerializer(data={"type": "PEER", "name": "peer0"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["tail"], 200)

    def test_tail_bounds(self):
        s = NodeLogsRequestSerializer(data={"type": "PEER", "name": "peer0", "tail": 0})
        self.assertFalse(s.is_valid())
        s = NodeLogsRequestSerializer(data={"type": "PEER", "name": "peer0", "tail": 1001})
        self.assertFalse(s.is_valid())
        s = NodeLogsRequestSerializer(data={"type": "PEER", "name": "peer0", "tail": 50})
        self.assertTrue(s.is_valid(), s.errors)


class NodeLogsViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = NodeViewSet.as_view({"get": "logs"})

    @patch("node.serializers.get_node_logs", return_value="some logs")
    def test_logs_returns_200(self, _mock_logs):
        request = self.factory.get("/api/v1/nodes/logs?type=PEER&name=peer0&tail=10")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["logs"], "some logs")

    def test_logs_missing_params_returns_400(self):
        request = self.factory.get("/api/v1/nodes/logs?type=PEER")
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

    @patch("node.serializers.get_node_logs", side_effect=docker.errors.NotFound("not found"))
    def test_logs_not_found_returns_404(self, _mock_logs):
        request = self.factory.get("/api/v1/nodes/logs?type=PEER&name=missing")
        response = self.view(request)
        self.assertEqual(response.status_code, 404)

import base64
import os
from zipfile import ZipFile

import yaml
from rest_framework import serializers

from api.common.serializers import PageQuerySerializer, ListResponseSerializer
from api.config import CELLO_HOME
from api.lib.pki import CryptoConfig, CryptoGen
from node.enums import NodeType
from node.models import Node


class NodeQuery(PageQuerySerializer):
    class Meta:
        fields = (
            "page",
            "per_page",
        )


class NodeIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of node")


class NodeResponseSerializer(NodeIDSerializer, serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            "created_at",
            "status",
            "organization",
            "cid",
        )


class NodeListSerializer(ListResponseSerializer):
    total = serializers.IntegerField(
        help_text="Total number of node", min_value=0
    )
    data = NodeResponseSerializer(many=True, help_text="Nodes list")


class NodeCreateBody(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = (
            "name",
            "type",
        )
        extra_kwargs = {
            "name": {"required": True},
            "type": {"required": True},
        }

    def validate(self, data):
        if any(node.name == data["name"] for node in self.context["request"].user.organization.agent.nodes):
            raise serializers.ValidationError("Node Exists")
        return data

    def create(self, validated_data):
        organization_name = self.context["request"].user.organization.name
        node_type = validated_data["type"]
        node_name = validated_data["name"]
        CryptoConfig(organization_name).update({"type": node_type, "Specs": [node_name]})
        CryptoGen(organization_name).extend()
        self._generate_node_config(node_type, organization_name, node_name)


    def _generate_node_config(self, node_type: NodeType, organization_name: str, node_name: str) -> None:
        if node_type == NodeType.Peer:
            self._generate_peer_config(organization_name, node_name)
        elif node_type == NodeType.Orderer:
            self._generate_orderer_config(organization_name, node_name)
        # throw exception here
        pass

    def _generate_peer_config(self, organization_name: str, peer_name: str) -> None:
        peer_full_name = "{}.{}".format(peer_name, organization_name)
        self._generate_config(
            "/opt/node/core.yaml.bak",
            os.path.join(
                self._get_peer_directory(organization_name, peer_name),
                "core.yaml"),
            **{
                "peer_tls_enabled": True,
                "operations_listenAddress": "{}:9444".format(peer_full_name),
                "peer_address": "{}:7051".format(peer_full_name),
                "peer_gossip_bootstrap": "{}:7051".format(peer_full_name),
                "peer_gossip_externalEndpoint": "{}:7051".format(peer_full_name),
                "peer_id": peer_full_name,
                "peer_localMspId": "{}MSP".format(organization_name.capitalize()),
                "peer_mspConfigPath": "/etc/hyperledger/fabric/msp",
                "peer_tls_cert_file": "/etc/hyperledger/fabric/tls/server.crt",
                "peer_tls_key_file": "/etc/hyperledger/fabric/tls/server.key",
                "peer_tls_rootcert_file": "/etc/hyperledger/fabric/tls/ca.crt",
                "vm_docker_hostConfig_NetworkMode": "cello_net",
                "vm_endpoint": "unix:///host/var/run/docker.sock"
            }
        )

    def _generate_orderer_config(self, organization_name: str, orderer_name: str) -> None:
        organization_domain = organization_name.split(".", 1)[1]
        orderer_full_name = "{}.{}".format(orderer_name, organization_domain)
        self._generate_config(
            "/opt/node/orderer.yaml.bak",
            os.path.join(
                self._get_orderer_directory(organization_name, orderer_name),
                "orderer.yaml"),
            **{
                "Admin_TLS_Enabled": True,
                "Admin_ListenAddress": "0.0.0.0:7053",
                "Admin_TLS_Certificate": "/etc/hyperledger/fabric/tls/server.crt",
                "Admin_TLS_PrivateKey": "/etc/hyperledger/fabric/tls/server.key",
                "ChannelParticipation_Enabled": True,
                "General_Cluster_ClientCertificate": "/etc/hyperledger/fabric/tls/server.crt",
                "General_Cluster_ClientPrivateKey": "/etc/hyperledger/fabric/tls/server.key",
                "General_ListenAddress": "0.0.0.0",
                "General_ListenPort": 7050,
                "General_LocalMSPID": "OrdererMSP",
                "General_LocalMSPDir": "/etc/hyperledger/fabric/msp",
                "General_TLS_Enabled": True,
                "General_TLS_Certificate": "/etc/hyperledger/fabric/tls/server.crt",
                "General_TLS_PrivateKey": "/etc/hyperledger/fabric/tls/server.key",
                "General_TLS_RootCAs": "[/etc/hyperledger/fabric/tls/ca.crt]",
                "General_BootstrapMethod": "none",
                "Metrics_Provider": "prometheus",
                "Operations_ListenAddress": "{}:9443".format(orderer_full_name),
            }
        )

    @staticmethod
    def _generate_config(src: str, dst: str, **kwargs) -> None:
        with open(src, "r+") as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        for key, value in kwargs.items():
            sub_keys = key.split("_")
            cfg_iterator = cfg
            for sub_key in sub_keys[:-1]:
                cfg_iterator = cfg_iterator.setdefault(sub_key, {})
            cfg_iterator[sub_keys[-1]] = value
        with open(dst, "w+") as f:
            yaml.dump(cfg, f)

    def _generate_msp_tls_and_cfg(self, node_type: NodeType, organization_name: str, node_name: str) -> None:

    def _generate_msp(self, node_type: NodeType, organization_name: str, peer_name: str):
        directory_path = self._get_node_directory(node_type, organization_name, peer_name)
        msp_zip_path = os.path.join(directory_path, "msp.zip")
        self._zip_directory(
            os.path.join(directory_path, "msp"),
            msp_zip_path,
        )
        with open(msp_zip_path, "rb") as msp_input_stream:
            msp = base64.b64encode(msp_input_stream.read())
        return msp

    def _generate_tls(self, node_type: NodeType, organization_name: str, peer_name: str):
        directory_path = self._get_node_directory(node_type, organization_name, peer_name)
        tls_zip_path = os.path.join(directory_path, "tls.zip")
        self._zip_directory(
            os.path.join(directory_path, "tls"),
            tls_zip_path,
        )
        with open(tls_zip_path, "rb") as tls_input_stream:
            tls = base64.b64encode(tls_input_stream.read())
        return tls

    def _generate_peer_cfg(self, organization_name: str, peer_name: str):
        directory_path = self._get_peer_directory(organization_name, peer_name)
        cfg_zip_path = os.path.join(directory_path, "peer_config.zip")
        self._zip_directory(
            os.path.join(directory_path, "core.yaml"),
            cfg_zip_path
        )
        with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
            cfg = base64.b64encode(cfg_zip_input_stream.read())

    def _generate_orderer_cfg(self, organization_name: str, orderer_name: str):
        directory_path = self._get_orderer_directory(organization_name, orderer_name)
        cfg_zip_path = os.path.join(directory_path, "orderer_config.zip")
        self._zip_directory(
            os.path.join(directory_path, "orderer.yaml"),
            cfg_zip_path
        )
        with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
            cfg = base64.b64encode(cfg_zip_input_stream.read())

    def _generate_peer_msp_tls_and_cfg(self, organization_name: str, peer_name: str) -> None:
        directory_path = self._get_peer_directory(organization_name, peer_name)

        cfg_zip_path = os.path.join(directory_path, "peer_config.zip")
        self._zip_directory(
            os.path.join(directory_path, "core.yaml"),
            cfg_zip_path
        )
        with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
            cfg = base64.b64encode(cfg_zip_input_stream.read())

    def _get_peer_directory(self, organization_name: str, peer_name: str):
        return self._get_node_directory(NodeType.Peer, organization_name, peer_name)

    def _get_orderer_directory(self, organization_name: str, orderer_name: str):
        return self._get_node_directory(NodeType.Orderer, organization_name, orderer_name)

    @staticmethod
    def _get_node_directory(node_type: NodeType, organization_name: str, node_name: str):
        organization_domain = organization_name.split(".", 1)[1] \
            if node_type == NodeType.Orderer \
            else organization_name
        return ("{}/{}/crypto-config/{}Organizations/{}/{}s/{}.{}"
            .format(
                CELLO_HOME,
                organization_name,
                node_type.name.lower(),
                organization_domain,
                node_type.name.lower(),
                node_name,
                organization_domain,
            ))

    @staticmethod
    def _zip_directory(directory_path:str, output_file_path: str) -> None:
        root_path_inside_zip = "/{}".format(directory_path.rsplit("/", 1)[1])
        with ZipFile(output_file_path, "w") as zip_output_stream:
            for path, sub_directories, files in os.walk(directory_path):
                path_inside_zip = root_path_inside_zip +  path.replace(directory_path, "")
                for filename in files:
                    zip_output_stream.write(
                        str(os.path.join(path, filename)),
                        str(os.path.join(path_inside_zip, filename))
                    )
                for sud_directory in sub_directories:
                    zip_output_stream.write(
                        str(os.path.join(path, sud_directory)),
                        str(os.path.join(path_inside_zip, sud_directory))
                    )

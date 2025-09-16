import base64
import os
from typing import Optional, Dict, Any
from zipfile import ZipFile

import yaml
from requests import post
from rest_framework import serializers

from agent.enums import AgentType
from api.common.serializers import ListResponseSerializer
from api.config import CELLO_HOME
from api.lib.agent.docker import DockerAgent
from api.lib.pki import CryptoConfig, CryptoGen
from node.enums import NodeType, NodeStatus
from node.models import Node


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
            "cid",
        )


class NodeListSerializer(ListResponseSerializer):
    data = NodeResponseSerializer(many=True, help_text="Node list")


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

    def validate(self, data: Dict[str, Any]):
        if any(node.name == data["name"] for node in self.context["request"].user.organization.agent.nodes):
            raise serializers.ValidationError("Node Exists")
        return data

    def create(self, validated_data: Dict[str, Any]) -> Node:
        organization = self.context["request"].user.organization
        node_type = validated_data["type"]
        node_name = validated_data["name"]
        CryptoConfig(organization.name).update({"type": node_type, "Specs": [node_name]})
        CryptoGen(organization.name).extend()
        node_domain_name = self._get_node_domain_name(node_type, organization.name, node_name)
        self._generate_node_config(node_type, organization.name, node_domain_name)
        msp = self._get_msp(node_type, organization.name, node_domain_name)
        tls = self._get_tls(node_type, organization.name, node_domain_name)
        cfg = self._get_cfg(node_type, organization.name, node_domain_name)
        agent = organization.agent
        response = post(
            "{}/api/v1/nodes".format(agent.url),
            data={
                "msp": msp,
                "tls": tls,
                "peer_config_file": cfg,
                "orderer_config_file": cfg,
                "img": "hyperledger/fabric:2.5.10",
                "cmd": (
                    'bash /tmp/init.sh "peer node start"'
                    if node_type == NodeType.Peer
                    else 'bash /tmp/init.sh "orderer"'
                ),
                "name": node_domain_name,
                "type": node_type,
                "action": "create",
            })
        node = Node(
            name=node_name,
            type=node_type,
            agent=organization.agent,
            status=NodeStatus.Running.name if response.status_code == 200 else NodeStatus.Failed.name,
            config_file=cfg,
            msp=msp,
            tls=tls,
        )
        node.save()
        return node

    def _generate_node_config(self, node_type: NodeType, organization_name: str, node_domain_name: str) -> None:
        if node_type == NodeType.Peer:
            self._generate_peer_config(organization_name, node_domain_name)
        elif node_type == NodeType.Orderer:
            self._generate_orderer_config(organization_name, node_domain_name)
        # throw exception here
        return None

    def _generate_peer_config(self, organization_name: str, peer_domain_name: str) -> None:
        self._generate_config(
            "/opt/node/core.yaml.bak",
            os.path.join(
                self._get_peer_directory(organization_name, peer_domain_name),
                "core.yaml"),
            **{
                "peer_tls_enabled": True,
                "operations_listenAddress": "{}:9444".format(peer_domain_name),
                "peer_address": "{}:7051".format(peer_domain_name),
                "peer_gossip_bootstrap": "{}:7051".format(peer_domain_name),
                "peer_gossip_externalEndpoint": "{}:7051".format(peer_domain_name),
                "peer_id": peer_domain_name,
                "peer_localMspId": "{}MSP".format(organization_name.capitalize()),
                "peer_mspConfigPath": "/etc/hyperledger/fabric/msp",
                "peer_tls_cert_file": "/etc/hyperledger/fabric/tls/server.crt",
                "peer_tls_key_file": "/etc/hyperledger/fabric/tls/server.key",
                "peer_tls_rootcert_file": "/etc/hyperledger/fabric/tls/ca.crt",
                "vm_docker_hostConfig_NetworkMode": "cello_net",
                "vm_endpoint": "unix:///host/var/run/docker.sock"
            }
        )

    def _generate_orderer_config(self, organization_name: str, orderer_domain_name: str) -> None:
        self._generate_config(
            "/opt/node/orderer.yaml.bak",
            os.path.join(
                self._get_orderer_directory(organization_name, orderer_domain_name),
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
                "Operations_ListenAddress": "{}:9443".format(orderer_domain_name),
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

    def _get_msp(self, node_type: NodeType, organization_name: str, node_domain_name: str) -> bytes:
        directory_path = self._get_node_directory(node_type, organization_name, node_domain_name)
        msp_zip_path = os.path.join(directory_path, "msp.zip")
        self._zip_directory(
            os.path.join(directory_path, "msp"),
            msp_zip_path,
        )
        with open(msp_zip_path, "rb") as msp_input_stream:
            return base64.b64encode(msp_input_stream.read())

    def _get_tls(self, node_type: NodeType, organization_name: str, node_domain_name: str) -> bytes:
        directory_path = self._get_node_directory(node_type, organization_name, node_domain_name)
        tls_zip_path = os.path.join(directory_path, "tls.zip")
        self._zip_directory(
            os.path.join(directory_path, "tls"),
            tls_zip_path,
        )
        with open(tls_zip_path, "rb") as tls_input_stream:
            return base64.b64encode(tls_input_stream.read())

    def _get_cfg(self, node_type: NodeType, organization_name: str, node_domain_name: str) -> Optional[bytes]:
        if node_type == NodeType.Peer:
            return self._get_peer_cfg(organization_name, node_domain_name)
        elif node_type == NodeType.Orderer:
            return self._get_orderer_cfg(organization_name, node_domain_name)
        # throw exception here
        return None

    def _get_peer_cfg(self, organization_name: str, peer_domain_name: str):
        directory_path = self._get_peer_directory(organization_name, peer_domain_name)
        cfg_zip_path = os.path.join(directory_path, "peer_config.zip")
        self._zip_directory(
            os.path.join(directory_path, "core.yaml"),
            cfg_zip_path
        )
        with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
            return base64.b64encode(cfg_zip_input_stream.read())

    def _get_orderer_cfg(self, organization_name: str, orderer_domain_name: str):
        directory_path = self._get_orderer_directory(organization_name, orderer_domain_name)
        cfg_zip_path = os.path.join(directory_path, "orderer_config.zip")
        self._zip_directory(
            os.path.join(directory_path, "orderer.yaml"),
            cfg_zip_path
        )
        with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
            return base64.b64encode(cfg_zip_input_stream.read())

    def _get_peer_directory(self, organization_name: str, peer_domain_name: str):
        return self._get_node_directory(NodeType.Peer, organization_name, peer_domain_name)

    def _get_orderer_directory(self, organization_name: str, orderer_domain_name: str):
        return self._get_node_directory(NodeType.Orderer, organization_name, orderer_domain_name)

    @staticmethod
    def _get_node_directory(node_type: NodeType, organization_name: str, node_domain_name: str):
        return ("{}/{}/crypto-config/{}Organizations/{}/{}s/{}"
            .format(
                CELLO_HOME,
                organization_name,
                node_type.name.lower(),
                organization_name.split(".", 1)[1]
                    if node_type == NodeType.Orderer
                    else organization_name,
                node_type.name.lower(),
                node_domain_name,
            ))

    @staticmethod
    def _get_node_domain_name(node_type: NodeType, organization_name: str, node_name: str):
        return "{}.{}".format(
            node_name,
            organization_name
                if node_type == NodeType.Peer
                else organization_name.split(".", 1)[1])

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

    def _get_agent_interface(self, agent_type: AgentType) -> Optional[DockerAgent]:
        if agent_type == AgentType.Docker:
            return DockerAgent()
        return None

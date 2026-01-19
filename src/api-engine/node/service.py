import base64
import logging
import os
import sys
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from zipfile import ZipFile

import docker
import requests
import yaml
from docker.errors import DockerException

from api.lib.pki import CryptoConfig, CryptoGen
from api_engine.settings import CELLO_HOME, FABRIC_PEER_CFG, FABRIC_ORDERER_CFG, FABRIC_VERSION
from node.models import Node
from organization.models import Organization


def get_node(node_id: str) -> Optional[Node]:
    try:
        return Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return None


def create(organization: Organization, node_type: Node.Type, node_name: str) -> Node:
    agent_url = organization.agent_url
    requests.get(urljoin(agent_url, "health")).raise_for_status()
    requests.post(urljoin(agent_url, "nodes"), json=dict(name=org_name)).raise_for_status()

    node = Node(
        name=node_name,
        type=node_type,
        organization=organization,
    )
    node.save()
    return node


def get_domain_name(organization_name: str, node_type: Node.Type, node_name: str) -> str:
    return "{}.{}".format(
        node_name,
        organization_name
        if node_type == Node.Type.PEER
        else organization_name.split(".", 1)[1])


def _generate_node_config(organization_name: str, node_type: Node.Type, node_domain_name: str) -> None:
    if node_type == Node.Type.PEER:
        _generate_peer_config(organization_name, node_domain_name)
    elif node_type == Node.Type.ORDERER:
        _generate_orderer_config(organization_name, node_domain_name)
    # throw exception here
    return None


def _generate_peer_config(organization_name: str, peer_domain_name: str) -> None:
    _generate_config(
        FABRIC_PEER_CFG,
        os.path.join(
            get_peer_directory(organization_name, peer_domain_name),
            "core.yaml"),
        **{
            "peer_tls_enabled": True,
            "operations_listenAddress": "{}:9444".format(peer_domain_name),
            "peer_address": "{}:7051".format(peer_domain_name),
            "peer_gossip_bootstrap": "{}:7051".format(peer_domain_name),
            "peer_gossip_externalEndpoint": "{}:7051".format(peer_domain_name),
            "peer_id": peer_domain_name,
            "peer_localMspId": "{}MSP".format(organization_name.split(".", 1)[0].capitalize()),
            "peer_mspConfigPath": "/etc/hyperledger/fabric/msp",
            "peer_tls_cert_file": "/etc/hyperledger/fabric/tls/server.crt",
            "peer_tls_key_file": "/etc/hyperledger/fabric/tls/server.key",
            "peer_tls_rootcert_file": "/etc/hyperledger/fabric/tls/ca.crt",
            "vm_docker_hostConfig_NetworkMode": "cello_net",
            "vm_endpoint": "unix:///host/var/run/docker.sock"
        }
    )


def _generate_orderer_config(organization_name: str, orderer_domain_name: str) -> None:
    _generate_config(
        FABRIC_ORDERER_CFG,
        os.path.join(
            get_orderer_directory(organization_name, orderer_domain_name),
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


def _generate_config(src: str, dst: str, **kwargs) -> None:
    with open(src, "r+") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    if cfg is None:
        cfg = {}

    for key, value in kwargs.items():
        sub_keys = key.split("_")
        cfg_iterator = cfg
        for sub_key in sub_keys[:-1]:
            cfg_iterator = cfg_iterator.setdefault(sub_key, {})
        cfg_iterator[sub_keys[-1]] = value
    with open(dst, "w+") as f:
        yaml.dump(cfg, f)


def _get_msp(organization_name: str, node_type: Node.Type, node_domain_name: str) -> bytes:
    directory_path = _get_node_directory(organization_name, node_type, node_domain_name)
    msp_zip_path = os.path.join(directory_path, "msp.zip")
    _zip_directory(
        os.path.join(directory_path, "msp"),
        msp_zip_path,
    )
    with open(msp_zip_path, "rb") as msp_input_stream:
        return base64.b64encode(msp_input_stream.read())


def _get_tls(organization_name: str, node_type: Node.Type, node_domain_name: str) -> bytes:
    directory_path = _get_node_directory(organization_name, node_type, node_domain_name)
    tls_zip_path = os.path.join(directory_path, "tls.zip")
    _zip_directory(
        os.path.join(directory_path, "tls"),
        tls_zip_path,
    )
    with open(tls_zip_path, "rb") as tls_input_stream:
        return base64.b64encode(tls_input_stream.read())


def _get_cfg(organization_name: str, node_type: Node.Type, node_domain_name: str) -> Optional[bytes]:
    if node_type == Node.Type.PEER:
        return _get_peer_cfg(organization_name, node_domain_name)
    elif node_type == Node.Type.ORDERER:
        return _get_orderer_cfg(organization_name, node_domain_name)
    # throw exception here
    return None


def _get_peer_cfg(organization_name: str, peer_domain_name: str):
    directory_path = get_peer_directory(organization_name, peer_domain_name)
    cfg_zip_path = os.path.join(directory_path, "peer_config.zip")
    _zip_directory(
        os.path.join(directory_path, "core.yaml"),
        cfg_zip_path
    )
    with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
        return base64.b64encode(cfg_zip_input_stream.read())


def _get_orderer_cfg(organization_name: str, orderer_domain_name: str):
    directory_path = get_orderer_directory(organization_name, orderer_domain_name)
    cfg_zip_path = os.path.join(directory_path, "orderer_config.zip")
    _zip_directory(
        os.path.join(directory_path, "orderer.yaml"),
        cfg_zip_path
    )
    with open(cfg_zip_path, "rb") as cfg_zip_input_stream:
        return base64.b64encode(cfg_zip_input_stream.read())


def _zip_directory(directory_path: str, output_file_path: str) -> None:
    root_path_inside_zip = "/{}".format(directory_path.rsplit("/", 1)[1])
    with ZipFile(output_file_path, "w") as zip_output_stream:
        for path, sub_directories, files in os.walk(directory_path):
            path_inside_zip = root_path_inside_zip + path.replace(directory_path, "")
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


def get_peer_directory(organization_name: str, peer_domain_name: str):
    return _get_node_directory(organization_name, Node.Type.PEER, peer_domain_name)


def get_orderer_directory(organization_name: str, orderer_domain_name: str):
    return _get_node_directory(organization_name, Node.Type.ORDERER, orderer_domain_name)


def _get_node_directory(organization_name: str, node_type: Node.Type, node_domain_name: str) -> str:
    return "{}/{}s/{}".format(
        get_org_directory(organization_name, node_type),
        node_type.lower(),
        node_domain_name,
    )


def get_org_directory(organization_name: str, node_type: Node.Type) -> str:
    return "{}/{}/crypto-config/{}Organizations/{}".format(
        CELLO_HOME,
        organization_name,
        node_type.lower(),
        organization_name.split(".", 1)[1]
        if node_type == Node.Type.ORDERER
        else organization_name,
    )


def _get_node_env(node_type: Node.Type, node_domain_name: str, msp, tls, cfg) -> Optional[Dict[str, Any]]:
    if node_type == Node.Type.PEER:
        return _get_peer_env(node_domain_name, msp, tls, cfg)
    elif node_type == Node.Type.ORDERER:
        return _get_orderer_env(node_domain_name, msp, tls, cfg)
    # throw exception here
    return None


def _get_peer_env(peer_domain_name: str, msp, tls, cfg) -> Dict[str, Any]:
    return {
        "HLF_NODE_MSP": msp,
        "HLF_NODE_TLS": tls,
        "HLF_NODE_PEER_CONFIG": cfg,
        "HLF_NODE_ORDERER_CONFIG": cfg,
        "platform": "linux/amd64",
        "CORE_VM_ENDPOINT": "unix:///host/var/run/docker.sock",
        "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE": "cello-net",
        "FABRIC_LOGGING_SPEC": "INFO",
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_PROFILE_ENABLED": "false",
        "CORE_PEER_TLS_CERT_FILE": "/etc/hyperledger/fabric/tls/server.crt",
        "CORE_PEER_TLS_KEY_FILE": "/etc/hyperledger/fabric/tls/server.key",
        "CORE_PEER_TLS_ROOTCERT_FILE": "/etc/hyperledger/fabric/tls/ca.crt",
        "CORE_PEER_ID": peer_domain_name,
        "CORE_PEER_ADDRESS": peer_domain_name + ":7051",
        "CORE_PEER_LISTENADDRESS": "0.0.0.0:7051",
        "CORE_PEER_CHAINCODEADDRESS": peer_domain_name + ":7052",
        "CORE_PEER_CHAINCODELISTENADDRESS": "0.0.0.0:7052",
        "CORE_PEER_GOSSIP_BOOTSTRAP": peer_domain_name + ":7051",
        "CORE_PEER_GOSSIP_EXTERNALENDPOINT": peer_domain_name + ":7051",
        "CORE_PEER_LOCALMSPID": peer_domain_name.split(".")[1].capitalize() + "MSP",
        "CORE_PEER_MSPCONFIGPATH": "/etc/hyperledger/fabric/msp",
        "CORE_OPERATIONS_LISTENADDRESS": peer_domain_name + ":9444",
        "CORE_METRICS_PROVIDER": "prometheus",
    }


def _get_orderer_env(orderer_domain_name: str, msp, tls, cfg) -> Dict[str, Any]:
    return {
        "HLF_NODE_MSP": msp,
        "HLF_NODE_TLS": tls,
        "HLF_NODE_PEER_CONFIG": cfg,
        "HLF_NODE_ORDERER_CONFIG": cfg,
        "platform": "linux/amd64",
        "FABRIC_LOGGING_SPEC": "INFO",
        "ORDERER_GENERAL_LISTENADDRESS": "0.0.0.0",
        "ORDERER_GENERAL_LISTENPORT": "7050",
        "ORDERER_GENERAL_LOCALMSPID": "OrdererMSP",
        "ORDERER_GENERAL_LOCALMSPDIR": "/etc/hyperledger/fabric/msp",
        "ORDERER_GENERAL_TLS_ENABLED": "true",
        "ORDERER_GENERAL_TLS_PRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
        "ORDERER_GENERAL_TLS_CERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
        "ORDERER_GENERAL_TLS_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
        "ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
        "ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
        "ORDERER_GENERAL_CLUSTER_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
        "ORDERER_GENERAL_BOOTSTRAPMETHOD": "none",
        "ORDERER_CHANNELPARTICIPATION_ENABLED": "true",
        "ORDERER_ADMIN_TLS_ENABLED": "true",
        "ORDERER_ADMIN_TLS_CERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
        "ORDERER_ADMIN_TLS_PRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
        "ORDERER_ADMIN_TLS_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
        "ORDERER_ADMIN_TLS_CLIENTROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
        "ORDERER_ADMIN_LISTENADDRESS": "0.0.0.0:7053",
        "ORDERER_OPERATIONS_LISTENADDRESS": orderer_domain_name + ":9443",
        "ORDERER_METRICS_PROVIDER": "prometheus",
    }


def _get_node_cmd(node_type: Node.Type) -> Optional[str]:
    if node_type == Node.Type.PEER:
        return 'bash /tmp/init.sh "peer node start"'
    elif node_type == Node.Type.ORDERER:
        return 'bash /tmp/init.sh "orderer"'
    return None

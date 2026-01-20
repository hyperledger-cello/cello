import base64
import logging
import os
import subprocess
import zipfile
from io import BytesIO

import docker
import yaml

from hyperledger_fabric.settings import CRYPTO_CONFIG, FABRIC_TOOL, CELLO_HOME, FABRIC_VERSION
from node.enums import NodeType

LOG = logging.getLogger(__name__)

def create_node(node_type: str, name: str):
    _create_node(NodeType.PEER if node_type == NodeType.PEER.name else NodeType.ORDERER, name)

def _create_node(node_type: NodeType, name: str):
    # edit CRYPTO_CONFIG
    with open(
            CRYPTO_CONFIG,
            "r+",
            encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)
        organization = crypto_config["PeerOrgs" if node_type == NodeType.PEER else "OrdererOrgs"][0]
        specs = organization["Specs"]
        if name not in [spec["Hostname"] for spec in specs]:
            specs.append(dict(Hostname=name))
        yaml.dump(crypto_config, f)
    command = [
        os.path.join(FABRIC_TOOL, "cryptogen"),
        "extend",
        "--input={}".format(CELLO_HOME),
        "--config={}".format(CRYPTO_CONFIG),
    ]
    LOG.info(" ".join(command))
    LOG.info(subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
    ).stdout)

    with open(
            os.path.join(
                CELLO_HOME,
                "config",
                "core.yaml" if node_type == NodeType.PEER else "orderer.yaml"),
            "r") as f:
        cfg = yaml.safe_load(f)

    domain = name + "." + organization["Domain"]
    for key, value in ({
            "peer_tls_enabled": True,
            "operations_listenAddress": "0.0.0.0:9444",
            "peer_gossip_externalEndpoint": domain + ":7051",
            "peer_id": domain,
            "peer_localMspId": organization["Domain"].split(".", 1)[0].capitalize() + "MSP",
            "peer_mspConfigPath": "/etc/hyperledger/fabric/msp",
            "peer_tls_cert_file": "/etc/hyperledger/fabric/tls/server.crt",
            "peer_tls_key_file": "/etc/hyperledger/fabric/tls/server.key",
            "peer_tls_rootcert_file": "/etc/hyperledger/fabric/tls/ca.crt",
            "vm_docker_hostConfig_NetworkMode": "cello_net",
            "vm_endpoint": "unix:///host/var/run/docker.sock"
        } if node_type == NodeType.PEER else {
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
            "Operations_ListenAddress": "0.0.0.0:9443",
        }).items():
        sub_keys = key.split("_")
        cfg_iterator = cfg
        for sub_key in sub_keys[:-1]:
            cfg_iterator = cfg_iterator.setdefault(sub_key, {})
        cfg_iterator[sub_keys[-1]] = value

    node_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations" if node_type == NodeType.PEER else "ordererOrganizations",
        organization["Domain"],
        "peers" if node_type == NodeType.PEER else "orderers",
        domain
    )

    msp_buffer = BytesIO()
    with zipfile.ZipFile(msp_buffer, 'w') as z:
        folder_path = os.path.join(node_directory, "msp")
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                z.write(full_path, rel_path)

    tls_buffer = BytesIO()
    with zipfile.ZipFile(tls_buffer, 'w') as z:
        folder_path = os.path.join(node_directory, "tls")
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                z.write(full_path, rel_path)

    cfg_buffer = BytesIO()
    with zipfile.ZipFile(cfg_buffer, "w") as z:
        z.writestr("core.yaml" if node_type == NodeType.PEER else "orderer.yaml", yaml.dump(cfg))

    cfg = base64.b64encode(cfg_buffer.getvalue())
    docker.DockerClient("unix:///var/run/docker.sock").containers.run(
        "hyperledger/fabric:" + FABRIC_VERSION,
        "bash /tmp/init.sh " + '"peer node start"' if node_type == NodeType.PEER else '"orderer"',
        detach=True,
        tty=True,
        stdin_open=True,
        network="cello-net",
        name=name + "." + organization["Domain"],
        volumes=[
            "/var/run/docker.sock:/host/var/run/docker.sock"
        ],
        environment={
            "HLF_NODE_MSP": base64.b64encode(msp_buffer.getvalue()),
            "HLF_NODE_TLS": base64.b64encode(tls_buffer.getvalue()),
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
            "CORE_PEER_ID": domain,
            "CORE_PEER_ADDRESS": domain + ":7051",
            "CORE_PEER_LISTENADDRESS": "0.0.0.0:7051",
            "CORE_PEER_CHAINCODEADDRESS": domain + ":7052",
            "CORE_PEER_CHAINCODELISTENADDRESS": "0.0.0.0:7052",
            "CORE_PEER_GOSSIP_BOOTSTRAP": domain + ":7051",
            "CORE_PEER_GOSSIP_EXTERNALENDPOINT": domain + ":7051",
            "CORE_PEER_LOCALMSPID": organization["Domain"].split(".", 1)[0].capitalize() + "MSP",
            "CORE_PEER_MSPCONFIGPATH": "/etc/hyperledger/fabric/msp",
            "CORE_OPERATIONS_LISTENADDRESS": "0.0.0.0:9444",
            "CORE_METRICS_PROVIDER": "prometheus",
        } if node_type == NodeType.PEER else {
            "HLF_NODE_MSP": base64.b64encode(msp_buffer.getvalue()),
            "HLF_NODE_TLS": base64.b64encode(tls_buffer.getvalue()),
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
            "ORDERER_OPERATIONS_LISTENADDRESS": "0.0.0.0:9443",
            "ORDERER_METRICS_PROVIDER": "prometheus",
        },
    )

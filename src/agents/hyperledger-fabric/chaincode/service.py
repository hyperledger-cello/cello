import json
import logging
import os
import subprocess
import tarfile
from typing import List, Optional, Dict, Any
import yaml
from django.core.files.storage import FileSystemStorage
from hyperledger_fabric.settings import CELLO_HOME, CRYPTO_CONFIG, FABRIC_TOOL

LOG = logging.getLogger(__name__)


def get_metadata(file_path) -> Optional[Dict[str, Any]]:
    res = None
    with tarfile.open(file_path, mode='r:gz') as tar:
        for member in tar.getmembers():
            if member.name.endswith("metadata.json"):
                res = json.loads(
                    tar.extractfile(member)
                    .read()
                    .decode("utf-8")
                )
                break
    return res


def create_chaincode(
        name: str,
        version: str,
        sequence: int,
        channel_name: str,
        file_path: str,
        package_id: str,
        init_required: bool = False,
        signature_policy: str = None):
    install_chaincode(file_path)
    approve_chaincode(
        name,
        channel_name,
        version,
        package_id,
        sequence,
        init_required,
        signature_policy)


def install_chaincode(file_path: str):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    peer_organization_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations",
        crypto_config["PeerOrgs"][0]["Domain"]
    )
    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "lifecycle",
        "chaincode",
        "install",
        file_path,
    ]
    for peer in crypto_config["PeerOrgs"][0]["Specs"]:
        peer_domain_name = "{}.{}".format(peer["Hostname"], crypto_config["PeerOrgs"][0]["Domain"])
        peer_dir = os.path.join(
            peer_organization_directory, 
            "peers", 
            peer_domain_name
        )
        peer_env = {
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": crypto_config["PeerOrgs"][0]["Name"] + "MSP",
            "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(peer_dir, "tls", "ca.crt"),
            "CORE_PEER_MSPCONFIGPATH": os.path.join(
                peer_organization_directory, 
                "users", 
                "Admin@" + crypto_config["PeerOrgs"][0]["Domain"], 
                "msp"
            ),
            "CORE_PEER_ADDRESS": peer_domain_name + ":7051",
            "FABRIC_CFG_PATH": peer_dir,
        }
        LOG.info(peer_env)
        LOG.info(command)
        subprocess.run(
            command,
            env=peer_env,
            check=True)


def get_chaincode_package_id(file_path: str):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    peer_organization_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations",
        crypto_config["PeerOrgs"][0]["Domain"]
    )
    peer_name = crypto_config["PeerOrgs"][0]["Specs"][0]["Hostname"]
    peer_cmd = os.path.join(FABRIC_TOOL, "peer")
    peer_domain_name = "{}.{}".format(peer_name, crypto_config["PeerOrgs"][0]["Domain"])
    peer_dir = os.path.join(
        peer_organization_directory,
        "peers",
        peer_domain_name
    )
    peer_env = {
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": crypto_config["PeerOrgs"][0]["Name"] + "MSP",
        "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(peer_dir, "tls", "ca.crt"),
        "CORE_PEER_MSPCONFIGPATH": os.path.join(
            peer_organization_directory,
            "users",
            "Admin@" + crypto_config["PeerOrgs"][0]["Domain"],
            "msp"
        ),
        "CORE_PEER_ADDRESS": peer_domain_name + ":7051",
        "FABRIC_CFG_PATH": peer_dir,
    }
    command: List[str] = [
        peer_cmd,
        "lifecycle",
        "chaincode",
        "calculatepackageid",
        file_path
    ]
    LOG.info(peer_env)
    LOG.info(" ".join(command))
    return subprocess.run(
        command,
        env=peer_env,
        check=True,
        capture_output=True,
        text=True
    ).stdout.rstrip("\n")


def approve_chaincode(
        name: str,
        channel_name: str,
        version: str,
        package_id: str,
        sequence: int,
        init_required: bool = False,
        signature_policy: str = None):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    peer_organization_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations",
        crypto_config["PeerOrgs"][0]["Domain"]
    )
    peer_name = crypto_config["PeerOrgs"][0]["Specs"][0]["Hostname"]
    peer_cmd = os.path.join(FABRIC_TOOL, "peer")
    peer_domain_name = "{}.{}".format(peer_name, crypto_config["PeerOrgs"][0]["Domain"])
    peer_dir = os.path.join(
        peer_organization_directory, 
        "peers", 
        peer_domain_name
    )
    peer_env = {
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": crypto_config["PeerOrgs"][0]["Name"] + "MSP",
        "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(peer_dir, "tls", "ca.crt"),
        "CORE_PEER_MSPCONFIGPATH": os.path.join(
            peer_organization_directory, 
            "users", 
            "Admin@" + crypto_config["PeerOrgs"][0]["Domain"], 
            "msp"
        ),
        "CORE_PEER_ADDRESS": peer_domain_name + ":7051",
        "FABRIC_CFG_PATH": peer_dir,
    }

    orderer_domain_name = "{}.{}".format(
        crypto_config["OrdererOrgs"][0]["Specs"][0]["Hostname"], 
        crypto_config["OrdererOrgs"][0]["Domain"])
    command = [
        peer_cmd,
        "lifecycle",
        "chaincode",
        "approveformyorg",
        "-o",
        orderer_domain_name + ":7050",
        "--channelID",
        channel_name,
        "--name",
        name,
        "--version",
        version,
        "--package-id",
        package_id,
        "--sequence",
        str(sequence),
        "--tls",
        "--cafile",
        os.path.join(
            CELLO_HOME,
            "ordererOrganizations",
            crypto_config["OrdererOrgs"][0]["Domain"],
            "orderers",
            orderer_domain_name,
            "msp",
            "tlscacerts",
            "tlsca.{}-cert.pem".format(crypto_config["OrdererOrgs"][0]["Domain"])
        )
    ]
    if init_required:
        command.append("--init-required")
    if signature_policy and signature_policy.strip():
        command.extend(["--signature-policy", signature_policy])

    LOG.info(peer_env)
    LOG.info(" ".join(command))
    subprocess.run(
        command,
        env=peer_env,
        check=True,
    )


def commit_chaincode(
        name: str,
        channel_name: str,
        version: str,
        sequence: int):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    peer_organization_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations",
        crypto_config["PeerOrgs"][0]["Domain"]
    )
    peer_name = crypto_config["PeerOrgs"][0]["Specs"][0]["Hostname"]
    peer_cmd = os.path.join(FABRIC_TOOL, "peer")
    peer_domain_name = "{}.{}".format(peer_name, crypto_config["PeerOrgs"][0]["Domain"])
    peer_dir = os.path.join(
        peer_organization_directory,
        "peers",
        peer_domain_name
    )
    peer_env = {
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": crypto_config["PeerOrgs"][0]["Name"] + "MSP",
        "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(peer_dir, "tls", "ca.crt"),
        "CORE_PEER_MSPCONFIGPATH": os.path.join(
            peer_organization_directory,
            "users",
            "Admin@" + crypto_config["PeerOrgs"][0]["Domain"],
            "msp"
        ),
        "CORE_PEER_ADDRESS": peer_domain_name + ":7051",
        "FABRIC_CFG_PATH": peer_dir,
    }

    orderer_domain_name = "{}.{}".format(
        crypto_config["OrdererOrgs"][0]["Specs"][0]["Hostname"],
        crypto_config["OrdererOrgs"][0]["Domain"])
    command = [
        peer_cmd,
        "lifecycle",
        "chaincode",
        "commit",
        "-o",
        orderer_domain_name + ":7050",
        "--channelID",
        channel_name,
        "--name",
        name,
        "--version",
        version,
        "--sequence",
        str(sequence),
        "--tls",
        "--cafile",
        os.path.join(
            CELLO_HOME,
            "ordererOrganizations",
            crypto_config["OrdererOrgs"][0]["Domain"],
            "orderers",
            orderer_domain_name,
            "msp",
            "tlscacerts",
            "tlsca.{}-cert.pem".format(crypto_config["OrdererOrgs"][0]["Domain"])
        )
    ]
    LOG.info(peer_env)
    LOG.info(" ".join(command))
    subprocess.run(
        command,
        env=peer_env,
        check=True,
    )

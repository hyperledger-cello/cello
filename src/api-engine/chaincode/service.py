from enum import Enum, auto
import json
import logging
import os
import subprocess
import tarfile
from typing import Optional, List, Any, Dict

from django.db import transaction

from api_engine.settings import CELLO_HOME, FABRIC_TOOL
from chaincode.models import Chaincode
from channel.models import Channel
from node.models import Node
from node.service import get_domain_name, get_peer_directory, get_org_directory, get_orderer_directory
from organization.models import Organization
from user.models import UserProfile

LOG = logging.getLogger(__name__)

peer_command = os.path.join(FABRIC_TOOL, "peer")

def create_chaincode(
        name: str,
        version: str,
        sequence: int,
        package,
        channel: Channel,
        user: UserProfile,
        organization: Organization,
        peers: List[Node],
        description: str,
        init_required: bool = False,
        signature_policy: str = None) -> Chaincode:
    metadata = get_metadata(package)

    chaincode = Chaincode(
        name=name,
        version=version,
        sequence=sequence,
        label=metadata["label"],
        language=metadata["type"],
        package=package,
        init_required=init_required,
        signature_policy=signature_policy,
        channel=channel,
        creator=user,
        description=description,
    )
    chaincode.save()
    chaincode.peers.add(*peers)

    peer_root_certs: list[str] = []
    peer_addresses: list[str] = []
    peer_envs: list[map[str, str]] = []
    for peer in peers:
        peer_root_cert, peer_address, peer_env = get_peer_root_cert_and_address_and_envs(organization.name, peer.name)
        peer_root_certs.append(peer_root_cert)
        peer_addresses.append(peer_address)
        peer_envs.append(peer_env)

    set_chaincode_package_id(peer_envs[0], chaincode)
    install_chaincode_with_envs(peer_envs, chaincode)

    command[3] = "commit"
    # Remove package ID
    del command[14:16]
    for i in range(len(peers)):
        command.extend(["--peerAddresses", peer_addresses[i], "--tlsRootCertFiles", peer_root_certs[i]])

    LOG.info(" ".join(command))
    for peer_env in peer_envs:
        subprocess.run(
            command,
            env=peer_env,
            check=True)

    with transaction.atomic():
        chaincode.status = Chaincode.Status.COMMITTED
        chaincode.save()

    return chaincode

def get_metadata(file) -> Optional[Dict[str, Any]]:
    file.seek(0)
    res = None
    with tarfile.open(fileobj=file, mode='r:gz') as tar:
        for member in tar.getmembers():
            if member.name.endswith("metadata.json"):
                res = json.loads(
                    tar.extractfile(member)
                    .read()
                    .decode("utf-8")
                )
                break
    file.seek(0)
    return res

def install_chaincode(organization: Organization, chaincode: Chaincode):
    peer_envs: list[map[str, str]] = []
    for peer in chaincode.peers:
        peer_envs.append(get_peer_root_cert_and_address_and_envs(organization.name, peer.name)[2])

    if chaincode.package_id is None:
        set_chaincode_package_id(peer_envs[0], chaincode)

    install_chaincode_with_envs(peer_envs, chaincode)

def approve_chaincode(
        peer_envs: list[dict[str, str]],
        channel_name: str,
        organization: Organization, 
        chaincode: Chaincode):
    orderer_domain_name = get_domain_name(
        organization.name,
        Node.Type.ORDERER,
        Node.objects.filter(type=Node.Type.ORDERER, organization=organization).first().name
    )
    command = [
        peer_command,
        "lifecycle",
        "chaincode",
        "approveformyorg",
        "-o",
        "{}:7050".format(orderer_domain_name),
        "--ordererTLSHostnameOverride",
        orderer_domain_name,
        "--channelID",
        channel_name,
        "--name",
        chaincode.name,
        "--version",
        chaincode.version,
        "--package-id",
        chaincode.package_id,
        "--sequence",
        str(chaincode.sequence),
        "--tls",
        "--cafile",
        "{}/msp/tlscacerts/tlsca.{}-cert.pem".format(
            get_orderer_directory(organization.name, orderer_domain_name),
            organization.name.split(".", 1)[1],
        )
    ]
    if chaincode.init_required:
        command.append("--init-required")
    if chaincode.signature_policy and chaincode.signature_policy.strip():
        command.extend(["--signature-policy", chaincode.signature_policy])

    LOG.info(" ".join(command))
    for peer_env in peer_envs:
        subprocess.run(
            command,
            env=peer_env,
            check=True)

    with transaction.atomic():
        chaincode.status = Chaincode.Status.APPROVED
        chaincode.save()

def get_peer_root_cert_and_address_and_envs(organization_name: str, peer_name: str) -> tuple[str, str, map[str, str]]:
    peer_domain_name: str = get_domain_name(organization_name, Node.Type.PEER, peer_name)
    peer_dir: str = get_peer_directory(organization_name, peer_domain_name)
    peer_root_cert: str = os.path.join(peer_dir, "tls/ca.crt")
    peer_address: str = "{}:7051".format(peer_domain_name)
    return peer_root_cert, peer_address, {
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": "{}MSP".format(organization_name.split(".", 1)[0].capitalize()),
        "CORE_PEER_TLS_ROOTCERT_FILE": peer_root_cert,
        "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
            get_org_directory(organization_name, Node.Type.PEER),
            organization_name
        ),
        "CORE_PEER_ADDRESS": peer_address,
        "FABRIC_CFG_PATH": peer_dir,
    }

def set_chaincode_package_id(peer_env: dict[str, str], chaincode: Chaincode):
    command: list[str] = [
        peer_command,
        "lifecycle",
        "chaincode",
        "calculatepackageid",
        chaincode.package.path
    ]
    LOG.info(" ".join(command))
    with transaction.atomic():
        chaincode.package_id = subprocess.run(
            command,
            env=peer_env,
            check=True,
            capture_output=True,
            text=True
        ).stdout
        chaincode.save()

def install_chaincode_with_envs(peer_envs: list[dict[str, str]], chaincode: Chaincode):
    command = [
        peer_command,
        "lifecycle",
        "chaincode",
        "install",
        chaincode.package.path,
    ]
    LOG.info(" ".join(command))
    for peer_env in peer_envs:
        subprocess.run(
            command,
            env=peer_env,
            check=True)

    with transaction.atomic():
        chaincode.status = Chaincode.Status.INSTALLED
        chaincode.save()

class ChaincodeAction(Enum):
    SUBMIT = auto()
    EVALUATE = auto()

def send_chaincode_request(
        channel: Channel,
        organization: Organization,
        peer: Node,
        chaincode: Chaincode,
        action: ChaincodeAction,
        function: str,
        *args: str):
    peer_organization_name = organization.name.split(".", 1)[0].capitalize()
    peer_msp = "{}MSP".format(peer_organization_name)
    peer_domain_name = get_domain_name(organization.name, Node.Type.PEER, peer.name)
    peer_dir = get_peer_directory(organization.name, peer_domain_name)
    peer_root_cert = os.path.join(peer_dir, "tls/ca.crt")
    peer_address = "{}:7051".format(peer_domain_name)
    command = [
        "go", 
        "run",
        os.path.join(CELLO_HOME, "chaincode", "application-gateway", "main.go"),
        action.name,
        function,
        *args
    ]
    LOG.info(" ".join(command))
    subprocess.run(
        command,
        env={
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": peer_msp,
            "CORE_PEER_TLS_ROOTCERT_FILE": peer_root_cert,
            "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
                get_org_directory(organization.name, Node.Type.PEER),
                organization.name
            ),
            "CORE_PEER_ADDRESS": peer_address,
            "FABRIC_CFG_PATH": peer_dir,
            "CHANNEL_NAME": channel.name,
            "CHAINCODE_NAME": chaincode.name
        },
        check=True)

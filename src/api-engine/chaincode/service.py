from enum import Enum, auto
import json
import logging
import os
import subprocess
import tarfile
from typing import Optional, List, Any, Dict, Tuple

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


def get_chaincode(id: str) -> Optional[Chaincode]:
    return Chaincode.objects.get(id=id)


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
    chaincode.peers.add(*peers)

    peer_envs = get_peers_root_certs_and_addresses_and_envs(
        organization.name,
        peers
    )[2]

    _set_chaincode_package_id(peer_envs[0], chaincode)
    _install_chaincode_with_envs(peer_envs, chaincode)
    _approve_chaincode_with_envs(peer_envs[0], organization, chaincode)
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


def install_chaincode(organization: Organization, chaincode: Chaincode) -> None:
    peer_envs: List[Dict[str, str]] = get_peers_root_certs_and_addresses_and_envs(
        organization.name,
        chaincode.peers
    )[2]

    _install_chaincode_with_envs(peer_envs, chaincode)


def _set_chaincode_package_id(peer_env: Dict[str, str], chaincode: Chaincode) -> None:
    command: List[str] = [
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


def _install_chaincode_with_envs(peer_envs: List[Dict[str, str]], chaincode: Chaincode) -> None:
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


def approve_chaincode(
        organization: Organization,
        chaincode: Chaincode) -> None:
    _approve_chaincode_with_envs(
        get_peers_root_certs_and_addresses_and_envs(
            organization.name,
            [chaincode.peers[0]]  # type: ignore
        )[2][0],
        organization,
        chaincode
    )


def _approve_chaincode_with_envs(
        peer_env: Dict[str, str],
        organization: Organization,
        chaincode: Chaincode) -> None:
    # Chaincode is approved at the organization level,
    # so the command only needs to target one peer.
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
        chaincode.channel.name,
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
    subprocess.run(
        command,
        env=peer_env,
        check=True)


def commit_chaincode(
        organization: Organization,
        chaincode: Chaincode) -> None:
    peer_root_certs, peer_addresses, peer_envs = get_peers_root_certs_and_addresses_and_envs(
        organization.name,
        chaincode.peers
    )
    orderer_domain_name = get_domain_name(
        organization.name,
        Node.Type.ORDERER,
        Node.objects.filter(type=Node.Type.ORDERER, organization=organization).first().name
    )
    command = [
        peer_command,
        "lifecycle",
        "chaincode",
        "commit",
        "-o",
        "{}:7050".format(orderer_domain_name),
        "--ordererTLSHostnameOverride",
        orderer_domain_name,
        "--channelID",
        chaincode.channel.name,
        "--name",
        chaincode.name,
        "--version",
        chaincode.version,
        "--sequence",
        str(chaincode.sequence),
        "--tls",
        "--cafile",
        "{}/msp/tlscacerts/tlsca.{}-cert.pem".format(
            get_orderer_directory(organization.name, orderer_domain_name),
            organization.name.split(".", 1)[1],
        )
    ]
    for i in range(len(chaincode.peers)):
        command.extend(["--peerAddresses", peer_addresses[i], "--tlsRootCertFiles", peer_root_certs[i]])

    LOG.info(" ".join(command))
    subprocess.run(
        command,
        env=peer_envs[0],
        check=True)


class ChaincodeAction(Enum):
    SUBMIT = auto()
    EVALUATE = auto()


def send_chaincode_request(
        organization: Organization,
        chaincode: Chaincode,
        action: ChaincodeAction,
        function: str,
        *args: str):
    # Pick any organization peer
    peer_env: Dict[str, str] = get_peers_root_certs_and_addresses_and_envs(
        organization.name,
        [chaincode.peers.filter(organization=organization)[0]]  # type: ignore
    )[2][0]
    command = [
        "go",
        "run",
        os.path.join(CELLO_HOME, "chaincode", "application-gateway", "main.go"),
        action.name,
        function,
        *args
    ]
    LOG.info(" ".join(command))
    response: str = subprocess.run(
        command,
        env={
            **peer_env,
            "CHANNEL_NAME": chaincode.channel.name,
            "CHAINCODE_NAME": chaincode.name
        },
        check=True,
        capture_output=True,
        text=True).stdout
    LOG.info(response)


def get_peers_root_certs_and_addresses_and_envs(
        organization_name: str,
        peers: List[Node]) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
    peer_root_certs: List[str] = []
    peer_addresses: List[str] = []
    peer_envs: List[Dict[str, str]] = []
    for peer_name in [peer.name for peer in peers]:
        peer_domain_name: str = get_domain_name(organization_name, Node.Type.PEER, peer_name)
        peer_dir: str = get_peer_directory(organization_name, peer_domain_name)
        peer_root_cert: str = os.path.join(peer_dir, "tls/ca.crt")
        peer_address: str = "{}:7051".format(peer_domain_name)
        peer_root_certs.append(peer_root_cert)
        peer_addresses.append(peer_address)
        peer_envs.append({
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": "{}MSP".format(organization_name.split(".", 1)[0].capitalize()),
            "CORE_PEER_TLS_ROOTCERT_FILE": peer_root_cert,
            "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
                get_org_directory(organization_name, Node.Type.PEER),
                organization_name
            ),
            "CORE_PEER_ADDRESS": peer_address,
            "FABRIC_CFG_PATH": peer_dir,
        })
    return peer_root_certs, peer_addresses, peer_envs

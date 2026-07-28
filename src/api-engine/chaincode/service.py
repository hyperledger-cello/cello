from enum import Enum, auto
import json
import logging
import os
import subprocess
import tarfile
import threading
from typing import Optional, List, Any, Dict, Tuple
from common.utils import safe_urljoin

import requests
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


def get_chaincode(pk: str) -> Optional[Chaincode]:
    return Chaincode.objects.get(id=pk)


def get_chaincode_status(organization: Organization, chaincode: Chaincode) -> str:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    response = requests.get(
        safe_urljoin(agent_url, "chaincodes/status"),
        params=dict(
            name=chaincode.name,
            package_id=chaincode.package_id,
            sequence=chaincode.sequence,
            channel=chaincode.channel.name
        )
    )
    response.raise_for_status()
    return response.json()["status"]


def get_chaincode_commit_readiness(organization: Organization, chaincode: Chaincode) -> str:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    response = requests.get(
        safe_urljoin(agent_url, "chaincodes/commit/readiness"),
        params=dict(
            name=chaincode.name,
            version=chaincode.version,
            sequence=chaincode.sequence,
            channel=chaincode.channel.name,
            init_required=(chaincode.init_required is not None and chaincode.init_required),
        )
    )
    response.raise_for_status()
    return response.json()["approvals"]


def create_chaincode(
        name: str,
        version: str,
        sequence: int,
        package,
        channel: Channel,
        user: UserProfile,
        organization: Organization,
        description: str = None,
        init_required: bool = False,
        signature_policy: str = None) -> Chaincode:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    response = requests.post(
        safe_urljoin(agent_url, "chaincodes"),
        data=dict(
            name=name,
            version=version,
            sequence=sequence,
            channel_name=channel.name,
            init_required=init_required,
            signature_policy=signature_policy
        ),
        files=dict(
            file=package
        )
    )
    response.raise_for_status()
    response_json = response.json()

    chaincode = Chaincode(
        package_id=response_json["package_id"],
        name=name,
        version=version,
        sequence=sequence,
        label=response_json["label"],
        language=response_json["language"],
        package=package,
        init_required=init_required,
        signature_policy=signature_policy,
        channel=channel,
        creator=user,
        description=description,
    )
    chaincode.save()
    return chaincode


def metadata_exists(file) -> bool:
    file.seek(0)
    res = False
    with tarfile.open(fileobj=file, mode='r:gz') as tar:
        for member in tar.getmembers():
            if member.name.endswith("metadata.json"):
                res = True
                break
    file.seek(0)
    return res


def install_chaincode(organization: Organization, chaincode: Chaincode) -> None:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.put(
        safe_urljoin(agent_url, "chaincodes/install"),
        data=dict(
            name=chaincode.name,
            version=chaincode.version,
            sequence=chaincode.sequence,
            channel_name=chaincode.channel.name
        ),
        files=dict(
            file=chaincode.package
        )
    ).raise_for_status()


def approve_chaincode(
        organization: Organization,
        chaincode: Chaincode) -> None:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.put(
        safe_urljoin(agent_url, "chaincodes/approve"),
        json=dict(
            name=chaincode.name,
            version=chaincode.version,
            sequence=chaincode.sequence,
            package_id=chaincode.package_id,
            channel_name=chaincode.channel.name,
            init_required=chaincode.init_required,
            signature_policy=chaincode.signature_policy
        )
    ).raise_for_status()


def commit_chaincode(
        organization: Organization,
        chaincode: Chaincode) -> None:
    agent_url = organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.put(
        safe_urljoin(agent_url, "chaincodes/commit"),
        json=dict(
            name=chaincode.name,
            version=chaincode.version,
            sequence=chaincode.sequence,
            channel_name=chaincode.channel.name
        )
    ).raise_for_status()


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
        [chaincode.peers.filter(organization=organization).first()]
    )[2][0]
    go = subprocess.run(
        ["which", "go"],
        check=True,
        capture_output=True,
        text=True).stdout.rstrip('\n')
    try:
        command = [
            go,
            "run",
            ".",
            action.name,
            function,
            *args
        ]
        LOG.info(" ".join(command))
        LOG.info(subprocess.run(
            command,
            env={
                **peer_env,
                "CHANNEL_NAME": chaincode.channel.name,
                "CHAINCODE_NAME": chaincode.name,
                "GOPATH": subprocess.run(
                    [go, "env", "GOPATH"],
                    check=True,
                    capture_output=True,
                    text=True).stdout.rstrip('\n'),
                "GOCACHE": subprocess.run(
                    [go, "env", "GOCACHE"],
                    check=True,
                    capture_output=True,
                    text=True).stdout.rstrip('\n')
            },
            cwd=os.path.join(CELLO_HOME, "application-gateway"),
            check=True,
            capture_output=True,
            text=True).stdout)
    except subprocess.CalledProcessError as e:
        LOG.error(e.stderr)


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

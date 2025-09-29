import json
import logging
import os
import subprocess
import time
from copy import deepcopy
from typing import List

import yaml

from api.exceptions import NoResource
from api_engine.settings import CELLO_HOME, FABRIC_TOOL
from channel.models import Channel
from node.models import Node
from node.service import get_org_directory, get_domain_name, get_orderer_directory, get_peer_directory
from organization.models import Organization

LOG = logging.getLogger(__name__)

def create(
        channel_organization: Organization,
        channel_name: str,
        channel_peer_ids: List[str],
        channel_orderer_ids: List[str]) -> Channel:
    channel_peers = list(Node.objects.filter(id__in=channel_peer_ids))
    channel_orderers = list(Node.objects.filter(id__in=channel_orderer_ids))
    validate_nodes(channel_peers + channel_orderers)

    orderer_msp = "OrdererMSP"
    orderer_domain_names = [get_domain_name(
            channel_organization.name,
            Node.Type.ORDERER,
            orderer.name) for orderer in channel_orderers]
    orderer_addresses = ["{}:7050".format(orderer_domain_name) for orderer_domain_name in orderer_domain_names]
    consenters = [{
        "Host": orderer_domain_name,
        "Port": 7050,
        "ClientTLSCert": "{}/tls/server.crt".format(get_orderer_directory(
            channel_organization.name,
            orderer_domain_name)),
        "ServerTLSCert": "{}/tls/server.crt".format(get_orderer_directory(
            channel_organization.name,
            orderer_domain_name)),
    } for orderer_domain_name in orderer_domain_names]
    orderer_organization = {
        "Name": "Orderer",
        "ID": orderer_msp,
        "MSPDir": "{}/msp".format(get_org_directory(channel_organization.name, Node.Type.ORDERER)),
        "Policies": {
            "Readers": {
                "Type": "Signature",
                "Rule": "OR('{}.member')".format(orderer_msp),
            },
            "Writers": {
                "Type": "Signature",
                "Rule": "OR('{}.member')".format(orderer_msp),
            },
            "Admins": {
                "Type": "Signature",
                "Rule": "OR('{}.admin')".format(orderer_msp),
            },
        },
        "OrdererEndpoints": orderer_addresses,
    }

    peer_organization_name = channel_organization.name.split(".", 1)[0].capitalize()
    peer_msp = "{}MSP".format(peer_organization_name)
    peer_organization = {
        "Name": peer_organization_name,
        "ID": peer_msp,
        "MSPDir": "{}/msp".format(get_org_directory(channel_organization.name, Node.Type.PEER)),
        "Policies": {
            "Readers": {
                "Type": "Signature",
                "Rule": "OR('{}.admin', '{}.peer', '{}.client')".format(peer_msp, peer_msp, peer_msp),
            },
            "Writers": {
                "Type": "Signature",
                "Rule": "OR('{}.admin', '{}.client')".format(peer_msp, peer_msp),
            },
            "Admins": {
                "Type": "Signature",
                "Rule": "OR('{}.admin')".format(peer_msp),
            },
            "Endorsement": {
                "Type": "Signature",
                "Rule": "OR('{}.peer')".format(peer_msp),
            }
        }
    }

    with open(os.path.join(CELLO_HOME, "config", "configtx.yaml"), "r", encoding="utf-8") as f:
        template = yaml.load(f, Loader=yaml.FullLoader)

    application = deepcopy(template["Application"])
    application["Capabilities"] = template["Capabilities"]["Application"]

    orderer = deepcopy(template["Orderer"])
    orderer["Addresses"] = orderer_addresses
    orderer["Capabilities"] = template["Capabilities"]["Orderer"]
    orderer["OrdererType"] = "etcdraft"
    orderer["EtcdRaft"]["Consenters"] = consenters

    channel = deepcopy(template["Channel"])
    channel["Capabilities"] = template["Capabilities"]["Channel"]

    profiles = {channel_name: deepcopy(channel)}
    profiles[channel_name]["Orderer"] = deepcopy(orderer)
    profiles[channel_name]["Orderer"]["Capabilities"] = template["Capabilities"]["Orderer"]
    profiles[channel_name]["Orderer"]["Organizations"] = orderer_organization
    profiles[channel_name]["Application"] = deepcopy(application)
    profiles[channel_name]["Application"]["Capabilities"] = template["Capabilities"]["Application"]
    profiles[channel_name]["Application"]["Organizations"] = peer_organization

    channel_dir = os.path.join(CELLO_HOME, channel_name)
    os.makedirs(channel_dir, exist_ok=True)
    with open(os.path.join(channel_dir, "configtx.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "Organizations": [orderer_organization, peer_organization],
                "Capabilities": {
                    "Channel": template["Capabilities"]["Channel"],
                    "Orderer": template["Capabilities"]["Orderer"],
                    "Application": template["Capabilities"]["Application"],
                },
                "Application": application,
                "Orderer": orderer,
                "Channel": channel,
                "Profiles": profiles,
            },
            f,
            sort_keys=False)

    command = [
        os.path.join(FABRIC_TOOL, "configtxgen"),
        "-configPath",
        channel_dir,
        "-profile",
        channel_name,
        "-outputBlock",
        os.path.join(channel_dir, "genesis.block"),
        "-channelID",
        channel_name,
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    orderer_domain_name = orderer_domain_names[0]
    orderer_dir = get_orderer_directory(channel_organization.name, orderer_domain_name)
    command = [
        os.path.join(FABRIC_TOOL, "osnadmin"),
        "channel",
        "join",
        "--channelID",
        channel_name,
        "--config-block",
        os.path.join(channel_dir, "genesis.block"),
        "-o",
        "{}:7053".format(orderer_domain_name),
        "--ca-file",
        "{}/msp/tlscacerts/tlsca.{}-cert.pem".format(
            orderer_dir,
            channel_organization.name.split(".", 1)[1],
        ),
        "--client-cert",
        "{}/tls/server.crt".format(orderer_dir),
        "--client-key",
        "{}/tls/server.key".format(orderer_dir),
    ]
    LOG.info(" ".join(command))
    subprocess.run(
        command,
        check=True)

    peer_domain_names = [
        get_domain_name(channel_organization.name, Node.Type.PEER, peer.name) for peer in channel_peers
    ]
    for peer_domain_name in peer_domain_names:
        command = [
            os.path.join(FABRIC_TOOL, "peer"),
            "channel",
            "join",
            "-b",
            os.path.join(channel_dir, "genesis.block"),
        ]
        LOG.info(" ".join(command))
        peer_dir = get_peer_directory(channel_organization.name, peer_domain_name)
        subprocess.run(
            command,
            env={
                "CORE_PEER_TLS_ENABLED": "true",
                "CORE_PEER_LOCALMSPID": peer_msp,
                "CORE_PEER_TLS_ROOTCERT_FILE": "{}/tls/ca.crt".format(peer_dir),
                "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
                    get_org_directory(channel_organization.name, Node.Type.PEER),
                    channel_organization.name
                ),
                "CORE_PEER_ADDRESS": "{}:7051".format(peer_domain_name),
                "FABRIC_CFG_PATH": peer_dir,
            },
            check=True)

    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "fetch",
        "config",
        os.path.join(channel_dir, "config_block.pb"),
        "-o",
        orderer_addresses[0],
        "--ordererTLSHostnameOverride",
        orderer_domain_name,
        "-c",
        channel_name,
        "--tls",
        "--cafile",
        "{}/msp/tlscacerts/tlsca.{}-cert.pem".format(
            orderer_dir,
            channel_organization.name.split(".", 1)[1],
        )
    ]
    LOG.info(" ".join(command))
    anchor_peer_domain_name = peer_domain_names[0]
    anchor_peer_dir = get_peer_directory(channel_organization.name, anchor_peer_domain_name)
    time.sleep(5)
    subprocess.run(
        command,
        env={
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": peer_msp,
            "CORE_PEER_TLS_ROOTCERT_FILE": "{}/tls/ca.crt".format(anchor_peer_dir),
            "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
                get_org_directory(channel_organization.name, Node.Type.PEER),
                channel_organization.name
            ),
            "CORE_PEER_ADDRESS": "{}:7051".format(
                anchor_peer_domain_name
            ),
            "FABRIC_CFG_PATH": anchor_peer_dir,
        },
        check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_decode",
        "--input={}".format(os.path.join(channel_dir, "config_block.pb")),
        "--type=common.Block",
        "--output={}".format(os.path.join(channel_dir, "config_block.json")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    with open(os.path.join(channel_dir, "config_block.json"), "r", encoding="utf-8") as f:
        config_block = json.load(f)

    with open(os.path.join(channel_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_block["data"]["data"][0]["payload"]["data"]["config"], f, sort_keys=False, indent=4)

    with open(os.path.join(channel_dir, "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    config["channel_group"]["groups"]["Application"]["groups"][peer_organization_name]["values"].update({
        "AnchorPeers": {
            "mod_policy": "Admins",
            "value": {
                "anchor_peers": [
                    {"host": "{}:7051".format(anchor_peer_domain_name)}
                ]
            },
            "version": 0,
        }
    })

    with open(os.path.join(channel_dir, "modified_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, sort_keys=False, indent=4)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_dir, "config.json")),
        "--type=common.Config",
        "--output={}".format(os.path.join(channel_dir, "config.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_dir, "modified_config.json")),
        "--type=common.Config",
        "--output={}".format(os.path.join(channel_dir, "modified_config.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "compute_update",
        "--original={}".format(os.path.join(channel_dir, "config.pb")),
        "--updated={}".format(os.path.join(channel_dir, "modified_config.pb")),
        "--channel_id={}".format(channel_name),
        "--output={}".format(os.path.join(channel_dir, "config_update.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_decode",
        "--input={}".format(os.path.join(channel_dir, "config_update.pb")),
        "--type=common.ConfigUpdate",
        "--output={}".format(os.path.join(channel_dir, "config_update.json")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    with open(os.path.join(channel_dir, "config_update.json"), "r", encoding="utf-8") as f:
        config_update = json.load(f)

    with open(os.path.join(channel_dir, "config_update_in_envelope.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "payload": {
                    "header": {
                        "channel_header": {"channel_id": channel_name, "type": 2}
                    },
                    "data": {"config_update": config_update},
                }
            },
            f,
            sort_keys = False,
            indent = 4
        )

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_dir, "config_update_in_envelope.json")),
        "--type=common.Envelope",
        "--output={}".format(os.path.join(channel_dir, "config_update_in_envelope.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "update",
        "-f",
        os.path.join(channel_dir, "config_update_in_envelope.pb"),
        "-c",
        channel_name,
        "-o",
        orderer_addresses[0],
        "--ordererTLSHostnameOverride",
        orderer_domain_name,
        "--tls",
        "--cafile",
        "{}/msp/tlscacerts/tlsca.{}-cert.pem".format(
            orderer_dir,
            channel_organization.name.split(".", 1)[1],
        )
    ]
    LOG.info(" ".join(command))
    subprocess.run(
        command,
        env={
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": peer_msp,
            "CORE_PEER_TLS_ROOTCERT_FILE": "{}/tls/ca.crt".format(anchor_peer_dir),
            "CORE_PEER_MSPCONFIGPATH": "{}/users/Admin@{}/msp".format(
                get_org_directory(channel_organization.name, Node.Type.PEER),
                channel_organization.name
            ),
            "CORE_PEER_ADDRESS": "{}:7051".format(
                anchor_peer_domain_name
            ),
            "FABRIC_CFG_PATH": anchor_peer_dir,
        },
        check=True)

    res = Channel.objects.create(name=channel_name)
    res.organizations.add(channel_organization)
    res.orderers.add(channel_orderers[0])
    return res

def validate_nodes(nodes: List[Node]):
    for node in nodes:
        if node.status != Node.Status.RUNNING:
            raise NoResource("Node {} is not running".format(node.name))

from copy import deepcopy
import json
import logging
import os
import subprocess
import time

import yaml

from hyperledger_fabric.settings import CELLO_HOME, CRYPTO_CONFIG, FABRIC_TOOL

LOG = logging.getLogger(__name__)

def create_channel(channel_name: str, orderer_names: list[str], peer_names: list[str]):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    orderer_hosts = ["{}.{}".format(orderer_name, crypto_config["OrdererOrgs"][0]["Domain"]) for orderer_name in orderer_names]
    orderer_addresses = [orderer_host + ":7050" for orderer_host in orderer_hosts]
    orderer_organization_directory = os.path.join(
        CELLO_HOME,
        "ordererOrganizations",
        crypto_config["OrdererOrgs"][0]["Domain"]
    )
    orderer_organizations = {
        "Name": "Orderer",
        "ID": "OrdererMSP",
        "MSPDir": os.path.join(orderer_organization_directory, "msp"),
        "Policies": {
            "Readers": {
                "Type": "Signature",
                "Rule": "OR('OrdererMSP.member')",
            },
            "Writers": {
                "Type": "Signature",
                "Rule": "OR('OrdererMSP.member')",
            },
            "Admins": {
                "Type": "Signature",
                "Rule": "OR('OrdererMSP.admin')",
            },
        },
        "OrdererEndpoints": orderer_addresses,
    }

    peer_organization_directory = os.path.join(
        CELLO_HOME,
        "peerOrganizations",
        crypto_config["PeerOrgs"][0]["Domain"]
    )
    peer_organizations = {
        "Name": crypto_config["PeerOrgs"][0]["Name"],
        "ID": crypto_config["PeerOrgs"][0]["Name"] + "MSP",
        "MSPDir": os.path.join(peer_organization_directory, "msp"),
        "Policies": {
            "Readers": {
                "Type": "Signature",
                "Rule": "OR('{}MSP.admin', '{}MSP.peer', '{}MSP.client')".format(
                    crypto_config["PeerOrgs"][0]["Name"], 
                    crypto_config["PeerOrgs"][0]["Name"], 
                    crypto_config["PeerOrgs"][0]["Name"]
                ),
            },
            "Writers": {
                "Type": "Signature",
                "Rule": "OR('{}MSP.admin', '{}MSP.client')".format(
                    crypto_config["PeerOrgs"][0]["Name"], 
                    crypto_config["PeerOrgs"][0]["Name"]
                ),
            },
            "Admins": {
                "Type": "Signature",
                "Rule": "OR('{}MSP.admin')".format(crypto_config["PeerOrgs"][0]["Name"]),
            },
            "Endorsement": {
                "Type": "Signature",
                "Rule": "OR('{}MSP.peer')".format(crypto_config["PeerOrgs"][0]["Name"]),
            }
        }
    }

    orderer_directories = [os.path.join(
        orderer_organization_directory, 
        "orderers", 
        orderer_host) for orderer_host in orderer_hosts]

    with open(os.path.join(CELLO_HOME, "config", "configtx.yaml"), "r", encoding="utf-8") as f:
        configtx = yaml.safe_load(f)

    application = deepcopy(configtx["Application"])
    application["Capabilities"] = configtx["Capabilities"]["Application"]

    orderer = deepcopy(configtx["Orderer"])
    orderer["Addresses"] = orderer_addresses
    orderer["Capabilities"] = configtx["Capabilities"]["Orderer"]
    orderer["OrdererType"] = "etcdraft"
    orderer["EtcdRaft"]["Consenters"] = [{
        "Host": orderer_host,
        "Port": 7050,
        "ClientTLSCert": os.path.join(orderer_directory, "tls", "server.crt"),
        "ServerTLSCert": os.path.join(orderer_directory, "tls", "server.crt"),
    } for orderer_host, orderer_directory in zip(orderer_hosts, orderer_directories)]

    channel = deepcopy(configtx["Channel"])
    channel["Capabilities"] = configtx["Capabilities"]["Channel"]

    profiles = {channel_name: deepcopy(channel)}
    profiles[channel_name]["Orderer"] = deepcopy(orderer)
    profiles[channel_name]["Orderer"]["Capabilities"] = configtx["Capabilities"]["Orderer"]
    profiles[channel_name]["Orderer"]["Organizations"] = orderer_organizations
    profiles[channel_name]["Application"] = deepcopy(application)
    profiles[channel_name]["Application"]["Capabilities"] = configtx["Capabilities"]["Application"]
    profiles[channel_name]["Application"]["Organizations"] = peer_organizations

    channel_directory = os.path.join(CELLO_HOME, channel_name)
    os.makedirs(channel_directory, exist_ok=True)
    with open(os.path.join(channel_directory, "configtx.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "Organizations": [
                    orderer_organizations, 
                    peer_organizations
                ],
                "Capabilities": {
                    "Channel": configtx["Capabilities"]["Channel"],
                    "Orderer": configtx["Capabilities"]["Orderer"],
                    "Application": configtx["Capabilities"]["Application"],
                },
                "Application": application,
                "Orderer": orderer,
                "Channel": channel,
                "Profiles": profiles,
            },
            f
        )

    command = [
        os.path.join(FABRIC_TOOL, "configtxgen"),
        "-configPath",
        channel_directory,
        "-profile",
        channel_name,
        "-outputBlock",
        os.path.join(channel_directory, "genesis.block"),
        "-channelID",
        channel_name,
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    for orderer_host, orderer_directory in zip(orderer_hosts, orderer_directories):
        command = [
            os.path.join(FABRIC_TOOL, "osnadmin"),
            "channel",
            "join",
            "--channelID",
            channel_name,
            "--config-block",
            os.path.join(channel_directory, "genesis.block"),
            "-o",
            orderer_host + ":7053",
            "--ca-file",
            os.path.join(orderer_directory, "msp", "tlscacerts", "tlsca.{}-cert.pem".format(crypto_config["OrdererOrgs"][0]["Domain"])),
            "--client-cert",
            os.path.join(orderer_directory, "tls", "server.crt"),
            "--client-key",
            os.path.join(orderer_directory, "tls", "server.key"),
        ]
        LOG.info(" ".join(command))
        subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "join",
        "-b",
        os.path.join(channel_directory, "genesis.block"),
    ]
    for peer_name in peer_names:
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
        LOG.info(peer_env)
        LOG.info(" ".join(command))
        subprocess.run(
            command,
            env=peer_env,
            check=True)

    time.sleep(5)
    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "fetch",
        "config",
        os.path.join(channel_directory, "config_block.pb"),
        "-o",
        orderer_addresses[0],
        "--ordererTLSHostnameOverride",
        orderer_hosts[0],
        "-c",
        channel_name,
        "--tls",
        "--cafile",
        os.path.join(
            orderer_directories[0], 
            "msp", 
            "tlscacerts", 
            "tlsca.{}-cert.pem".format(crypto_config["OrdererOrgs"][0]["Domain"])
        ),
    ]
    LOG.info(" ".join(command))
    LOG.info(peer_env)
    subprocess.run(
        command,
        env=peer_env,
        check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_decode",
        "--input={}".format(os.path.join(channel_directory, "config_block.pb")),
        "--type=common.Block",
        "--output={}".format(os.path.join(channel_directory, "config_block.json")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    with open(os.path.join(channel_directory, "config_block.json"), "r", encoding="utf-8") as f:
        config_block = json.load(f)

    with open(os.path.join(channel_directory, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_block["data"]["data"][0]["payload"]["data"]["config"], f, sort_keys=False, indent=4)

    with open(os.path.join(channel_directory, "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    config["channel_group"]["groups"]["Application"]["groups"][crypto_config["PeerOrgs"][0]["Name"]]["values"].update({
        "AnchorPeers": {
            "mod_policy": "Admins",
            "value": {
                "anchor_peers": [
                    {
                        "host": peer_domain_name,
                        "port": 7051
                    }
                ]
            },
            "version": 0,
        }
    })

    with open(os.path.join(channel_directory, "modified_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, sort_keys=False, indent=4)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_directory, "config.json")),
        "--type=common.Config",
        "--output={}".format(os.path.join(channel_directory, "config.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_directory, "modified_config.json")),
        "--type=common.Config",
        "--output={}".format(os.path.join(channel_directory, "modified_config.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "compute_update",
        "--original={}".format(os.path.join(channel_directory, "config.pb")),
        "--updated={}".format(os.path.join(channel_directory, "modified_config.pb")),
        "--channel_id={}".format(channel_name),
        "--output={}".format(os.path.join(channel_directory, "config_update.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_decode",
        "--input={}".format(os.path.join(channel_directory, "config_update.pb")),
        "--type=common.ConfigUpdate",
        "--output={}".format(os.path.join(channel_directory, "config_update.json")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    with open(os.path.join(channel_directory, "config_update.json"), "r", encoding="utf-8") as f:
        config_update = json.load(f)

    with open(os.path.join(channel_directory, "config_update_in_envelope.json"), "w", encoding="utf-8") as f:
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
            sort_keys=False,
            indent=4
        )

    command = [
        os.path.join(FABRIC_TOOL, "configtxlator"),
        "proto_encode",
        "--input={}".format(os.path.join(channel_directory, "config_update_in_envelope.json")),
        "--type=common.Envelope",
        "--output={}".format(os.path.join(channel_directory, "config_update_in_envelope.pb")),
    ]
    LOG.info(" ".join(command))
    subprocess.run(command, check=True)

    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "update",
        "-f",
        os.path.join(channel_directory, "config_update_in_envelope.pb"),
        "-c",
        channel_name,
        "-o",
        orderer_addresses[0],
        "--ordererTLSHostnameOverride",
        orderer_hosts[0],
        "--tls",
        "--cafile",
        os.path.join(
            orderer_directories[0], 
            "msp", 
            "tlscacerts", 
            "tlsca.{}-cert.pem".format(crypto_config["OrdererOrgs"][0]["Domain"])
        )
    ]
    LOG.info(" ".join(command))
    LOG.info(peer_env)
    subprocess.run(
        command,
        env=peer_env,
        check=True)

    os.remove(os.path.join(channel_directory, "config_block.pb"))
    os.remove(os.path.join(channel_directory, "config_block.json"))
    os.remove(os.path.join(channel_directory, "config.json"))
    os.remove(os.path.join(channel_directory, "modified_config.json"))
    os.remove(os.path.join(channel_directory, "config.pb"))
    os.remove(os.path.join(channel_directory, "modified_config.pb"))
    os.remove(os.path.join(channel_directory, "config_update.pb"))
    os.remove(os.path.join(channel_directory, "config_update.json"))
    os.remove(os.path.join(channel_directory, "config_update_in_envelope.json"))
    os.remove(os.path.join(channel_directory, "config_update_in_envelope.pb"))

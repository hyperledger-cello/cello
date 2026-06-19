import base64
from copy import deepcopy
import json
import logging
import os
import subprocess
import time

import yaml

from hyperledger_fabric.settings import CELLO_HOME, CRYPTO_CONFIG, FABRIC_TOOL

LOG = logging.getLogger(__name__)


def create_channel(channel_name: str):
    with open(
        CRYPTO_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        crypto_config = yaml.safe_load(f)

    order_org = crypto_config["OrdererOrgs"][0]
    orderer_hosts = ["{}.{}".format(spec["Hostname"], order_org["Domain"]) for spec in order_org["Specs"]]
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

    peer_org = crypto_config["PeerOrgs"][0]
    command = [
        os.path.join(FABRIC_TOOL, "peer"),
        "channel",
        "join",
        "-b",
        os.path.join(channel_directory, "genesis.block"),
    ]
    for spec in peer_org["Specs"]:
        peer_domain_name = "{}.{}".format(spec["Hostname"], peer_org["Domain"])
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


def _channel_dir(channel_name):
    return os.path.join(CELLO_HOME, channel_name)


def _read_crypto_config():
    with open(CRYPTO_CONFIG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _read_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _build_org_group(crypto_config, msp_id):
    org_name = msp_id.replace("MSP", "")
    peer_org = None
    for org in crypto_config["PeerOrgs"]:
        if org["Name"] == org_name:
            peer_org = org
            break
    if not peer_org:
        raise ValueError(f"Organization '{org_name}' not found in crypto config")

    domain = peer_org["Domain"]
    org_dir = os.path.join(CELLO_HOME, "peerOrganizations", domain)
    msp_dir = os.path.join(org_dir, "msp")

    ca_cert_path = os.path.join(msp_dir, "cacerts", f"ca.{domain}-cert.pem")
    admin_cert_path = os.path.join(msp_dir, "admincerts", f"Admin@{domain}-cert.pem")
    tls_ca_cert_path = os.path.join(msp_dir, "tlscacerts", f"tlsca.{domain}-cert.pem")

    root_certs = [_read_b64(ca_cert_path)]
    admin_certs = [_read_b64(admin_cert_path)]
    tls_root_certs = [_read_b64(tls_ca_cert_path)]

    spec = peer_org.get("Specs", [{}])[0]
    peer_host = f"{spec.get('Hostname', 'peer0')}.{domain}"

    return {
        "values": {
            "MSP": {
                "mod_policy": "Admins",
                "value": {
                    "type": 0,
                    "value": {
                        "name": msp_id,
                        "root_certs": root_certs,
                        "intermediate_certs": [],
                        "admin_sign_certs": admin_certs,
                        "tls_root_certs": tls_root_certs,
                        "tls_intermediate_certs": [],
                    }
                },
                "version": 0,
            },
            "AnchorPeers": {
                "mod_policy": "Admins",
                "value": {
                    "anchor_peers": [
                        {"host": peer_host, "port": 7051}
                    ]
                },
                "version": 0,
            },
        },
        "policies": {
            "Readers": {
                "mod_policy": "Admins",
                "policy": {
                    "type": 3,
                    "value": {
                        "rule": f"OR('{msp_id}.admin', '{msp_id}.peer', '{msp_id}.client')"
                    }
                },
                "version": 0,
            },
            "Writers": {
                "mod_policy": "Admins",
                "policy": {
                    "type": 3,
                    "value": {
                        "rule": f"OR('{msp_id}.admin', '{msp_id}.client')"
                    }
                },
                "version": 0,
            },
            "Admins": {
                "mod_policy": "Admins",
                "policy": {
                    "type": 3,
                    "value": {
                        "rule": f"OR('{msp_id}.admin')"
                    }
                },
                "version": 0,
            },
            "Endorsement": {
                "mod_policy": "Admins",
                "policy": {
                    "type": 3,
                    "value": {
                        "rule": f"OR('{msp_id}.peer')"
                    }
                },
                "version": 0,
            },
        },
        "mod_policy": "Admins",
        "version": 0,
    }


def generate_invitation_definition(channel_name, organization_msp_ids):
    channel_dir = _channel_dir(channel_name)
    os.makedirs(channel_dir, exist_ok=True)

    config_block_pb = os.path.join(channel_dir, "config_block.pb")
    config_block_json = os.path.join(channel_dir, "config_block.json")
    config_json = os.path.join(channel_dir, "config.json")
    modified_config_json = os.path.join(channel_dir, "modified_config.json")
    config_pb = os.path.join(channel_dir, "config.pb")
    modified_config_pb = os.path.join(channel_dir, "modified_config.pb")
    config_update_pb = os.path.join(channel_dir, "config_update.pb")
    config_update_json = os.path.join(channel_dir, "config_update.json")
    envelope_json = os.path.join(channel_dir, "envelope.json")
    envelope_pb = os.path.join(channel_dir, "envelope.pb")

    temp_files = [
        config_block_pb, config_block_json, config_json,
        modified_config_json, config_pb, modified_config_pb,
        config_update_pb, config_update_json, envelope_json, envelope_pb,
    ]

    try:
        crypto_config = _read_crypto_config()

        peer_org = crypto_config["PeerOrgs"][0]
        domain = peer_org["Domain"]
        peer_org_dir = os.path.join(CELLO_HOME, "peerOrganizations", domain)
        order_org = crypto_config["OrdererOrgs"][0]
        orderer_host = "{}.{}".format(order_org["Specs"][0]["Hostname"], order_org["Domain"])
        orderer_directory = os.path.join(
            CELLO_HOME, "ordererOrganizations", order_org["Domain"], "orderers", orderer_host
        )

        peer_env = {
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": peer_org["Name"] + "MSP",
            "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(
                peer_org_dir, "peers",
                "{}.{}".format(peer_org["Specs"][0]["Hostname"], domain),
                "tls", "ca.crt"
            ),
            "CORE_PEER_MSPCONFIGPATH": os.path.join(
                peer_org_dir, "users", "Admin@" + domain, "msp"
            ),
            "CORE_PEER_ADDRESS": "{}.{}:7051".format(
                peer_org["Specs"][0]["Hostname"], domain
            ),
            "FABRIC_CFG_PATH": os.path.join(
                peer_org_dir, "peers",
                "{}.{}".format(peer_org["Specs"][0]["Hostname"], domain)
            ),
        }

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "peer"),
                "channel", "fetch", "config",
                config_block_pb,
                "-c", channel_name,
                "-o", "{}:7050".format(orderer_host),
                "--ordererTLSHostnameOverride", orderer_host,
                "--tls",
                "--cafile", os.path.join(
                    orderer_directory, "msp", "tlscacerts",
                    "tlsca.{}-cert.pem".format(order_org["Domain"])
                ),
            ],
            check=True, env=peer_env,
        )

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "configtxlator"),
                "proto_decode",
                f"--input={config_block_pb}",
                "--type=common.Block",
                f"--output={config_block_json}",
            ],
            check=True,
        )

        with open(config_block_json, "r", encoding="utf-8") as f:
            config_block = json.load(f)

        config = config_block["data"]["data"][0]["payload"]["data"]["config"]

        with open(config_json, "w", encoding="utf-8") as f:
            json.dump(config, f, sort_keys=False, indent=4)

        modified_config = deepcopy(config)
        app_groups = modified_config["channel_group"]["groups"]["Application"]["groups"]

        for msp_id in organization_msp_ids:
            org_group = _build_org_group(crypto_config, msp_id)
            org_name = msp_id.replace("MSP", "")
            app_groups[org_name] = org_group

        with open(modified_config_json, "w", encoding="utf-8") as f:
            json.dump(modified_config, f, sort_keys=False, indent=4)

        for src_json, dst_pb in [(config_json, config_pb), (modified_config_json, modified_config_pb)]:
            subprocess.run(
                [
                    os.path.join(FABRIC_TOOL, "configtxlator"),
                    "proto_encode",
                    f"--input={src_json}",
                    "--type=common.Config",
                    f"--output={dst_pb}",
                ],
                check=True,
            )

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "configtxlator"),
                "compute_update",
                f"--original={config_pb}",
                f"--updated={modified_config_pb}",
                f"--channel_id={channel_name}",
                f"--output={config_update_pb}",
            ],
            check=True,
        )

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "configtxlator"),
                "proto_decode",
                f"--input={config_update_pb}",
                "--type=common.ConfigUpdate",
                f"--output={config_update_json}",
            ],
            check=True,
        )

        with open(config_update_json, "r", encoding="utf-8") as f:
            config_update = json.load(f)

        envelope = {
            "payload": {
                "header": {
                    "channel_header": {"channel_id": channel_name, "type": 2}
                },
                "data": {"config_update": config_update},
            }
        }
        with open(envelope_json, "w", encoding="utf-8") as f:
            json.dump(envelope, f, sort_keys=False, indent=4)

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "configtxlator"),
                "proto_encode",
                f"--input={envelope_json}",
                "--type=common.Envelope",
                f"--output={envelope_pb}",
            ],
            check=True,
        )

        with open(envelope_pb, "rb") as f:
            artifact = f.read()

        return artifact

    finally:
        for f_path in temp_files:
            try:
                os.remove(f_path)
            except OSError:
                pass


def sign_config_update(channel_name, artifact_bytes):
    channel_dir = _channel_dir(channel_name)
    os.makedirs(channel_dir, exist_ok=True)

    input_pb = os.path.join(channel_dir, "sign_input.pb")
    output_pb = os.path.join(channel_dir, "sign_output.pb")

    temp_files = [input_pb, output_pb]

    try:
        crypto_config = _read_crypto_config()
        peer_org = crypto_config["PeerOrgs"][0]
        domain = peer_org["Domain"]
        peer_org_dir = os.path.join(CELLO_HOME, "peerOrganizations", domain)

        peer_env = {
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": peer_org["Name"] + "MSP",
            "CORE_PEER_TLS_ROOTCERT_FILE": os.path.join(
                peer_org_dir, "peers",
                "{}.{}".format(peer_org["Specs"][0]["Hostname"], domain),
                "tls", "ca.crt"
            ),
            "CORE_PEER_MSPCONFIGPATH": os.path.join(
                peer_org_dir, "users", "Admin@" + domain, "msp"
            ),
            "CORE_PEER_ADDRESS": "{}.{}:7051".format(
                peer_org["Specs"][0]["Hostname"], domain
            ),
            "FABRIC_CFG_PATH": os.path.join(
                peer_org_dir, "peers",
                "{}.{}".format(peer_org["Specs"][0]["Hostname"], domain)
            ),
        }

        with open(input_pb, "wb") as f:
            f.write(artifact_bytes)

        subprocess.run(
            [
                os.path.join(FABRIC_TOOL, "peer"),
                "channel", "signconfigtx",
                "-f", input_pb,
                "--output", output_pb,
            ],
            check=True, env=peer_env,
        )

        with open(output_pb, "rb") as f:
            return f.read()

    finally:
        for f_path in temp_files:
            try:
                os.remove(f_path)
            except OSError:
                pass

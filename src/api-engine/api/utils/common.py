#
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
import os

from drf_yasg import openapi
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from functools import reduce, partial
from api.common.serializers import BadResponseSerializer
import uuid
from zipfile import ZipFile
from json import loads
from api.config import CELLO_HOME
import json
import logging

LOG = logging.getLogger(__name__)


def make_uuid():
    return str(uuid.uuid4())


def random_name(prefix=""):
    return "%s-%s" % (prefix, uuid.uuid4().hex)


def with_common_response(responses=None):
    if responses is None:
        responses = {}

    responses.update(
        {
            status.HTTP_400_BAD_REQUEST: BadResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: "Permission denied",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Error",
            status.HTTP_403_FORBIDDEN: "Authentication credentials "
            "were not provided.",
        }
    )

    return responses


basic_type_info = [
    (serializers.CharField, openapi.TYPE_STRING),
    (serializers.BooleanField, openapi.TYPE_BOOLEAN),
    (serializers.IntegerField, openapi.TYPE_INTEGER),
    (serializers.FloatField, openapi.TYPE_NUMBER),
    (serializers.FileField, openapi.TYPE_FILE),
    (serializers.ImageField, openapi.TYPE_FILE),
]


def to_form_paras(self):
    custom_paras = []
    for field_name, field in self.fields.items():
        type_str = openapi.TYPE_STRING
        for field_class, type_format in basic_type_info:
            if isinstance(field, field_class):
                type_str = type_format
        help_text = getattr(field, "help_text")
        default = getattr(field, "default", None)
        required = getattr(field, "required")
        if callable(default):
            custom_paras.append(
                openapi.Parameter(
                    field_name,
                    openapi.IN_FORM,
                    help_text,
                    type=type_str,
                    required=required,
                )
            )
        else:
            custom_paras.append(
                openapi.Parameter(
                    field_name,
                    openapi.IN_FORM,
                    help_text,
                    type=type_str,
                    required=required,
                    default=default,
                )
            )
    return custom_paras


def any_of(*perm_classes):
    """Returns permission class that allows access for
       one of permission classes provided in perm_classes"""

    class Or(BasePermission):
        def has_permission(*args):
            allowed = [p.has_permission(*args) for p in perm_classes]
            return reduce(lambda x, y: x or y, allowed)

    return Or


def hash_file(file, block_size=65536):
    hash_func = hashlib.md5()
    for buf in iter(partial(file.read, block_size), b""):
        hash_func.update(buf)

    return hash_func.hexdigest()


def zip_dir(dirpath, outFullName):
    """
    Compress the specified folder
    :param dirpath: specified folder
    :param outFullName: Save path+xxxx.zip
    :return: null
    """
    dir_dst = "/" + dirpath.rsplit("/", 1)[1]
    zdir = ZipFile(outFullName, "w")
    for path, dirnames, filenames in os.walk(dirpath):
        fpath = dir_dst + path.replace(dirpath, '')
        for filename in filenames:
            zdir.write(os.path.join(path, filename),
                       os.path.join(fpath, filename))
        # zip empty folder
        for dirname in dirnames:
            zdir.write(os.path.join(path, dirname),
                       os.path.join(fpath, dirname))
    zdir.close()


def zip_file(dirpath, outFullName):
    """
    Compress the specified file
    :param dirpath: specified folder of file
    :param outFullName: Save path+filename.zip
    :return: null
    """
    zfile = ZipFile(outFullName, "w")
    zfile.write(dirpath, dirpath.rsplit("/", 1)[1])
    zfile.close()


def parse_block_file(data):
    """
    Parse org config from channel config block.

    :param data: channel config block in json format.
    :param org_name: the organization prefix name
    :return organization config
    """
    config = loads(data)
    if config.get("data"):
        return config.get("data").get("data")[0].get("payload").get("data").get("config")
    return {"error": "can't find channel config"}


def to_dict(data):
    return loads(data)


def json_filter(input, output, expression):
    """
    Process JSON data using path expression similar to jq

    Args:
        input (str): JSON data or file path to JSON
        output (str): Path expression like ".data.data[0].payload.data.config"

    Returns:
        dict: Processed JSON data
    """
    # if json_data is a file path, read the file
    if isinstance(input, str):
        with open(input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = input

    # parse the path expression
    path_parts = expression.strip('.').split('.')
    result = data

    for part in path_parts:
        # handle array index, like data[0]
        if '[' in part and ']' in part:
            array_name = part.split('[')[0]
            index = int(part.split('[')[1].split(']')[0])
            result = result[array_name][index]
        else:
            result = result[part]

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, sort_keys=False, indent=4)

    LOG.info("jq {} {} -> {}".format(expression, input, output))


def json_add_anchor_peer(input, output, anchor_peer_config, org_msp):
    """
    Add anchor peer to the organization

    Args:
        input (str): JSON data or file path to JSON
        output (str): Path expression like ".data.data[0].payload.data.config"
        expression (str): Anchor peer data
    """
    # if json_data is a file path, read the file
    if isinstance(input, str):
        with open(input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = input

    if "groups" not in data["channel_group"]:
        data["channel_group"]["groups"] = {}
    if "Application" not in data["channel_group"]["groups"]:
        data["channel_group"]["groups"]["Application"] = {"groups": {}}
    if org_msp not in data["channel_group"]["groups"]["Application"]["groups"]:
        data["channel_group"]["groups"]["Application"]["groups"][org_msp] = {"values": {}}

    data["channel_group"]["groups"]["Application"]["groups"][org_msp]["values"].update(anchor_peer_config)

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=False, indent=4)

    LOG.info("jq '.channel_group.groups.Application.groups.Org1MSP.values += ... ' {} -> {}".format(input, output))


def json_create_envelope(input, output, channel):
    """
    Create a config update envelope structure

    Args:
        input (str): Path to the config update JSON file
        output (str): Path to save the envelope JSON
        channel (str): Name of the channel
    """
    try:
        # Read the config update file
        with open(input, 'r', encoding='utf-8') as f:
            config_update = json.load(f)

        # Create the envelope structure
        envelope = {
            "payload": {
                "header": {
                    "channel_header": {
                        "channel_id": channel,
                        "type": 2
                    }
                },
                "data": {
                    "config_update": config_update
                }
            }
        }

        # Write the envelope to output file
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(envelope, f, sort_keys=False, indent=4)

        LOG.info("echo 'payload ... ' | jq . > {}".format(output))

    except Exception as e:
        LOG.error("Failed to create config update envelope: {}".format(str(e)))
        raise


def init_env_vars(node, org):
    """
    Initialize environment variables for peer channel CLI.
    :param node: Node object
    :param org: Organization object.
    :return env: dict
    """
    org_name = org.name
    org_domain = org_name.split(".", 1)[1]
    dir_certificate = "{}/{}/crypto-config/ordererOrganizations/{}".format(
        CELLO_HOME, org_name, org_domain)
    dir_node = "{}/{}/crypto-config/peerOrganizations".format(
        CELLO_HOME, org_name)

    envs = {}

    if (node.type == "orderer"):
        envs = {
            "CORE_PEER_TLS_ENABLED": "true",
            "ORDERER_CA": "{}/orderers/{}/msp/tlscacerts/tlsca.{}-cert.pem".format(dir_certificate, node.name + "." + org_domain, org_domain),
            "ORDERER_ADMIN_TLS_SIGN_CERT": "{}/orderers/{}/tls/server.crt".format(dir_certificate, node.name + "." + org_domain),
            "ORDERER_ADMIN_TLS_PRIVATE_KEY": "{}/orderers/{}/tls/server.key".format(dir_certificate, node.name + "." + org_domain)
        }
    elif (node.type == "peer"):
        envs = {
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_LOCALMSPID": "{}MSP".format(org_name.split(".")[0].capitalize()),
            "CORE_PEER_TLS_ROOTCERT_FILE": "{}/{}/peers/{}/tls/ca.crt".format(dir_node, org_name, node.name + "." + org_name),
            "CORE_PEER_MSPCONFIGPATH": "{}/{}/users/Admin@{}/msp".format(dir_node, org_name, org_name),
            "CORE_PEER_ADDRESS": "{}:{}".format(
                node.name + "." + org_name, str(7051)),
            "FABRIC_CFG_PATH": "{}/{}/peers/{}/".format(dir_node, org_name, node.name + "." + org_name)
        }

    return envs

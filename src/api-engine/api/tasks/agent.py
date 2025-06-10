#
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import absolute_import, unicode_literals

import json
import logging
import os

import docker
from django.core.exceptions import ObjectDoesNotExist

from api.models import Node, Port
from api_engine.celery import app

LOG = logging.getLogger(__name__)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


class NodeHandler(object):
    def __init__(self, node_id=None, action=None, **kwargs):
        self._node_id = node_id
        self._action = action

        try:
            node = Node.objects.get(id=node_id)
            ports = Port.objects.filter(node=node)
            ports = {str(item.internal): item.external for item in ports}
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("Node Does Not Exist")

        self._node = node
        self._network_type = node.network_type
        self._network_version = node.network_version
        self._node_type = node.type
        self._agent_image = node.agent.image
        self._agent_id = str(node.agent.id)
        self._agent_ip = str(node.agent.ip)
        self._service_ports = ports

        self._agent_config_file = kwargs.get("agent_config_file")
        self._node_detail_url = kwargs.get("node_detail_url")
        self._node_file_upload_api = kwargs.get("node_file_upload_api")
        self._node_file_url = kwargs.get("node_file_url")
        self._fabric_ca_user = kwargs.get("fabric_ca_user", {})
        self._user_patch_url = kwargs.get("user_patch_url")
        self._peer_ca_list = json.loads(kwargs.get("peer_ca_list", "[]"))

        self._agent_environment = {
            "DEPLOY_NAME": node.name,
            "NETWORK_TYPE": node.network_type,
            "NETWORK_VERSION": node.network_version,
            "NODE_TYPE": node.type,
            "NODE_ID": str(node.id),
            "AGENT_ID": str(node.agent.id),
            "AGENT_IP": str(node.agent.ip),
            "AGENT_CONFIG_FILE": self._agent_config_file,
            "NODE_DETAIL_URL": self._node_detail_url,
            "NODE_UPLOAD_FILE_URL": self._node_file_upload_api,
            # Related files to node
            "NODE_FILE_URL": self._node_file_url,
            # Token for call update node api
            "TOKEN": ADMIN_TOKEN,
            "OPERATION": self._action,
            "FABRIC_CA_USER": json.dumps(self._fabric_ca_user),
            "SERVICE_PORTS": json.dumps(self._service_ports),
            "USER_PATCH_URL": self._user_patch_url,
        }

        if node.ca:
            self._agent_environment.update(
                {
                    "FABRIC_CA_CONFIG": json.dumps(
                        {
                            "admin_name": node.ca.admin_name,
                            "admin_password": node.ca.admin_password,
                            "hosts": ",".join(node.ca.hosts),
                        }
                    )
                }
            )

        if node.peer:
            peer = node.peer
            peer_config = {
                "gossip_use_leader_reflection": peer.gossip_use_leader_reflection,
                "gossip_org_leader": peer.gossip_org_leader,
                "gossip_skip_handshake": peer.gossip_skip_handshake,
                "name": peer.name,
                "local_msp_id": peer.local_msp_id,
                "ca_list": self._peer_ca_list,
            }
            self._agent_environment.update(
                {"FABRIC_PEER_CONFIG": json.dumps(peer_config)}
            )

    def _launch_agent(self):
        client = docker.from_env()
        client.containers.run(
            self._agent_image,
            auto_remove=True,
            environment=self._agent_environment,
            detach=True,
        )

    def run(self):
        self._launch_agent()


@app.task(bind=True, default_retry_delay=5, max_retires=3, time_limit=360)
def operate_node(self, node_id=None, action=None, **kwargs):
    if node_id is None or action is None:
        return False

    try:
        node_handler = NodeHandler(node_id=node_id, action=action, **kwargs)
    except ObjectDoesNotExist:
        return False

    try:
        node_handler.run()
    except Exception as e:
        self.retry(exc=e)

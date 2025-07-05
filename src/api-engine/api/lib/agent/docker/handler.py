#
# SPDX-License-Identifier: Apache-2.0
#
import logging
from requests import get, post
import json

from api.lib.agent.base import AgentBase

LOG = logging.getLogger(__name__)


class DockerAgent(AgentBase):
    """Class represents docker agent."""

    def __init__(self, node=None):
        """init DockerAgent
        param:
        node:Information needed to create, start, and delete nodes, such as organizations, nodes, and so on
        return:null
        """
        if node is None:
            node = {}
        self._id = node.get("id")
        self._name = node.get("name")
        self._urls = node.get("urls")
        self._cname = node.get("container_name")

    def create(self, info):
        """
        Create node
        :param node: Information needed to create nodes
        :return: container ID
        :rtype: string
        """
        try:
            port_map = {
                str(port.internal): str(port.external)
                for port in info.get("ports")
            }

            data = {
                "msp": info.get("msp")[2:-1],
                "tls": info.get("tls")[2:-1],
                "peer_config_file": info.get("config_file")[2:-1],
                "orderer_config_file": info.get("config_file")[2:-1],
                "img": "hyperledger/fabric:2.5.10",
                "cmd": (
                    'bash /tmp/init.sh "peer node start"'
                    if info.get("type") == "peer"
                    else 'bash /tmp/init.sh "orderer"'
                ),
                "name": info.get("name"),
                "type": info.get("type"),
                "port_map": port_map.__repr__(),
                "action": "create",
            }

            response = post("{}/api/v1/nodes".format(self._urls), data=data)

            if response.status_code == 200:
                txt = json.loads(response.text)
                return txt["data"]["id"]
            else:
                return None
        except Exception as e:
            LOG.exception("DockerAgent Not Created")
            raise e

    def delete(self, *args, **kwargs):
        try:
            response = post(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname),
                data={"action": "delete"},
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Deleted")
            raise e

    def start(self, *args, **kwargs):
        try:
            response = post(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname),
                data={"action": "start"},
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Started")
            raise e

    def restart(self, *args, **kwargs):
        try:
            response = post(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname),
                data={"action": "restart"},
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Restarted")
            raise e

    def stop(self, *args, **kwargs):
        try:
            response = post(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname),
                data={"action": "stop"},
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Stopped")
            raise e

    def get(self, *args, **kwargs):
        try:
            response = get(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname)
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Found")
            raise e

    def update_config(self, config_file, node_type):
        try:
            cmd = 'bash /tmp/update.sh "{} node start"'.format(node_type)
            data = {
                "peer_config_file": config_file,
                "orderer_config_file": config_file,
                "action": "update",
                "cmd": cmd,
            }
            response = post(
                "{}/api/v1/nodes/{}".format(self._urls, self._cname), data=data
            )
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("Config Update Failed")
            raise e

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
        LOG.info(f"DockerAgent.create called for node: {info.get('name')}")
        LOG.info(f"DockerAgent.create - Agent URL: {self._urls}/api/v1/nodes")
        try:
            port_map = {str(port.internal): str(port.external) for port in info.get("ports")}
            LOG.info(f"DockerAgent.create - Ports: {port_map}")

            # Determine image and command based on node type
            node_type = info.get("type")
            node_name = info.get("name")
            img = None
            cmd = None

            if node_type == "peer":
                img = info.get("image", "hyperledger/fabric-peer")
                cmd = 'peer node start'
            elif node_type == "orderer":
                img = info.get("image", "hyperledger/fabric-orderer")
                cmd = 'orderer'
            elif node_type == "ca":
                img = info.get("image", "hyperledger/fabric-ca")
                ca_admin_user = info.get('ca_admin_user', 'admin')
                ca_admin_pass = info.get('ca_admin_pass', 'adminpw')
                cmd = f'fabric-ca-server start -b {ca_admin_user}:{ca_admin_pass}'
            else:
                LOG.error(f"Unknown node type: {node_type} in DockerAgent.create")
                raise ValueError(f"Unknown node type: {node_type}")
            
            # Use image from info if available, otherwise default
            img = info.get("image", img)
            # Use command from info if available, otherwise default
            cmd = info.get("command", cmd)

            LOG.info(f"DockerAgent.create - Image: {img}, Command: {cmd}")

            data = {
                'msp': info.get("msp")[2:-1] if info.get("msp") else None,
                'tls': info.get("tls")[2:-1] if info.get("tls") else None,
                'config_file': info.get("config_file")[2:-1] if info.get("config_file") else None,
                'img': img,
                'cmd': cmd,
                'name': node_name,
                'type': node_type,
                'port_map': port_map.__repr__(),
                'action': 'create'
            }
            LOG.info(f"DockerAgent.create - Data to send to agent: {data}")

            response = post('{}/api/v1/nodes'.format(self._urls), data=data)
            LOG.info(f"DockerAgent.create - Agent response status: {response.status_code}")
            LOG.info(f"DockerAgent.create - Agent response text: {response.text}")

            if response.status_code == 200:
                txt = json.loads(response.text)
                if txt.get('code') == 'OK' and txt.get('data', {}).get('id'):
                    LOG.info(f"DockerAgent.create - Successfully created node, container ID: {txt['data']['id']}")
                    return txt['data']['id']
                else:
                    LOG.error(f"DockerAgent.create - Agent returned OK status but error in response body: {response.text}")
                    raise Exception(f"Agent error: {txt.get('msg', 'Unknown agent error')}")
            else:
                LOG.error(f"DockerAgent.create - Agent returned error status {response.status_code}: {response.text}")
                raise Exception(f"Agent HTTP error {response.status_code}: {response.reason}")
        except Exception as e:
            LOG.exception("DockerAgent Not Created")
            raise e

    def delete(self, *args, **kwargs):
        try:
            response = post('{}/api/v1/nodes/{}'.format(self._urls, self._cname), data={'action': 'delete'})
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Deleted")
            raise e

    def start(self, *args, **kwargs):
        try:
            response = post('{}/api/v1/nodes/{}'.format(self._urls, self._cname), data={'action': 'start'})
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Started")
            raise e

    def restart(self, *args, **kwargs):
        try:
            response = post('{}/api/v1/nodes/{}'.format(self._urls, self._cname), data={'action': 'restart'})
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Restarted")
            raise e

    def stop(self, *args, **kwargs):
        try:
            response = post('{}/api/v1/nodes/{}'.format(self._urls, self._cname), data={'action': 'stop'})
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("DockerAgent Not Stopped")
            raise e

    def get(self, *args, **kwargs):
        try:
            response = get('{}/api/v1/nodes/{}'.format(self._urls, self._cname))
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
                'peer_config_file': config_file,
                'orderer_config_file': config_file,
                'action': 'update',
                'cmd': cmd
            }
            response = post('{}/api/v1/nodes/{}'.format(self._urls, self._cname), data=data)
            if response.status_code == 200:
                return True
            else:
                raise response.reason
        except Exception as e:
            LOG.exception("Config Update Failed")
            raise e

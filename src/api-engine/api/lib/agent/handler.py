#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.conf import settings

from api.lib.agent.docker import DockerAgent
from api.lib.agent.kubernetes import KubernetesAgent
from api.common.enums import HostType

LOG = logging.getLogger(__name__)
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT")


class AgentHandler(object):
    def __init__(self, node=None):
        self._network_type = node.get("network_type")
        self._network_version = node.get("network_version")
        self._node_type = node.get("type")
        self._agent_type = node.get("agent_type")
        self._node = node
        if self._agent_type == HostType.Docker.name.lower():
            self._agent = DockerAgent(node)
        elif self._agent_type == HostType.Kubernetes.name.lower():
            self._agent = KubernetesAgent(node)

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, value):
        self._node = value

    @property
    def config(self):
        return self._agent.generate_config()

    def create(self, info):
        try:
            cid = self._agent.create(info)
            if cid:
                return cid
            else:
                return None
        except Exception as e:
            LOG.error("Agent Not Created", exc_info=True)
            raise e

    def delete(self):
        self._agent.delete()

        return True

    def start(self):
        self._agent.start()

        return True

    def stop(self):
        self._agent.stop()

        return True

    def update_config(self, config_file, node_type):
        self._agent.update_config(config_file, node_type)

        return True

    def get(self):
        try:
            return self._agent.get()
        except Exception as e:
            LOG.error("Agent Not Found: %s", e, exc_info=True)
            return False

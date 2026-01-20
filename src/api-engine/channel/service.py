import json
import logging
import os
import subprocess
import time
from typing import List
from urllib.parse import urljoin

import requests
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
    agent_url = channel_organization.agent_url
    channel_orderers = Node.objects.filter(id__in=channel_orderer_ids)
    requests.get(urljoin(agent_url, "health")).raise_for_status()
    requests.post(
        urljoin(agent_url, "channels"), 
        json=dict(
            name=channel_name, 
            orderers=list(channel_orderers.values_list('name', flat=True)), 
            peers=list(Node.objects.filter(id__in=channel_peer_ids).values_list('name', flat=True))
        )
    ).raise_for_status()

    res = Channel.objects.create(name=channel_name)
    res.organizations.add(channel_organization)
    res.orderers.add(channel_orderers)
    return res

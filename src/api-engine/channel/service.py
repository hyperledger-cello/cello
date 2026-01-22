import logging
from typing import List
from urllib.parse import urljoin

import requests

from channel.models import Channel
from node.models import Node
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
    res.orderers.add(list(channel_orderers))
    return res

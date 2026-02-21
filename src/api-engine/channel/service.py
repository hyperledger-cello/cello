import logging
from urllib.parse import urljoin

import requests

from channel.models import Channel
from organization.models import Organization

LOG = logging.getLogger(__name__)


def create(
        channel_organization: Organization,
        channel_name: str) -> Channel:
    agent_url = channel_organization.agent_url
    requests.get(urljoin(agent_url, "health")).raise_for_status()
    requests.post(
        urljoin(agent_url, "channels"),
        json=dict(name=channel_name)
    ).raise_for_status()

    res = Channel.objects.create(name=channel_name)
    res.organizations.add(channel_organization)
    return res

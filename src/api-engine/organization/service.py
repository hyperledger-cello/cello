from common.utils import safe_urljoin

import requests

from organization.models import Organization


def create_organization(org_name: str, agent_url: str) -> Organization:
    _create_organization(org_name, agent_url)
    organization = Organization(name=org_name, agent_url=agent_url)
    organization.save()
    return organization


def _create_organization(org_name: str, agent_url: str):
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.post(safe_urljoin(agent_url, "organizations"), json=dict(name=org_name)).raise_for_status()

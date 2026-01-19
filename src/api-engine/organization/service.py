from urllib.parse import urljoin

import requests

from organization.models import Organization


def create_organization(org_name: str, agent_url: str) -> Organization:
    _create_organization(org_name, agent_url)
    organization = Organization(name=org_name, agent_url=agent_url)
    organization.save()
    return organization


def _create_organization(org_name: str, agent_url: str):
    requests.get(urljoin(agent_url, "health")).raise_for_status()
    requests.post(urljoin(agent_url, "organizations"), json=dict(name=org_name)).raise_for_status()

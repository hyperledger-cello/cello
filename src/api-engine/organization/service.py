from common.utils import safe_urljoin

import requests

from organization.models import Organization


def create_organization(org_name: str, agent_url: str, msp_id: str = "") -> Organization:
    _create_organization(org_name, agent_url)
    if not msp_id:
        msp_id = "{}MSP".format(org_name.split(".", 1)[0].capitalize())
    organization = Organization(name=org_name, agent_url=agent_url, msp_id=msp_id)
    organization.save()
    return organization


def _create_organization(org_name: str, agent_url: str):
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.post(safe_urljoin(agent_url, "organizations"), json=dict(name=org_name)).raise_for_status()

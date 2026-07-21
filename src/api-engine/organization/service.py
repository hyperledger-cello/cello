# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging
from urllib.parse import urljoin

import requests

from organization.models import Organization

LOG = logging.getLogger(__name__)


def create_organization(org_name: str, agent_url: str, msp_id: str = "") -> Organization:
    try:
        _create_organization(org_name, agent_url)
    except Exception as e:
        LOG.warning(
            "Could not register org '%s' with agent at %s: %s. "
            "The organization will be created in the database but may need "
            "to be synced with the agent later.",
            org_name, agent_url, e,
        )
    if not msp_id:
        msp_id = "{}MSP".format(org_name.split(".", 1)[0].capitalize())
    organization = Organization(name=org_name, agent_url=agent_url, msp_id=msp_id)
    organization.save()
    return organization


def _get_agent_base(agent_url: str) -> str:
    if agent_url.rstrip('/').endswith('/api/v1'):
        agent_url = agent_url.rstrip('/')[:-7]
    return urljoin(agent_url, "api/v1/")


def _create_organization(org_name: str, agent_url: str):
    base = _get_agent_base(agent_url)
    requests.get(urljoin(base, "health")).raise_for_status()
    requests.post(urljoin(base, "organizations"), json=dict(name=org_name)).raise_for_status()

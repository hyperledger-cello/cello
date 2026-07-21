import hashlib
import logging
import os
from urllib.parse import urljoin

import requests

from organization.models import Organization

LOG = logging.getLogger(__name__)

AGENT_AUTH_TOKEN = os.getenv("AGENT_AUTH_TOKEN", "")


def _get_agent_base(agent_url: str) -> str:
    if agent_url.rstrip('/').endswith('/api/v1'):
        agent_url = agent_url.rstrip('/')[:-7]
    return urljoin(agent_url, "api/v1/")


def _agent_headers():
    headers = {}
    if AGENT_AUTH_TOKEN:
        headers["X-Agent-Token"] = AGENT_AUTH_TOKEN
    return headers


def create(channel_organization: Organization, channel_name: str):
    base = _get_agent_base(channel_organization.agent_url)
    requests.get(
        urljoin(base, "health"), headers=_agent_headers()
    ).raise_for_status()
    requests.post(
        urljoin(base, "channels"),
        json=dict(name=channel_name),
        headers=_agent_headers(),
    ).raise_for_status()
    from channel.models import Channel
    res = Channel.objects.create(name=channel_name)
    res.organizations.add(channel_organization)
    return res


def create_invitation_artifact(agent_url, channel_name, msp_ids):
    base = _get_agent_base(agent_url)
    requests.get(
        urljoin(base, "health"), headers=_agent_headers()
    ).raise_for_status()
    resp = requests.post(
        urljoin(base, f"channels/{channel_name}/invitations/definition"),
        json={"organization_msp_ids": msp_ids},
        headers=_agent_headers(),
    )
    resp.raise_for_status()
    content = resp.content
    return content, hashlib.sha256(content).hexdigest()


def sign_invitation_artifact(agent_url, channel_name, artifact_bytes):
    base = _get_agent_base(agent_url)
    headers = {"Content-Type": "application/octet-stream"}
    headers.update(_agent_headers())
    resp = requests.post(
        urljoin(base, f"channels/{channel_name}/invitations/sign"),
        data=artifact_bytes,
        headers=headers,
    )
    resp.raise_for_status()
    return resp.content


def accept_invitation(agent_url, channel_name, artifact_bytes):
    base = _get_agent_base(agent_url)
    headers = {"Content-Type": "application/octet-stream"}
    headers.update(_agent_headers())
    resp = requests.post(
        urljoin(base, f"channels/{channel_name}/invitations/join"),
        data=artifact_bytes,
        headers=headers,
    )
    resp.raise_for_status()

import hashlib
import logging
from common.utils import safe_urljoin

from django.core.files.base import ContentFile
import requests

from channel.models import Channel, ChannelInvitation, ChannelInvitationSignature
from organization.models import Organization

LOG = logging.getLogger(__name__)


def create(
        channel_organization: Organization,
        channel_name: str) -> Channel:
    agent_url = channel_organization.agent_url
    requests.get(safe_urljoin(agent_url, "health")).raise_for_status()
    requests.post(
        safe_urljoin(agent_url, "channels"),
        json=dict(name=channel_name)
    ).raise_for_status()

    res = Channel.objects.create(name=channel_name)
    res.organizations.add(channel_organization)
    return res


def create_invitation_artifact(agent_url, channel_name, msp_ids):
    requests.get(urljoin(agent_url, "health")).raise_for_status()
    resp = requests.post(
        urljoin(agent_url, f"channels/{channel_name}/invitations/definition"),
        json={"organization_msp_ids": msp_ids}
    )
    resp.raise_for_status()
    content = resp.content
    return content, hashlib.sha256(content).hexdigest()


def sign_invitation_artifact(agent_url, channel_name, artifact_bytes):
    resp = requests.post(
        urljoin(agent_url, f"channels/{channel_name}/invitations/sign"),
        data=artifact_bytes,
        headers={"Content-Type": "application/octet-stream"},
    )
    resp.raise_for_status()
    return resp.content


def accept_invitation(agent_url, channel_name, artifact_bytes):
    resp = requests.post(
        urljoin(agent_url, f"channels/{channel_name}/invitations/join"),
        data=artifact_bytes,
        headers={"Content-Type": "application/octet-stream"},
    )
    resp.raise_for_status()

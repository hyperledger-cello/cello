import json
import tarfile
from typing import Optional, List

from chaincode.models import Chaincode
from channel.models import Channel
from node.models import Node
from user.models import UserProfile


def create_chaincode(package, channel: Channel, user: UserProfile, peers: List[Node], description: str) -> Chaincode:
    chaincode = Chaincode(
        package=package,
        channel=channel,
        creator=user,
        description=description,
    )
    chaincode.save()
    chaincode.peers.add(*peers)
    return chaincode


def get_metadata_label(file) -> Optional[str]:
    file.seek(0)
    res = None
    with tarfile.open(fileobj=file, mode='r:gz') as tar:
        for member in tar.getmembers():
            if member.name.endswith("metadata.json"):
                res = json.loads(
                    tar.extractfile(member)
                        .read()
                        .decode("utf-8")
                ).get("label")
                break
    file.seek(0)
    return res

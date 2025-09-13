from enum import unique

from common.enums import ExtraEnum


@unique
class NodeType(ExtraEnum):
    Orderer = 1
    Peer = 2


@unique
class NodeStatus(ExtraEnum):
    Created = 1
    Running = 2
    Failed = 3

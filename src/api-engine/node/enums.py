from enum import unique

from common.enums import ExtraEnum


@unique
class NodeType(ExtraEnum):
    Orderer = 1
    Peer = 2


@unique
class NodeStatus(ExtraEnum):
    Created = 0
    Restarting = 1
    Running = 2
    Removing = 3
    Paused = 4
    Exited = 5
    Dead = 6

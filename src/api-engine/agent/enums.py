from enum import unique

from common.enums import ExtraEnum


@unique
class AgentStatus(ExtraEnum):
    Inactive = 0
    Active = 1

@unique
class AgentType(ExtraEnum):
    Docker = 0

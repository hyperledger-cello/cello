from enum import unique

from common.enums import ExtraEnum


@unique
class HostStatus(ExtraEnum):
    Inactive = 0
    Active = 1

@unique
class HostType(ExtraEnum):
    Docker = 0

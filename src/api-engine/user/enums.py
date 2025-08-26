from enum import unique

from common.enums import ExtraEnum


@unique
class UserRole(ExtraEnum):
    Admin = 0
    Operator = 1
    User = 2

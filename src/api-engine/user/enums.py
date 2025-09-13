from enum import unique, Enum, auto


@unique
class UserRole(Enum):
    ADMIN = auto()
    USER = auto()

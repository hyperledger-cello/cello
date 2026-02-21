from enum import Enum


class ChaincodeStatus(Enum):
    CREATED = "CREATED"
    INSTALLED = 'INSTALLED'
    APPROVED = 'APPROVED'
    COMMITTED = 'COMMITTED'


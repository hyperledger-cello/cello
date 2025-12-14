import os

from api_engine.settings import FABRIC_CFG

# Command class reads local environment variables by given their names
class Command:
    def __init__(self, version, **kwargs):
        self.version = version
        # Setting environment variables according to user input. Recommended main settings: CORE_PEER_LOCALMSPID、
        # CORE_PEER_TLS_CERT_FILE、 CORE_PEER_TLS_KEY_FILE、CORE_PEER_TLS_ROOTCERT_FILE、CORE_PEER_MSPCONFIGPATH，
        # CORE_PEER_MSPCONFIGPATH、 CORE_PEER_TLS_ROOTCERT_FILE，CORE_PEER_ADDRESS and so on.

        # Please put the config configuration file of the fabric binary in the /opt/node directory
        os.environ["FABRIC_CFG_PATH"] = FABRIC_CFG
        # os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        for k, v in kwargs.items():
            os.environ[k] = v

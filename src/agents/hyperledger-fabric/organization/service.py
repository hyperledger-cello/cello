import logging
import os
import subprocess

import yaml

from hyperledger_fabric.settings import CELLO_HOME, FABRIC_TOOL, CRYPTO_CONFIG

LOG = logging.getLogger(__name__)

def create(name: str):
    # create CRYPTO_CONFIG
    with open(
        CRYPTO_CONFIG,
        "w",
        encoding="utf-8",
    ) as f:
        yaml.dump({
            "PeerOrgs": [dict(
                Domain=name,
                Name=name.split(".")[0].capitalize(),
                CA=dict(
                    # Temporary hardcoded. Open in the future.
                    Country="CN",
                    Locality="BJ",
                    Province="CP",
                ),
                Specs=[],
                EnableNodeOUs=True,
                Template=dict(Count=0),
                Users=dict(Count=0),
            )],
            "OrdererOrgs": [dict(
                Domain=name.split(".", 1)[1],
                Name="Orderer",
                CA=dict(
                    # Temporary hardcoded. Open in the future.
                    Country="CN",
                    Locality="BJ",
                    Province="CP",
                ),
                Specs=[],
                EnableNodeOUs=True,
                Template=dict(Count=0),
            )]
        }, f)
        # Create crypto configs
        command = [
            os.path.join(FABRIC_TOOL, "cryptogen"),
            "generate",
            "--output={}".format(CELLO_HOME),
            "--config={}".format(CRYPTO_CONFIG),
        ]
        LOG.info(" ".join(command))
        # After this, there should files like
        # CELLO_HOME
        # |_ peerOrganizations
        # |_ ordererOrganizations
        # |_ crypto-config.yaml
        LOG.info(subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
        ).stdout)

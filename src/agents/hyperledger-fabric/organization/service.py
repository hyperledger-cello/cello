import logging
import os
import subprocess

import yaml

from hyperledger_fabric.settings import CELLO_HOME, FABRIC_TOOL

LOG = logging.getLogger(__name__)

def create(name: str):
    # create $CELLO_HOME/crypto-config.yaml
    crypto_config = os.path.join(CELLO_HOME, "crypto-config.yaml")
    with open(
        crypto_config,
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
            "--config={}".format(crypto_config),
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

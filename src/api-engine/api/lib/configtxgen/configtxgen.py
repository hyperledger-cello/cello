#
# SPDX-License-Identifier: Apache-2.0
#
from api.config import CELLO_HOME, FABRIC_TOOL, FABRIC_VERSION

import subprocess
import logging

LOG = logging.getLogger(__name__)


class ConfigTxGen:
    """Class represents cryptotxgen."""

    def __init__(
        self,
        network,
        filepath=CELLO_HOME,
        configtxgen=FABRIC_TOOL,
        version=FABRIC_VERSION,
    ):
        """init CryptoGen
        param:
            network: network's name
            configtxgen: tool path
            version: version
            filepath: cello's working directory
        return:
        """
        self.network = network
        self.configtxgen = configtxgen + "/configtxgen"
        self.filepath = filepath
        self.version = version

    def genesis(self, profile="", channelid="", outputblock="genesis.block"):
        """generate gensis
        param:
            profile: profile
            channelid: channelid
            outputblock: outputblock
        return:
        """
        try:
            command = [
                self.configtxgen,
                "-configPath",
                "{}/{}/".format(self.filepath, self.network),
                "-profile",
                "{}".format(profile),
                "-outputBlock",
                "{}/{}/{}".format(self.filepath, self.network, outputblock),
                "-channelID",
                "{}".format(channelid),
            ]

            LOG.info(" ".join(command))

            subprocess.run(command, check=True)

        except subprocess.CalledProcessError as e:
            err_msg = "configtxgen genesis fail! "
            raise Exception(err_msg + str(e))

        except Exception as e:
            err_msg = "configtxgen genesis fail! "
            raise Exception(err_msg + str(e))

    def anchorpeer(self, profile, channelid, outputblock):
        """set anchorpeer
        param:
            profile: profile
            channelid: channelid
            outputblock: outputblock
        return:
        """
        pass

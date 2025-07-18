#
# SPDX-License-Identifier: Apache-2.0
#
import os
import json
import subprocess
import time
from api.lib.peer.command import Command
from api.config import FABRIC_TOOL, FABRIC_VERSION
import logging

LOG = logging.getLogger(__name__)


class Channel(Command):
    """Call CMD to perform channel create, join and other related operations"""

    def __init__(self, version=FABRIC_VERSION, peer=FABRIC_TOOL, **kwargs):
        self.peer = peer + "/peer"
        self.osnadmin = peer + "/osnadmin"
        super(Channel, self).__init__(version, **kwargs)

    def create(self, channel, orderer_admin_url, block_path, time_out="90s"):
        try:
            command = []

            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                command = [
                    self.osnadmin,
                    "channel", "join",
                    "--channelID", channel,
                    "--config-block", block_path,
                    "-o", orderer_admin_url,
                ]
            else:
                ORDERER_CA = os.getenv("ORDERER_CA")
                ORDERER_ADMIN_TLS_SIGN_CERT = os.getenv("ORDERER_ADMIN_TLS_SIGN_CERT")
                ORDERER_ADMIN_TLS_PRIVATE_KEY = os.getenv("ORDERER_ADMIN_TLS_PRIVATE_KEY")
                command = [
                    self.osnadmin,
                    "channel", "join",
                    "--channelID", channel,
                    "--config-block", block_path,
                    "-o", orderer_admin_url,
                    "--ca-file", ORDERER_CA,
                    "--client-cert", ORDERER_ADMIN_TLS_SIGN_CERT,
                    "--client-key", ORDERER_ADMIN_TLS_PRIVATE_KEY
                ]

            LOG.info(" ".join(command))

            res = subprocess.run(command, check=True)

        except subprocess.CalledProcessError as e:
            err_msg = "create channel failed for {}!".format(e)
            raise Exception(err_msg + str(e))

        except Exception as e:
            err_msg = "create channel failed for {}!".format(e)
            raise Exception(err_msg)
        return res

    def list(self):
        try:
            res = subprocess.Popen("{} channel list".format(self.peer), shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = res.communicate()
            return_code = res.returncode

            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                content = content.split("\n")
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "get channel list failed for {}!".format(e)
            raise Exception(err_msg)
        return return_code, content[1:-1]

    def update(self, channel, channel_tx, orderer_url):
        """
        Send a configtx update.
        params:
            channel: channel id.
            channel_tx: Configuration transaction file generated by a tool such as configtxgen for submitting to orderer
            orderer_url: Ordering service endpoint.
        """
        try:
            ORDERER_CA = os.getenv("ORDERER_CA")

            command = [
                self.peer,
                "channel", "update",
                "-f", channel_tx,
                "-c", channel,
                "-o", orderer_url,
                "--ordererTLSHostnameOverride", orderer_url.split(":")[0],
                "--tls",
                "--cafile", ORDERER_CA
            ]
            LOG.info(" ".join(command))

            res = subprocess.run(command, check=True)

        except Exception as e:
            err_msg = "update channel failed for {}!".format(e)
            raise Exception(err_msg)
        return res

    def fetch(self, block_path, channel, orderer_general_url, max_retries=5, retry_interval=1):
        """
        Fetch a specified block, writing it to a file e.g. <channelID>.block.
        params:
            option: block option newest|oldest|config|(block number).
            channel: channel id.
        """
        res = 0
        command = []
        if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
            command = [
                self.peer,
                "channel", "fetch",
                "config", block_path,
                "-o", orderer_general_url,
                "-c", channel
            ]
        else:
            ORDERER_CA = os.getenv("ORDERER_CA")
            orderer_address = orderer_general_url.split(":")[0]
            command = [
                self.peer,
                "channel", "fetch",
                "config", block_path,
                "-o", orderer_general_url,
                "--ordererTLSHostnameOverride", orderer_address,
                "-c", channel,
                "--tls",
                "--cafile", ORDERER_CA
            ]

        LOG.info(" ".join(command))

        # Retry fetching the block up to max_retries times
        for attempt in range(1, max_retries + 1):
            try:
                LOG.debug("Attempt %d/%d to fetch block", attempt, max_retries)

                res = subprocess.run(command, check=True)

                LOG.info("Successfully fetched block")
                break

            except subprocess.CalledProcessError as e:
                LOG.debug(f"Attempt {attempt}/{max_retries} failed")

                if attempt <= max_retries:
                    time.sleep(retry_interval)
                else:
                    LOG.error(f"Failed to fetch block after {max_retries} attempts")
                    raise e

        return res

    def signconfigtx(self, channel_tx):
        """
        Signs a configtx update.
        params:
            channel_tx: Configuration transaction file generated by a tool such as configtxgen for submitting to orderer
        """
        try:
            res = os.system(
                "{} channel signconfigtx -f {}".format(self.peer, channel_tx))
        except Exception as e:
            err_msg = "signs a configtx update failed {}".format(e)
            raise Exception(err_msg)
        res = res >> 8
        return res

    def join(self, block_path):
        """
        Joins the peer to a channel.
        params:
            block_path: Path to file containing genesis block.
        """
        try:
            command = "{} channel join -b {} ".format(self.peer, block_path)

            LOG.info(f"{command}")

            res = os.system(command)

        except Exception as e:
            err_msg = "join the peer to a channel failed. {}".format(e)
            raise Exception(err_msg)
        res = res >> 8
        return res

    def getinfo(self, channel):
        """
        Get blockchain information of a specified channel.
        params:
            channel: In case of a newChain command, the channel ID to create.
        """
        try:
            res = subprocess.Popen("{} channel getinfo  -c {}".format(self.peer, channel), shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = res.communicate()
            return_code = res.returncode

            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                content = content.split("\n")[0].split(":", 1)[1]
                block_info = json.loads(content)
                body = {"block_info": block_info}
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "get blockchain information of a specified channel failed. {}".format(
                e)
            raise Exception(err_msg)
        return return_code, body

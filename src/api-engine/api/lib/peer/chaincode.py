#
# SPDX-License-Identifier: Apache-2.0
#
import os
import json
import subprocess
from api.lib.peer.command import Command
from api.config import FABRIC_TOOL, FABRIC_CFG, FABRIC_VERSION
import logging

LOG = logging.getLogger(__name__)


class ChainCode(Command):
    def __init__(self, version=FABRIC_VERSION, peer=FABRIC_TOOL, **kwargs):
        self.peer = peer + "/peer"
        super(ChainCode, self).__init__(version, **kwargs)

    def lifecycle_package(self, cc_name, cc_version, cc_path, language):
        """
            package the chaincode to a tar.gz file.
        :param cc_name: chaincode name
        :param cc_version: chaincode version
        :param cc_path: where the chaincode is
        :param language: Chain code development language, default: golang
        :return 0 means success.
        """
        try:
            label = cc_name + "_" + cc_version
            res = os.system("{} lifecycle chaincode package {}.tar.gz --path {} --lang {} --label {}"
                            .format(self.peer, cc_name, cc_path, language, label))
            res = res >> 8
        except Exception as e:
            err_msg = "package chaincode failed for {}!".format(e)
            raise Exception(err_msg)
        return res

    def lifecycle_install(self, cc_targz):
        """
            install the chaincode to peer.
        :param cc_targz: chaincode name wich accessible path
        :return: 0 means success.
        """
        try:
            command = [
                self.peer,
                "lifecycle", "chaincode", "install",
                cc_targz
            ]
            LOG.info(" ".join(command))
            res = os.system(" ".join(command))
            res = res >> 8
        except Exception as e:
            err_msg = "install chaincode failed for {}!".format(e)
            raise Exception(err_msg)
        return res

    def lifecycle_query_installed(self, timeout):
        """
            get the chaincode info installed in peer.
        :param timeout:
        :return: res 0 means success
                 installed_chaincodes: the json format of installed_chaincodes info
        """

        try:
            command = [
                self.peer,
                "lifecycle", "chaincode", "queryinstalled",
                "--output", "json",
                "--connTimeout", timeout
            ]
            LOG.info(" ".join(command))
            res = subprocess.Popen(
                command,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = res.communicate()
            return_code = res.returncode

            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                installed_chaincodes = json.loads(content)
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "query_installed chaincode info failed for {}!".format(e)
            raise Exception(err_msg)
        return return_code, installed_chaincodes

    def lifecycle_get_installed_package(self, timeout):
        """
            lifecycle_query_installed will return a list installed in peer.
            then execute cmd to get all chaincode with tar.gz format installed in peer.
        :param timeout:
        :return: res_return: 0 means success get all chaincode in peers.
        """
        try:
            res, installed = self.lifecycle_query_installed("3s")
            res_return = 0
            if res == 0:
                for item in installed['installed_chaincodes']:
                    res_get = os.system("{} lifecycle chaincode getinstalledpackage --package-id {} "
                                        "--output-directory {} --connTimeout {}".format(self.peer,
                                                                                        item['package_id'], FABRIC_CFG, timeout))
                    res_get = res_get >> 8
                    res_return = res_return or res_get
            else:
                print("package_id get failed.")
                return 1, {}
        except Exception as e:
            err_msg = "get_installed_package failed for {}!".format(e)
            raise Exception(err_msg)
        return res_return

    def lifecycle_approve_for_my_org(self, orderer_url, channel_name, cc_name,
                                     chaincode_version, sequence, policy, init_flag):
        """
        The administrator can use the peer lifecycle chaincode approveformyorg subcommand to approve the chain code on
        behalf of the organization.
        :param orderer_url: orderer accessable url
        :param channel_name: channel name
        :param cc_name: chaincode name
        :param chaincode_version: chaincode version
        :param sequence: The channel chain code defines the serial number. The default value is 1
        :param policy: chaincode policy
        :param init_flag: if the chaincode is first init.
        :return:
        """
        try:
            res, installed = self.lifecycle_query_installed("3s")
            cc_label = cc_name + "_" + chaincode_version
            package_id = ""
            for each in installed['installed_chaincodes']:
                if each['label'] == cc_label:
                    package_id = each['package_id']
                    break
            if package_id == "":
                return 1, "not exist the chaincode, please check chaincode_name and chaincode_version"

            command = []
            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "approveformyorg",
                    "-o", orderer_url,
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", chaincode_version,
                    "--package-id", package_id,
                    "--sequence", str(sequence)
                ]
            else:
                ORDERER_CA = os.getenv("ORDERER_CA")
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "approveformyorg",
                    "-o", orderer_url,
                    "--ordererTLSHostnameOverride", orderer_url.split(":")[0],
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", chaincode_version,
                    "--package-id", package_id,
                    "--sequence", str(sequence),
                    "--tls",
                    "--cafile", ORDERER_CA
                ]

            if init_flag:
                command.append("--init-required")
            if policy:
                command.append("--signature-policy")
                command.append(policy)

            LOG.info(" ".join(command))
            res = subprocess.Popen(command, shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = res.communicate()
            return_code = res.returncode

            if return_code == 0:
                content = str(stdout, encoding="utf-8")
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "lifecycle_approve_for_my_org failed for {}!".format(e)
            raise Exception(err_msg)
        return return_code, content

    def lifecycle_query_approved(self, channel_name, cc_name):
        """
         query_approved chaincode information.
        :param channel_name: channel name
        :param cc_name: chaincode name
        :return:
        """

        try:
            res = subprocess.Popen("{} lifecycle chaincode queryapproved --output json --channelID {}"
                                   " --name {}".format(self.peer,
                                                       channel_name, cc_name),
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = res.communicate()
            return_code = res.returncode
            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                chaincodes_info = json.loads(content)
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "lifecycle_query_approved failed for {}!".format(e)
            raise Exception(err_msg)

        return return_code, chaincodes_info

    def lifecycle_check_commit_readiness(self, channel_name, cc_name, cc_version, sequence=1):
        """
        :param channel_name:channel name
        :param cc_name: chaincode name
        :param cc_version: chaincode version
        :param sequence:The channel chain code defines the serial number. The default value is 1
        :return:
        """
        try:
            ORDERER_CA = os.getenv("ORDERER_CA")
            command = []
            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "checkcommitreadiness",
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", cc_version,
                    "--sequence", str(sequence),
                    "--output", "json",
                ]
            else:
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "checkcommitreadiness",
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", cc_version,
                    "--sequence", str(sequence),
                    "--tls",
                    "--cafile", ORDERER_CA,
                    "--output", "json",
                ]

            LOG.info(" ".join(command))

            res = subprocess.Popen(command, shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = res.communicate()
            return_code = res.returncode
            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                chaincodes_info = json.loads(content)
                return return_code, chaincodes_info
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "lifecycle_check_commit_readiness failed for {}!".format(e)
            raise Exception(err_msg)

    def lifecycle_commit(self, orderer_url, channel_name, cc_name, chaincode_version, sequence, policy, peer_list=[], peer_root_certs=[], init_flag=False):
        """
        The administrator can submit the chain code definition to the specified channel by using the peer lifecycle
        chain code commit subcommand
        :param orderer_url: orderer accessable url
        :param channel_name:channel name
        :param cc_name:chaincode name
        :param chaincode_version:chaincode version
        :param sequence:The channel chain code defines the serial number. The default value is 1
        :param policy:chaincode policy
        :param peer_list: the list of peerAddress
        :param peer_root_certs: the list of peer_root_certs, the orderer should be same as peerlist's.
        :param init_flag:if the chaincode is first init.
        :return:
        """
        try:
            command = []
            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "commit",
                    "-o", orderer_url,
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", chaincode_version,
                    "--sequence", str(sequence),
                ]
            else:
                ORDERER_CA = os.getenv("ORDERER_CA")
                command = [
                    self.peer,
                    "lifecycle", "chaincode", "commit",
                    "-o", orderer_url,
                    "--ordererTLSHostnameOverride", orderer_url.split(":")[0],
                    "--channelID", channel_name,
                    "--name", cc_name,
                    "--version", chaincode_version,
                    "--sequence", str(sequence),
                    "--tls",
                    "--cafile", ORDERER_CA,
                ]

            for i in range(len(peer_list)):
                command.append("--peerAddresses")
                command.append(peer_list[i])
                command.append("--tlsRootCertFiles")
                command.append(peer_root_certs[i])

            if init_flag:
                command.append("--init-required")
            if policy:
                command.append("--signature-policy")
                command.append(policy)

            LOG.info(" ".join(command))
            res = os.system(" ".join(command))
            res = res >> 8
            return res

        except Exception as e:
            err_msg = "lifecycle_commit failed for {}!".format(e)
            raise Exception(err_msg)

    def lifecycle_query_committed(self, channel_name, cc_name):
        """

        :param channel_name:channel name
        :param cc_name:chaincode name
        :return: chaincodes info has commited in channel of the cc_name
        """
        try:
            command = [
                self.peer,
                "lifecycle", "chaincode", "querycommitted",
                "--channelID", channel_name,
                "--output", "json",
                "--name", cc_name,
            ]
            LOG.info(" ".join(command))
            res = subprocess.Popen(command, shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = res.communicate()
            return_code = res.returncode
            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                chaincodes_commited = json.loads(content)
                return return_code, chaincodes_commited
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "lifecycle_query_committed failed for {}!".format(e)
            raise Exception(err_msg)

    def invoke(self, orderer_url, orderer_tls_rootcert, channel_name, cc_name, args, init=False):
        """
        :param orderer_url:orderer accessable url
        :param orderer_tls_rootcert: orderer tls certificate
        :param channel_name: channel name
        :param cc_name: chaincode name
        :param args: args to invoke
        :param init: if the chaincode is first init.
        :return:
            if success: 0, ''
            else: 1, stderr
        """
        try:
            if init:
                invoke_command = "{} chaincode invoke -I -o {} --channelID {} --name {} -c '{}'"
                invoke_command_tls = "{} chaincode invoke -I -o {} --tls --cafile {} --channelID {} --name {} -c '{}'"
            else:
                invoke_command = "{} chaincode invoke -o {} --channelID {} --name {} -c '{}'"
                invoke_command_tls = "{} chaincode invoke -o {} --tls --cafile {} --channelID {} --name {} -c '{}'"

            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                res = subprocess.Popen(invoke_command.format(self.peer, orderer_url, channel_name, cc_name, args),
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = res.communicate()
                return_code = res.returncode
                if return_code == 0:
                    return return_code, ''
                else:
                    stderr = str(stderr, encoding="utf-8")
                    return return_code, stderr
            else:
                res = subprocess.Popen(invoke_command_tls.format(self.peer, orderer_url, orderer_tls_rootcert,
                                                                 channel_name, cc_name, args),
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = res.communicate()
                return_code = res.returncode
                if return_code == 0:
                    return return_code, ''
                else:
                    stderr = str(stderr, encoding="utf-8")
                    return return_code, stderr
        except Exception as e:
            err_msg = "invoke failed for {}!".format(e)
            raise Exception(err_msg)

    def query(self, orderer_url, orderer_tls_rootcert, channel_name, cc_name, args):
        try:
            if os.getenv("CORE_PEER_TLS_ENABLED") == "false" or os.getenv("CORE_PEER_TLS_ENABLED") is None:
                res = subprocess.Popen("{} chaincode query -o {} --channelID {} --name {} -c '{}'"
                                       .format(self.peer, orderer_url, channel_name, cc_name, args),
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = res.communicate()
                return_code = res.returncode
                if return_code == 0:
                    return return_code, ''
                else:
                    stderr = str(stderr, encoding="utf-8")
                    return return_code, stderr
            else:
                res = subprocess.Popen("{} chaincode query -o {} --tls --cafile {} --channelID {}"
                                       " --name {} -c '{}'".format(self.peer, orderer_url, orderer_tls_rootcert,
                                                                   channel_name, cc_name, args),
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = res.communicate()
                return_code = res.returncode
                if return_code == 0:
                    content = str(stdout, encoding="utf-8")
                    query_result = json.loads(content)
                    return return_code, query_result
                else:
                    stderr = str(stderr, encoding="utf-8")
                    return return_code, stderr
        except Exception as e:
            err_msg = "query failed for {}!".format(e)
            raise Exception(err_msg)

    def lifecycle_calculatepackageid(self, cc_path):
        """
        calculate the chaincode packageid.
        :param cc_path: where the chaincode package is
        :return: calculated packageid
        """
        try:
            res = subprocess.Popen(
                "{} lifecycle chaincode calculatepackageid {} ".format(self.peer, cc_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = res.communicate()
            return_code = res.returncode
            if return_code == 0:
                content = str(stdout, encoding="utf-8")
                return return_code, content
            else:
                stderr = str(stderr, encoding="utf-8")
                return return_code, stderr
        except Exception as e:
            err_msg = "calculated chaincode packageid failed for {}!".format(e)
            raise Exception(err_msg)

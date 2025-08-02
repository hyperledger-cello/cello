#
# SPDX-License-Identifier: Apache-2.0
#
from string import Template
import os
import yaml
from api.config import CELLO_HOME


class NodeConfig:
    """Class represents crypto-config yaml."""

    def __init__(
        self,
        org,
        peer_file="core.yaml",
        orderer_file="orderer.yaml",
        ca_file="",
    ):
        """
        init  node config

        :param org: organization name
        :param peer: peer profile template
        :param ca: ca profile template
        :param orderer: orderer profile template
        :return: none
        :rtype: xxx
        """
        self.org = org
        self.peer_file = peer_file
        self.orderer_file = orderer_file
        self.ca_file = ca_file

    @staticmethod
    def _render(src, dst, **kw):
        """
        Generate configuration file based on parameters

        :param kw: Node configuration parameters,Use the underline interval key。
                    e.g.,
                    peer listenAddress, kwargs["peer_listenAddress"]="0.0.0.0:7051"
                    chaincode builder, kwargs["chaincode_builder"]="hyperledger/fabric-ccenv:1.4.2"
        :param src: Node profile template
        :param dst: Node profile
        :return: none
        :rtype: none
        """
        try:
            with open(src, "r+") as f:
                cfg = yaml.load(f, Loader=yaml.FullLoader)

            for key, value in kw.items():
                keys = key.split("_")
                # switch = {2: cfg[keys[0]][keys[1]],
                #           3: cfg[keys[0]][keys[1]][keys[2]],
                #           4: cfg[keys[0]][keys[1]][keys[2]][keys[3]],
                #           5: cfg[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]]}

                if len(keys) == 2:
                    cfg[keys[0]][keys[1]] = value
                elif len(keys) == 3:
                    cfg[keys[0]][keys[1]][keys[2]] = value
                elif len(keys) == 4:
                    cfg[keys[0]][keys[1]][keys[2]][keys[3]] = value
                elif len(keys) == 5:
                    cfg[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]] = value

            with open(dst, "w+") as f:
                yaml.dump(cfg, f)
        except Exception as e:
            raise Exception("Configuration File Not Generated") from e

    def __from_dst(self, node, node_type):
        """
        Location of the new profile

        :param node: node name
        :param node_type: node type (peer, orderer, ca)
        :return: dst
        :rtype: string
        """
        if node_type == "peer":
            dst = "{}/{}/crypto-config/peerOrganizations/{}/peers/{}.{}/{}".format(
                CELLO_HOME, self.org, self.org, node, self.org, self.peer_file
            )
        elif node_type == "orderer":
            dst = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}.{}/{}".format(
                CELLO_HOME,
                self.org,
                self.org.split(".", 1)[1],
                node,
                self.org.split(".", 1)[1],
                self.orderer_file,
            )
        else:
            dst = ""
        return dst

    def peer(self, node, **kwargs):
        """
        Location of the node profile

        :param node: peer name
        :param kwargs: Node configuration parameters,Use the underline interval key。
                    e.g.,
                    peer listenAddress, kwargs["peer_listenAddress"]="0.0.0.0:7051"
                    chaincode builder, kwargs["chaincode_builder"]="hyperledger/fabric-ccenv:1.4.2"
        :return: none
        :rtype: none
        """
        src = "/opt/node/core.yaml.bak"
        dst = self.__from_dst(node, "peer")
        self._render(src, dst, **kwargs)

    def orderer(self, node, **kwargs):
        """
        Location of the orderer profile

        :param node: orderer name
        :param kwargs: Node configuration parameters,Use the underline interval key。
                    e.g.,
                    peer listenAddress, kwargs["peer_listenAddress"]="0.0.0.0:7051"
                    chaincode builder, kwargs["chaincode_builder"]="hyperledger/fabric-ccenv:1.4.2"
        :return: none
        :rtype: none
        """
        src = "/opt/node/orderer.yaml.bak"
        dst = self.__from_dst(node, "orderer")
        self._render(src, dst, **kwargs)

    def ca(self, node, **kwargs):
        """
        Location of the orderer profile

        :param node: ca name
        :param kwargs: Node configuration parameters,Use the underline interval key。
                    e.g.,
                    peer listenAddress, kwargs["peer_listenAddress"]="0.0.0.0:7051"
                    chaincode builder, kwargs["chaincode_builder"]="hyperledger/fabric-ccenv:1.4.2"
        :return: none
        :rtype: none
        """
        src = self.ca_file
        dst = self.__from_dst(node, "ca")
        self._render(src, dst, **kwargs)

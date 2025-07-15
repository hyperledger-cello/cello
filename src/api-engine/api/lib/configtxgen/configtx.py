#
# SPDX-License-Identifier: Apache-2.0
#
import yaml
import os
from copy import deepcopy
from api.config import CELLO_HOME


def load_configtx(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class ConfigTX:
    """Class represents crypto-config yaml."""

    def __init__(self, network, filepath=CELLO_HOME, orderer=None, raft_option=None, template_path="/opt/config/configtx.yaml"):
        """init ConfigTX
                param:
                    network: network's name
                    orderer: configuration of output block
                    raft_option: configuration of raft
                    filepath: cello's working directory
                return:
        """
        self.filepath = filepath
        self.network = network
        self.template = load_configtx(template_path)

    def create(self, name, consensus, orderers, peers, orderer_cfg=None, application=None, option=None):
        """create the configtx.yaml
                param:
                    consensus:consensus
                    orderers:the list of orderer
                    peers: the list of peer
                    orderer_cfg: the config of orderer
                    application: application
                    option: option
                return:
        """
        OrdererDefaults = self.template["Orderer"]
        ChannelDefaults = self.template["Channel"]
        ApplicationDefaults = self.template["Application"]
        ChannelCapabilities = self.template["Capabilities"]["Channel"]
        OrdererCapabilities = self.template["Capabilities"]["Orderer"]
        ApplicationCapabilities = self.template["Capabilities"]["Application"]

        OrdererOrganizations = []
        OrdererAddress = []
        Consenters = []

        for orderer in orderers:
            OrdererMSP = "OrdererMSP"
            OrdererOrg = dict(
                Name="Orderer",
                ID=OrdererMSP,
                MSPDir='{}/{}/crypto-config/ordererOrganizations/{}/msp'.format(self.filepath, orderer["name"], orderer['name'].split(".", 1)[1]),
                Policies=dict(
                    Readers=dict(Type="Signature", Rule="OR('{}.member')".format(OrdererMSP)),
                    Writers=dict(Type="Signature", Rule="OR('{}.member')".format(OrdererMSP)),
                    Admins=dict(Type="Signature", Rule="OR('{}.admin')".format(OrdererMSP))
                )
            )
            for host in orderer['hosts']:
                OrdererAddress.append('{}.{}:{}'.format(host['name'], orderer['name'].split(".", 1)[1], 7050))
                Consenters.append(dict(
                    Host='{}.{}'.format(host['name'], orderer['name'].split(".", 1)[1]),
                    Port=7050,
                    ClientTLSCert='{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}.{}/tls/server.crt'
                                  .format(self.filepath, orderer['name'], orderer['name'].split(".", 1)[1], host['name'], orderer['name'].split(".", 1)[1]),
                    ServerTLSCert='{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}.{}/tls/server.crt'
                                  .format(self.filepath, orderer['name'], orderer['name'].split(".", 1)[1], host['name'], orderer['name'].split(".", 1)[1])))
            OrdererOrg["OrdererEndpoints"] = deepcopy(OrdererAddress)
            OrdererOrganizations.append(OrdererOrg)

        PeerOrganizations = []

        for peer in peers:
            PeerMSP = peer['name'].split(".", 1)[0].capitalize() + "MSP"
            PeerOrganizations.append(dict(Name=peer['name'].split(".", 1)[0].capitalize(),
                                          ID=PeerMSP,
                                          MSPDir='{}/{}/crypto-config/peerOrganizations/{}/msp'.format(self.filepath, peer['name'], peer['name']),
                                          Policies=dict(Readers=dict(Type="Signature", Rule="OR('{}.admin', '{}.peer', '{}.client')".format(PeerMSP, PeerMSP, PeerMSP)),
                                                        Writers=dict(Type="Signature", Rule="OR('{}.admin', '{}.client')".format(PeerMSP, PeerMSP)),
                                                        Admins=dict(Type="Signature", Rule="OR('{}.admin')".format(PeerMSP)),
                                                        Endorsement=dict(Type="Signature", Rule="OR('{}.peer')".format(PeerMSP)))
                                          ))
        Organizations = OrdererOrganizations + PeerOrganizations
        Capabilities = dict(
            Channel=ChannelCapabilities,
            Orderer=OrdererCapabilities,
            Application=ApplicationCapabilities
        )
        Application = deepcopy(ApplicationDefaults)
        Orderer = deepcopy(OrdererDefaults)
        Orderer["Addresses"] = deepcopy(OrdererAddress)
        Channel = deepcopy(ChannelDefaults)
        Application["Capabilities"] = Capabilities["Application"]
        Channel["Capabilities"] = Capabilities["Channel"]
        Orderer["Capabilities"] = Capabilities["Orderer"]
        Orderer["OrdererType"] = consensus
        Orderer["EtcdRaft"]["Consenters"] = deepcopy(Consenters)

        Profiles = {}
        Profiles[name] = deepcopy(Channel)
        Profiles[name]["Orderer"] = deepcopy(Orderer)
        Profiles[name]["Application"] = deepcopy(Application)
        Profiles[name]["Capabilities"] = Capabilities["Channel"]
        Profiles[name]["Orderer"]["Capabilities"] = Capabilities["Orderer"]
        Profiles[name]["Application"]["Capabilities"] = Capabilities["Application"]
        Profiles[name]["Orderer"]["Organizations"] = OrdererOrganizations
        Profiles[name]["Application"]["Organizations"] = PeerOrganizations

        configtx = dict(
            Organizations=Organizations,
            Capabilities=Capabilities,
            Application=Application,
            Orderer=Orderer,
            Channel=Channel,
            Profiles=Profiles
        )
        os.system('mkdir -p {}/{}'.format(self.filepath, self.network))

        with open('{}/{}/configtx.yaml'.format(self.filepath, self.network), 'w', encoding='utf-8') as f:
            yaml.dump(configtx, f, sort_keys=False)

    def createChannel(self, name, organizations):
        """create the channel.tx
                param:
                  name: name of channel
                  organizations: Organizations ready to join the channel
                return:
        """
        try:
            with open('{}/{}/{}'.format(self.filepath, self.network, "configtx.yaml"), 'r+', encoding='utf-8') as f:
                configtx = yaml.load(f, Loader=yaml.FullLoader)
                Profiles = configtx["Profiles"]
                Channel = configtx["Channel"]
                Orderer = configtx["Orderer"]
                Application = configtx["Application"]
                PeerOrganizations = []
                for org in configtx["Organizations"]:
                    for item in organizations:
                        if org["ID"] == item.capitalize() + "MSP":
                            PeerOrganizations.append(org)
                if PeerOrganizations == []:
                    raise Exception("can't find organnization")
                Profiles[name] = deepcopy(Channel)
                Profiles[name]["Orderer"] = Orderer
                Profiles[name]["Application"] = Application

            with open('{}/{}/{}'.format(self.filepath, self.network, "configtx.yaml"), 'w', encoding='utf-8') as f:
                yaml.safe_dump(configtx, f, sort_keys=False)

        except Exception as e:
            err_msg = "Configtx create channel failed for {}!".format(e)
            raise Exception(err_msg)


if __name__ == "__main__":
    orderers = [{"name": "org1.cello.com", "hosts": [{"name": "orderer1", "port": 8051}]}]
    # peers = [{"name": "org1.cello.com", "hosts": [{"name": "foo", "port": 7051},{"name": "car", "port": 7052}]},
    #         {"name": "org2.cello.com", "hosts": [{"name": "zoo", "port": 7053}]}]
    peers = [{"name": "org1.cello.com", "hosts": [{"name": "foo", "port": 7051}, {"name": "car", "port": 7052}]}]
    ConfigTX("test3").create(consensus="etcdraft", orderers=orderers, peers=peers)
    # tx = ConfigTX("test3")
    # print(tx.template)

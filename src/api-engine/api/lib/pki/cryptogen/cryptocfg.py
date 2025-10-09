#
# SPDX-License-Identifier: Apache-2.0
#
import yaml
import os
from api.config import CELLO_HOME


class CryptoConfig:
    """Class represents crypto-config yaml."""

    def __init__(
        self,
        name,
        file="crypto-config.yaml",
        country="CN",
        locality="BJ",
        province="CP",
        enablenodeous=True,
        filepath=CELLO_HOME,
    ):
        """init CryptoConfig
        param:
            name: organization's name
            file: crypto-config.yaml
            country: country
            locality: locality
            province: province
            enablenodeous: enablenodeous
            filepath: cello's working directory
        return:
        """
        self.filepath = filepath
        self.name = name
        self.country = country
        self.locality = locality
        self.province = province
        self.enablenodeous = enablenodeous
        self.file = file

    def create(self, peernum, orderernum) -> None:
        """create the crypto-config.yaml
        param
        return:
        """
        try:
            network = {}
            for item in ["Peer", "Orderer"]:
                org = []
                ca = dict(
                    Country=self.country,
                    Locality=self.locality,
                    Province=self.province,
                )
                specs = []
                # for host in org_info["Specs"]:
                #     specs.append(dict(Hostname=host))

                if item == "Peer":
                    template = dict(Count=peernum)
                    users = dict(Count=1)
                    org.append(
                        dict(
                            Domain=self.name,
                            Name=self.name.split(".")[0].capitalize(),
                            CA=ca,
                            Specs=specs,
                            EnableNodeOUs=self.enablenodeous,
                            Template=template,
                            Users=users,
                        )
                    )
                    network = {"PeerOrgs": org}
                else:
                    template = dict(Count=orderernum)
                    org.append(
                        dict(
                            Domain=self.name.split(".", 1)[1],
                            Name=item,
                            CA=ca,
                            Specs=specs,
                            EnableNodeOUs=self.enablenodeous,
                            Template=template,
                        )
                    )
                    network["OrdererOrgs"] = org

            os.system("mkdir -p {}/{}".format(self.filepath, self.name))

            with open(
                "{}/{}/{}".format(self.filepath, self.name, self.file),
                "w",
                encoding="utf-8",
            ) as f:
                yaml.dump(network, f)
        except Exception as e:
            err_msg = "CryptoConfig create failed for {}!".format(e)
            raise Exception(err_msg)

    def update(self, org_info: any) -> None:
        """update the crypto-config.yaml
        param:
            org_info: Node of type peer or orderer
        return:
        """
        try:
            with open(
                "{}/{}/{}".format(self.filepath, self.name, self.file),
                "r+",
                encoding="utf-8",
            ) as f:
                network = yaml.load(f, Loader=yaml.FullLoader)
                if org_info["type"] == "peer":
                    orgs = network["PeerOrgs"]
                else:
                    orgs = network["OrdererOrgs"]

                for org in orgs:
                    # org["Template"]["Count"] += 1
                    specs = org["Specs"]
                    for host in org_info["Specs"]:
                        specs.append(dict(Hostname=host))

            with open(
                "{}/{}/{}".format(self.filepath, self.name, self.file),
                "w",
                encoding="utf-8",
            ) as f:
                yaml.dump(network, f)
        except Exception as e:
            err_msg = "CryptoConfig update failed for {}!".format(e)
            raise Exception(err_msg)

    def delete(self):
        """delete the crypto-config.yaml
        param:
        return:
        """
        try:
            os.system("rm -rf {}/{}".format(self.filepath, self.name))
        except Exception as e:
            err_msg = "CryptoConfig delete failed for {}!".format(e)
            raise Exception(err_msg)

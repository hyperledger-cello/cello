#
# SPDX-License-Identifier: Apache-2.0
#
import yaml
import os

from api_engine.settings import CELLO_HOME


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

    def create(self) -> None:
        """create the crypto-config.yaml
        param
        return:
        """
        try:
            org_filepath = os.path.join(self.filepath, self.name)
            os.makedirs(org_filepath, exist_ok=True)

            with open(
                    os.path.join(org_filepath, self.file),
                    "w",
                    encoding="utf-8",
            ) as f:
                yaml.dump({
                    "PeerOrgs": [dict(
                        Domain=self.name,
                        Name=self.name.split(".")[0].capitalize(),
                        CA=dict(
                            Country=self.country,
                            Locality=self.locality,
                            Province=self.province,
                        ),
                        Specs=[],
                        EnableNodeOUs=self.enablenodeous,
                        Template=dict(Count=0),
                        Users=dict(Count=1),
                    )],
                    "OrdererOrgs": [dict(
                        Domain=self.name.split(".", 1)[1],
                        Name="Orderer",
                        CA=dict(
                            Country=self.country,
                            Locality=self.locality,
                            Province=self.province,
                        ),
                        Specs=[],
                        EnableNodeOUs=self.enablenodeous,
                        Template=dict(Count=0),
                    )]
                }, f)
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
                if org_info["type"].lower() == "peer":
                    orgs = network["PeerOrgs"]
                else:
                    orgs = network["OrdererOrgs"]

                for org in orgs:
                    # org["Template"]["Count"] += 1
                    specs = org["Specs"]
                    for host in org_info["Specs"]:
                        host_exists = False
                        for spec in specs:
                            if spec["Hostname"] == host:
                                host_exists = True
                                break
                        if not host_exists:
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

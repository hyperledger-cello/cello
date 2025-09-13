import yaml


def create():
    template = _load()
    default_orderer = template["Orderer"]
    default_channel = template["Channel"]
    default_application = template["Application"]
    default_channel_capabilities = template["Capabilities"]["Channel"]
    default_orderer_capabilities = template["Capabilities"]["Orderer"]
    default_application_capabilities = template["Capabilities"]["Application"]


def _load():
    with open("/opt/config/configtx.yaml", "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


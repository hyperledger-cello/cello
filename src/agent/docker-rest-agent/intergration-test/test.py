from requests import put, get, post
import base64
import docker
import json

client = docker.from_env()

with open("msp.zip", "rb") as node_msp, open("tls.zip", "rb") as tls, open(
    "block.zip", "rb"
) as block, open("peer_config.zip", "rb") as peer_config, open(
    "orderer_config.zip", "rb"
) as orderer_config:
    data = {
        "msp": base64.b64encode(node_msp.read()),
        "tls": base64.b64encode(tls.read()),
        "bootstrap_block": base64.b64encode(block.read()),
        "peer_config_file": base64.b64encode(peer_config.read()),
        "orderer_config_file": base64.b64encode(orderer_config.read()),
        "img": "hyperledger/cello-hlf:2.2.0",
        "cmd": 'bash /tmp/init.sh "peer node start"',
        "name": "cello-hlf-peer",
    }
print("-" * 20)
print("Test creating a node")
print()
n = post("http://localhost:5001/api/v1/nodes", data=data)
print(n.text)
txt = json.loads(n.text)
nid = txt["data"]["id"]
print("-" * 20)

print("Test starting a node")
print()
data = {"action": "start"}
response = post("http://localhost:5001/api/v1/nodes/" + nid, data=data)
print(response.text)
print("-" * 20)

print("Test restarting a node")
print()
data = {"action": "restart"}
response = post("http://localhost:5001/api/v1/nodes/" + nid, data=data)
print(response.text)
print("-" * 20)


print("Test updating a node")
print()
# TODO(dixing): use different commands & configuration files
with open("msp.zip", "rb") as node_msp, open("tls.zip", "rb") as tls, open(
    "block.zip", "rb"
) as block, open("peer_config.zip", "rb") as peer_config, open(
    "orderer_config.zip", "rb"
) as orderer_config:
    data = {
        "action": "update",
        "msp": base64.b64encode(node_msp.read()),
        "tls": base64.b64encode(tls.read()),
        "bootstrap_block": base64.b64encode(block.read()),
        "peer_config_file": base64.b64encode(peer_config.read()),
        "orderer_config_file": base64.b64encode(orderer_config.read()),
        "cmd": 'bash /tmp/update.sh "peer node start"',
    }
response = post("http://localhost:5001/api/v1/nodes/" + nid, data=data)
print(response.text)
print("-" * 20)

print("Test stopping a node")
print()
data = {"action": "stop"}
response = post("http://localhost:5001/api/v1/nodes/" + nid, data=data)
print(response.text)
print("-" * 20)


print("Get status of a node")
print()
response = get("http://localhost:5001/api/v1/nodes/" + nid)
print(response.text)
print("-" * 20)

print("Test deleting a node")
print()
data = {"action": "delete"}
response = post("http://localhost:5001/api/v1/nodes/" + nid, data=data)
print(response.text)

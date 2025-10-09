from flask import Flask, jsonify, request
import docker
import sys
import logging
import os
import ast

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
PASS_CODE = "OK"
FAIL_CODE = "Fail"

docker_url = os.getenv("DOCKER_URL")
storage_path = os.getenv("STORAGE_PATH")

client = docker.DockerClient(docker_url)
res = {"code": "", "data": {}, "msg": ""}


@app.route("/api/v1/networks", methods=["GET"])
def get_network():
    container_list = client.containers.list()
    containers = {}
    for container in container_list:
        containers[container.id] = {
            "id": container.id,
            "short_id": container.short_id,
            "name": container.name,
            "status": container.status,
            "image": str(container.image),
            "attrs": container.attrs,
        }
    res = {"code": PASS_CODE, "data": containers, "msg": ""}
    return jsonify({"res": res})


@app.route("/api/v1/nodes", methods=["POST"])
def create_node():
    node_name = request.form.get("name")
    env = {
        "HLF_NODE_MSP": request.form.get("msp"),
        "HLF_NODE_TLS": request.form.get("tls"),
        "HLF_NODE_PEER_CONFIG": request.form.get("peer_config_file"),
        "HLF_NODE_ORDERER_CONFIG": request.form.get("orderer_config_file"),
        "platform": "linux/amd64",
    }
    port_map = ast.literal_eval(request.form.get("port_map"))
    volumes = [
        "{}/fabric/{}:/etc/hyperledger/fabric".format(storage_path, node_name),
        "{}/production/{}:/var/hyperledger/production".format(
            storage_path, node_name
        ),
        "/var/run/docker.sock:/host/var/run/docker.sock",
    ]
    if request.form.get("type") == "peer":
        peer_envs = {
            "CORE_VM_ENDPOINT": "unix:///host/var/run/docker.sock",
            "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE": "cello-net",
            "FABRIC_LOGGING_SPEC": "INFO",
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_PROFILE_ENABLED": "false",
            "CORE_PEER_TLS_CERT_FILE": "/etc/hyperledger/fabric/tls/server.crt",
            "CORE_PEER_TLS_KEY_FILE": "/etc/hyperledger/fabric/tls/server.key",
            "CORE_PEER_TLS_ROOTCERT_FILE": "/etc/hyperledger/fabric/tls/ca.crt",
            "CORE_PEER_ID": node_name,
            "CORE_PEER_ADDRESS": node_name + ":7051",
            "CORE_PEER_LISTENADDRESS": "0.0.0.0:7051",
            "CORE_PEER_CHAINCODEADDRESS": node_name + ":7052",
            "CORE_PEER_CHAINCODELISTENADDRESS": "0.0.0.0:7052",
            "CORE_PEER_GOSSIP_BOOTSTRAP": node_name + ":7051",
            "CORE_PEER_GOSSIP_EXTERNALENDPOINT": node_name + ":7051",
            "CORE_PEER_LOCALMSPID": node_name.split(".")[1].capitalize()
            + "MSP",
            "CORE_PEER_MSPCONFIGPATH": "/etc/hyperledger/fabric/msp",
            "CORE_OPERATIONS_LISTENADDRESS": node_name + ":9444",
            "CORE_METRICS_PROVIDER": "prometheus",
        }
        env.update(peer_envs)
    else:
        order_envs = {
            "FABRIC_LOGGING_SPEC": "INFO",
            "ORDERER_GENERAL_LISTENADDRESS": "0.0.0.0",
            "ORDERER_GENERAL_LISTENPORT": "7050",
            "ORDERER_GENERAL_LOCALMSPID": "OrdererMSP",
            "ORDERER_GENERAL_LOCALMSPDIR": "/etc/hyperledger/fabric/msp",
            "ORDERER_GENERAL_TLS_ENABLED": "true",
            "ORDERER_GENERAL_TLS_PRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
            "ORDERER_GENERAL_TLS_CERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
            "ORDERER_GENERAL_TLS_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
            "ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
            "ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
            "ORDERER_GENERAL_CLUSTER_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
            "ORDERER_GENERAL_BOOTSTRAPMETHOD": "none",
            "ORDERER_CHANNELPARTICIPATION_ENABLED": "true",
            "ORDERER_ADMIN_TLS_ENABLED": "true",
            "ORDERER_ADMIN_TLS_CERTIFICATE": "/etc/hyperledger/fabric/tls/server.crt",
            "ORDERER_ADMIN_TLS_PRIVATEKEY": "/etc/hyperledger/fabric/tls/server.key",
            "ORDERER_ADMIN_TLS_ROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
            "ORDERER_ADMIN_TLS_CLIENTROOTCAS": "[/etc/hyperledger/fabric/tls/ca.crt]",
            "ORDERER_ADMIN_LISTENADDRESS": "0.0.0.0:7053",
            "ORDERER_OPERATIONS_LISTENADDRESS": node_name + ":9443",
            "ORDERER_METRICS_PROVIDER": "prometheus",
        }
        env.update(order_envs)
    try:
        # same as `docker run -dit yeasy/hyperledge-fabric:2.2.0 -e VARIABLES``
        container = client.containers.run(
            request.form.get("img"),
            request.form.get("cmd"),
            detach=True,
            tty=True,
            stdin_open=True,
            network="cello-net",
            name=request.form.get("name"),
            dns_search=["."],
            volumes=volumes,
            environment=env,
            ports=port_map,
        )
    except:
        res["code"] = FAIL_CODE
        res["data"] = sys.exc_info()[0]
        res["msg"] = "creation failed"
        logging.error(res)
        raise

    res["code"] = PASS_CODE
    res["data"]["status"] = "created"
    res["data"]["id"] = container.id
    res["data"][
        "public-grpc"
    ] = "127.0.0.1:7050"  # TODO: read the info from config file
    res["data"]["public-raft"] = "127.0.0.1:7052"
    res["msg"] = "node created"

    return jsonify(res)


@app.route("/api/v1/nodes/<id>", methods=["GET", "POST"])
def operate_node(id):
    container = client.containers.get(id)
    if request.method == "POST":
        act = request.form.get("action")  # only with POST

        try:
            if act == "start":
                container.start()
                res["msg"] = "node started"
            elif act == "restart":
                container.restart()
                res["msg"] = "node restarted"
            elif act == "stop":
                container.stop()
                res["msg"] = "node stopped"
            elif act == "delete":
                container.remove()
                res["msg"] = "node deleted"
            elif act == "update":

                env = {}

                if "msp" in request.form:
                    env["HLF_NODE_MSP"] = request.form.get("msp")

                if "tls" in request.form:
                    env["HLF_NODE_TLS"] = request.form.get("tls")

                if "bootstrap_block" in request.form:
                    env["HLF_NODE_BOOTSTRAP_BLOCK"] = request.form.get(
                        "bootstrap_block"
                    )

                if "peer_config_file" in request.form:
                    env["HLF_NODE_PEER_CONFIG"] = request.form.get(
                        "peer_config_file"
                    )

                if "orderer_config_file" in request.form:
                    env["HLF_NODE_ORDERER_CONFIG"] = request.form.get(
                        "orderer_config_file"
                    )

                container.exec_run(
                    request.form.get("cmd"),
                    detach=True,
                    tty=True,
                    stdin=True,
                    environment=env,
                )
                container.restart()
                res["msg"] = "node updated"

            else:
                res["msg"] = "undefined action"
        except:
            res["code"] = FAIL_CODE
            res["data"] = sys.exc_info()[0]
            res["msg"] = act + "failed"
            logging.error(res)
            raise
    else:
        # GET
        res["data"]["status"] = container.status

    res["code"] = PASS_CODE
    return jsonify(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

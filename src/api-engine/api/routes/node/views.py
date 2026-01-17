#
# SPDX-License-Identifier: Apache-2.0
#
import logging
import base64
import shutil
import os
import threading
import yaml

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from api.common.enums import AgentOperation
from api.exceptions import (
    CustomError,
    NoResource,
    ResourceExists,
    ResourceInUse,
)
from api.exceptions import ResourceNotFound
from api.models import (
    Node,
    Port,
    FabricCA,
    FabricCAServerType,
    NodeUser,
    FabricPeer,
    PeerCa,
    PeerCaUser,
)
from api.routes.node.serializers import (
    NodeOperationSerializer,
    NodeQuery,
    NodeCreateBody,
    NodeIDSerializer,
    NodeListSerializer,
    NodeUpdateBody,
    # NodeFileCreateSerializer,
    # NodeInfoSerializer,
    NodeStatusSerializer,
    NodeUserCreateSerializer,
    NodeUserIDSerializer,
    NodeUserPatchSerializer,
    NodeUserQuerySerializer,
    NodeUserListSerializer,
    NodeConfigFileSerializer,
)
from api.utils.common import with_common_response
from api.lib.pki import CryptoGen, CryptoConfig
from api.utils import zip_dir, zip_file
from api.config import CELLO_HOME, FABRIC_NODE, PRODUCTION_NODE
from api.utils.node_config import NodeConfig
from api.lib.agent import AgentHandler
from api.lib.peer.channel import Channel as PeerChannel
from api.utils.port_picker import set_ports_mapping, find_available_ports
from api.common import ok, err
from api.routes.channel.views import init_env_vars

LOG = logging.getLogger(__name__)


class NodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # Only operator can update node info
    # def get_permissions(self):
    #     if self.action in ["update"]:
    #         permission_classes = (IsAuthenticated, IsOperatorAuthenticated)
    #     else:
    #         permission_classes = (IsAuthenticated,)
    #
    #     return [permission() for permission in permission_classes]

    @staticmethod
    def _validate_organization(request):
        if request.user.organization is None:
            raise CustomError(detail="Need join in organization.")

    @swagger_auto_schema(
        query_serializer=NodeQuery,
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: NodeListSerializer})
        ),
    )
    def list(self, request, *args, **kwargs):
        """
        List node

        :param request: query parameter
        :return: node list
        :rtype: list
        """
        try:
            serializer = NodeQuery(data=request.GET)
            if serializer.is_valid(raise_exception=True):
                page = serializer.validated_data.get("page")
                per_page = serializer.validated_data.get("per_page")
                node_type = serializer.validated_data.get("type")
                name = serializer.validated_data.get("name")
                agent_id = serializer.validated_data.get("agent_id")

                # if agent_id is not None and not request.user.is_operator:
                #     raise PermissionDenied
                query_filter = {}

                if node_type:
                    query_filter.update({"type": node_type})
                if name:
                    query_filter.update({"name__icontains": name})
                if request.user.is_admin:
                    query_filter.update(
                        {"organization": request.user.organization}
                    )
                # elif request.user.is_common_user:
                #     query_filter.update({"user": request.user})
                if agent_id:
                    query_filter.update({"agent__id": agent_id})
                nodes = Node.objects.filter(**query_filter)
                p = Paginator(nodes, per_page)
                nodes = p.page(page)
                response = NodeListSerializer(
                    {"total": p.count, "data": nodes}
                )
                return Response(
                    data=ok(response.data), status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    def _save_fabric_ca(self, request, ca=None):
        if ca is None:
            return None

        ca_body = {}
        admin_name = ca.get("admin_name")
        admin_password = ca.get("admin_password")
        # If found tls type ca server under this organization,
        # will cause resource exists error
        ca_server_type = ca.get("type", FabricCAServerType.Signature.value)
        if ca_server_type == FabricCAServerType.TLS.value:
            exist_ca_server = Node.objects.filter(
                organization=request.user.organization,
                ca__type=FabricCAServerType.TLS.value,
            ).count()
            if exist_ca_server > 0:
                raise ResourceExists("CA Exists")
        hosts = ca.get("hosts", [])
        if admin_name:
            ca_body.update({"admin_name": admin_name})
        if admin_password:
            ca_body.update({"admin_password": admin_password})
        fabric_ca = FabricCA(**ca_body, hosts=hosts, type=ca_server_type)
        fabric_ca.save()

        return fabric_ca

    def _save_fabric_peer(self, request, peer=None):
        if peer is None:
            return None
        name = peer.get("name")
        gossip_use_leader_reflection = peer.get("gossip_use_leader_reflection")
        gossip_org_leader = peer.get("gossip_org_leader")
        gossip_skip_handshake = peer.get("gossip_skip_handshake")
        local_msp_id = peer.get("local_msp_id")
        ca_nodes = peer.get("ca_nodes")

        body = {"name": name, "local_msp_id": local_msp_id}
        if gossip_use_leader_reflection is not None:
            body.update(
                {"gossip_use_leader_reflection": gossip_use_leader_reflection}
            )
        if gossip_org_leader is not None:
            body.update({"gossip_org_leader": gossip_org_leader})
        if gossip_skip_handshake is not None:
            body.update({"gossip_skip_handshake": gossip_skip_handshake})

        fabric_peer = FabricPeer(**body)
        fabric_peer.save()

        ca_nodes_list = []
        for ca_node in ca_nodes:
            node = ca_node.get("node")
            address = ca_node.get("address")
            certificate = ca_node.get("certificate")
            ca_type = ca_node.get("type")

            ca_body = {"peer": fabric_peer}
            ca_node_dict = {}
            if node is not None:
                ca_body.update({"node": node})
                port = Port.objects.filter(node=node, internal=7054).first()
                if port:
                    ca_node_dict.update(
                        {"address": "%s:%s" % (node.agent.ip, port.external)}
                    )
                ca_node_dict.update(
                    {
                        "type": node.ca.type,
                        "certificate": request.build_absolute_uri(
                            node.file.url
                        ),
                    }
                )
            else:
                update_body = {
                    "address": address,
                    "certificate": certificate,
                    "type": ca_type,
                }
                ca_body.update(update_body)
                ca_node_dict.update(update_body)

            peer_ca = PeerCa(**ca_body)
            peer_ca.save()
            users = ca_node.get("users")

            user_list = []
            for ca_user in users:
                ca_user_body = {"peer_ca": peer_ca}
                user_dict = {}
                user = ca_user.get("user")
                username = ca_user.get("username")
                password = ca_user.get("password")
                user_type = ca_user.get("type")

                if user is not None:
                    ca_user_body.update({"user": user})
                    user_dict.update(
                        {
                            "username": user.name,
                            "password": user.secret,
                            "type": user.user_type,
                        }
                    )
                else:
                    update_body = {
                        "username": username,
                        "password": password,
                        "type": user_type,
                    }
                    ca_user_body.update(update_body)
                    user_dict.update(update_body)
                user_list.append(user_dict)

                ca_user_obj = PeerCaUser(**ca_user_body)
                ca_user_obj.save()

            ca_node_dict.update({"users": user_list})

            ca_nodes_list.append(ca_node_dict)

        return fabric_peer, ca_nodes_list

    @swagger_auto_schema(
        request_body=NodeCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: NodeIDSerializer}
        ),
    )
    def create(self, request):
        """
        Create Node

        :param request: create parameter
        :return: node ID
        :rtype: uuid
        """
        try:
            serializer = NodeCreateBody(data=request.data)
            if serializer.is_valid(raise_exception=True):
                node_name = serializer.validated_data.get("name")
                node_type = serializer.validated_data.get("type")
                organization = request.user.organization

                agent = organization.agent.get()
                if agent:
                    nodes = Node.objects.filter(
                        name=node_name,
                        organization=organization,
                        type=node_type,
                    )
                    if nodes:
                        raise ResourceExists("Node Exists")
                else:
                    raise NoResource("Node Does Not Exist")
                urls = "{}.{}".format(node_name, organization.name)
                nodes = {"type": node_type, "Specs": [node_name]}
                CryptoConfig(organization.name).update(nodes)
                CryptoGen(organization.name).extend()
                self._generate_config(node_type, organization.name, node_name)
                msp, tls, cfg = self._conversion_msp_tls_cfg(
                    node_type, organization.name, node_name
                )
                node = Node(
                    name=node_name,
                    organization=organization,
                    urls=urls,
                    type=node_type,
                    msp=msp,
                    tls=tls,
                    agent=agent,
                    config_file=cfg,
                )
                node.save()

                self._set_port(node_type, node, agent)
                if node.organization.network:
                    try:
                        threading.Thread(
                            target=self._start_node, args=(node.id,)
                        ).start()
                    except Exception as e:
                        LOG.exception("Thread Failed")
                        raise e

                response = NodeIDSerializer(data=node.__dict__)
                if response.is_valid(raise_exception=True):
                    return Response(
                        ok(response.validated_data),
                        status=status.HTTP_201_CREATED,
                    )
        except (ResourceExists, NoResource) as e:
            raise e
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    def _set_port(self, type, node, agent):
        """
        get free port from agent,

        :param type: node type
        :param node: node obj
        :param agent: agent obj
        :return: none
        :rtype: none
        """
        ip = agent.urls.split(":")[1].strip("//")

        if type == "peer":
            ports = find_available_ports(ip, node.id, agent.id, 2)
            set_ports_mapping(
                node.id,
                [
                    {"internal": 7051, "external": ports[0]},
                    {"internal": 9444, "external": ports[1]},
                ],
                True,
            )
        else:
            # unify the port mapping for orderer
            ports = find_available_ports(ip, node.id, agent.id, 3)
            set_ports_mapping(
                node.id,
                [
                    {"internal": 7050, "external": ports[0]},
                    {"internal": 7053, "external": ports[1]},
                    {"internal": 9443, "external": ports[2]},
                ],
                True,
            )

    def _conversion_msp_tls_cfg(self, type, org, node):
        """
        msp and tls , cfg from zip file to byte

        :param org: organization name
        :param type: node type
        :param node: node name
        :return: msp, tls, cfg
        :rtype: bytes
        """
        try:
            if type == "peer":
                dir_node = "{}/{}/crypto-config/peerOrganizations/{}/peers/{}/".format(
                    CELLO_HOME, org, org, node + "." + org
                )
                name = "core.yaml"
                cname = "peer_config.zip"
            else:
                dir_node = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}/".format(
                    CELLO_HOME,
                    org,
                    org.split(".", 1)[1],
                    node + "." + org.split(".", 1)[1],
                )
                name = "orderer.yaml"
                cname = "orderer_config.zip"

            zip_dir("{}msp".format(dir_node), "{}msp.zip".format(dir_node))
            with open("{}msp.zip".format(dir_node), "rb") as f_msp:
                msp = base64.b64encode(f_msp.read())

            zip_dir("{}tls".format(dir_node), "{}tls.zip".format(dir_node))
            with open("{}tls.zip".format(dir_node), "rb") as f_tls:
                tls = base64.b64encode(f_tls.read())

            zip_file(
                "{}{}".format(dir_node, name), "{}{}".format(dir_node, cname)
            )
            with open("{}{}".format(dir_node, cname), "rb") as f_cfg:
                cfg = base64.b64encode(f_cfg.read())
        except Exception as e:
            LOG.exception("Failed Conversion: CFG From Zip To Byte")
            raise e

        return msp, tls, cfg

    def _generate_config(self, type, org, node):
        """
        generate config for node (core.yaml, orderer.yaml)

        :param org: organization name
        :param type: node type
        :param node: node name
        :param port: node port(todo: automatic distribution port)
        :return: none
        :rtype: none
        """
        args = {}
        if type == "peer":
            args.update({"peer_tls_enabled": True})
            args.update(
                {"operations_listenAddress": node + "." + org + ":9444"}
            )
            args.update({"peer_address": node + "." + org + ":7051"})
            args.update({"peer_gossip_bootstrap": node + "." + org + ":7051"})
            args.update(
                {"peer_gossip_externalEndpoint": node + "." + org + ":7051"}
            )
            args.update({"peer_id": node + "." + org})
            args.update({"peer_localMspId": org.capitalize() + "MSP"})
            args.update({"peer_mspConfigPath": "/etc/hyperledger/fabric/msp"})
            args.update(
                {
                    "peer_tls_cert_file": "/etc/hyperledger/fabric/tls/server.crt"
                }
            )
            args.update(
                {"peer_tls_key_file": "/etc/hyperledger/fabric/tls/server.key"}
            )
            args.update(
                {
                    "peer_tls_rootcert_file": "/etc/hyperledger/fabric/tls/ca.crt"
                }
            )
            args.update({"vm_docker_hostConfig_NetworkMode": "cello_net"})
            args.update({"vm_endpoint": "unix:///host/var/run/docker.sock"})

            a = NodeConfig(org)
            a.peer(node, **args)
        else:
            args.update({"Admin_TLS_Enabled": True})
            args.update({"Admin_ListenAddress": "0.0.0.0:7053"})
            args.update(
                {
                    "Admin_TLS_Certificate": "/etc/hyperledger/fabric/tls/server.crt"
                }
            )
            args.update(
                {
                    "Admin_TLS_PrivateKey": "/etc/hyperledger/fabric/tls/server.key"
                }
            )
            args.update({"ChannelParticipation_Enabled": True})
            args.update(
                {
                    "General_Cluster_ClientCertificate": "/etc/hyperledger/fabric/tls/server.crt"
                }
            )
            args.update(
                {
                    "General_Cluster_ClientPrivateKey": "/etc/hyperledger/fabric/tls/server.key"
                }
            )
            args.update({"General_ListenAddress": "0.0.0.0"})
            args.update({"General_ListenPort": 7050})
            args.update({"General_LocalMSPID": "OrdererMSP"})
            args.update({"General_LocalMSPDir": "/etc/hyperledger/fabric/msp"})
            args.update({"General_TLS_Enabled": True})
            args.update(
                {
                    "General_TLS_Certificate": "/etc/hyperledger/fabric/tls/server.crt"
                }
            )
            args.update(
                {
                    "General_TLS_PrivateKey": "/etc/hyperledger/fabric/tls/server.key"
                }
            )
            args.update(
                {"General_TLS_RootCAs": "[/etc/hyperledger/fabric/tls/ca.crt]"}
            )
            args.update({"General_BootstrapMethod": "none"})
            args.update({"Metrics_Provider": "prometheus"})
            args.update(
                {
                    "Operations_ListenAddress": node
                    + "."
                    + org.split(".", 1)[1]
                    + ":9443"
                }
            )

            a = NodeConfig(org)
            a.orderer(node, **args)
        pass

    def _agent_params(self, pk):
        """
        get node's params from db
        :param node: node id
        :return: info
        """
        try:
            node = Node.objects.get(id=pk)
            org = node.organization
            if org is None:
                raise ResourceNotFound("Organization Not Found")
            network = org.network
            agent = org.agent.get()
            if agent is None:
                raise ResourceNotFound("Agent Not Found")
            ports = Port.objects.filter(node=node)
            if ports is None:
                raise ResourceNotFound("Port Not Found")

            info = {}
            org_name = (
                org.name if node.type == "peer" else org.name.split(".", 1)[1]
            )
            # get info of node, e.g, tls, msp, config.
            info["status"] = node.status
            info["msp"] = node.msp
            info["tls"] = node.tls
            info["config_file"] = node.config_file
            info["type"] = node.type
            info["name"] = "{}.{}".format(node.name, org_name)
            info["urls"] = agent.urls
            info["network_type"] = None if network is None else network.type
            info["agent_type"] = agent.type
            info["container_name"] = "{}.{}".format(node.name, org_name)
            info["ports"] = ports
            return info
        except Exception as e:
            LOG.exception("Failed To Get Node Params")
            raise e

    def _start_node(self, pk):
        """
        start node from agent
        :param node: node id
        :return: null
        """
        try:
            node_qs = Node.objects.filter(id=pk)
            infos = self._agent_params(pk)
            agent = AgentHandler(infos)
            cid = agent.create(infos)
            if cid:
                node_qs.update(cid=cid, status="running")
            else:
                raise ResourceNotFound("Node Not Found")
        except Exception as e:
            LOG.exception("Could Not Start Node")
            raise e

    @swagger_auto_schema(
        methods=["post"],
        request_body=NodeOperationSerializer,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    @action(methods=["post"], detail=True, url_path="operations")
    def operate(self, request, pk=None):
        """
        Operate Node

        Do some operation on node, start/stop/restart
        """
        try:
            serializer = NodeOperationSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                action = serializer.validated_data.get("action")
                infos = self._agent_params(pk)
                agent = AgentHandler(infos)
                node_qs = Node.objects.filter(id=pk)
                node_status = infos.get("status")

                if action == "start" and node_status == "paused":
                    node_qs.update(status="restarting")
                    res = True if agent.start() else False
                    if res:
                        node_qs.update(status="running")
                    return Response(
                        ok({"restart": res}), status=status.HTTP_201_CREATED
                    )
                elif action == "stop" and node_status == "running":
                    res = True if agent.stop() else False
                    if res:
                        node_qs.update(status="paused")
                    return Response(
                        ok({"stop": res}), status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        ok({"error": "invalid operation"}),
                        status=status.HTTP_201_CREATED,
                    )
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request, pk=None):
        """
        Delete Node

        :param request: destory parameter
        :param pk: primary key
        :return: none
        :rtype: rest_framework.status
        """
        try:
            node = Node.objects.get(id=pk)
            infos = self._agent_params(pk)
            agent = AgentHandler(infos)
            agent_exist = agent.get()
            node.status = "removing"
            node.save()
            if node.type == "orderer" and node.organization.network is not None:
                orderer_cnt = Node.objects.filter(
                    type="orderer", organization__network=node.organization.network).count()
                if orderer_cnt == 1:
                    raise ResourceInUse("Orderer In Use")
            res = False
            # if agent not exist or no continer is created for node, do not try to stop/delete container
            if not agent_exist or not node.cid:
                res = True
            else:
                # try to stop/delete container 3 times
                # TODO: optimize the retry logic
                for i in range(3):
                    LOG.info(
                        "Retry to stop/delete container %d time(s).", i + 1)
                    try:
                        response = agent.stop()
                        if response is not True:
                            LOG.error(
                                "Failed when agent stops/deletes container: %s", response)
                            continue
                        response = agent.delete()
                        if response is not True:
                            LOG.error(
                                "Failed when agent stops/deletes container: %s", response)
                            continue
                        res = True
                    except Exception as e:
                        LOG.error(
                            "Exception when agent stops/deletes container: %s", e)
                        continue
                    break
            if res:
                fabric_path = "{}/{}".format(FABRIC_NODE, infos["container_name"])
                if os.path.exists(fabric_path):
                    shutil.rmtree(fabric_path, True)
                prod_path = "{}/{}".format(PRODUCTION_NODE, infos["container_name"])
                if os.path.exists(prod_path):
                    shutil.rmtree(prod_path, True)
                node.delete()
                # node.status = "exited"
                # node.save()
            else:
                return Response(ok({"delete": False}), status=status.HTTP_202_ACCEPTED)
            return Response(ok({"delete": True}), status=status.HTTP_202_ACCEPTED)
        except ObjectDoesNotExist:
            raise ResourceNotFound("Node Not Found")
        except (ResourceNotFound, ResourceInUse) as e:
            raise e
        except Exception as e:
            LOG.exception("Node Not Deleted")
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_id="update node",
        request_body=NodeUpdateBody,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    def update(self, request, pk=None):
        """
        Update Node

        Update special node with id.
        """
        try:
            serializer = NodeUpdateBody(data=request.data)
            if serializer.is_valid(raise_exception=True):
                node_status = serializer.validated_data.get("status")
                ports = serializer.validated_data.get("ports", [])
                try:
                    node = Node.objects.get(id=pk)
                except ObjectDoesNotExist:
                    raise ResourceNotFound("Node Not Found")

                node.status = node_status
                node.save()

                for port_item in ports:
                    port = Port(
                        external=port_item.get("external"),
                        internal=port_item.get("internal"),
                        node=node,
                    )
                    port.save()

                return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(
    #     methods=["post"],
    #     request_body=NodeFileCreateSerializer,
    #     responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    # )
    # @action(methods=["post"], detail=True, url_path="files", url_name="files")
    # def upload_files(self, request, pk=None):
    #     """
    #     Upload file to node

    #     Upload related files to node
    #     """
    #     serializer = NodeFileCreateSerializer(data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         file = serializer.validated_data.get("file")
    #         try:
    #             node = Node.objects.get(id=pk)
    #         except ObjectDoesNotExist:
    #             raise ResourceNotFound
    #         else:
    #             # delete old file
    #             if node.file:
    #                 node.file.delete()
    #             node.file = file
    #             node.save()

    #     return Response(status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: NodeStatusSerializer})
        )
    )
    def retrieve(self, request, pk=None):
        """
        Get Node information

        Get node detail information.
        """
        try:
            self._validate_organization(request)
            try:
                node = Node.objects.get(
                    id=pk, organization=request.user.organization
                )
            except ObjectDoesNotExist:
                raise ResourceNotFound("Node Not Found")
            else:
                # Set file url of node, we only need node status for now
                # if node.file:
                #     node.file = request.build_absolute_uri(node.file.url)
                # ports = Port.objects.filter(node=node)
                # node.links = [
                #     {
                #         "internal_port": port.internal,
                #         "url": "%s:%s" % (node.agent.ip, port.external),
                #     }
                #     for port in ports
                # ]
                response = NodeStatusSerializer(node)
                return Response(
                    ok(data=response.data), status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        methods=["get"],
        responses=with_common_response(
            {status.HTTP_200_OK: NodeConfigFileSerializer}
        ),
    )
    @swagger_auto_schema(
        methods=["post"],
        request_body=NodeConfigFileSerializer,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    @action(
        methods=["get", "post"],
        detail=True,
        url_path="config",
        url_name="config",
    )
    def node_config(self, request, pk=None):
        """
        Download/upload the node config file
        """
        try:
            self._validate_organization(request)
            organization = request.user.organization
            org = organization.name
            try:
                node = Node.objects.get(id=pk, organization=organization)
            except ObjectDoesNotExist:
                raise ResourceNotFound("Node Not Found")
            # Get file locations based on node type
            if node.type == "peer":
                dir_node = "{}/{}/crypto-config/peerOrganizations/{}/peers/{}/".format(
                    CELLO_HOME, org, org, node.name + "." + org
                )
                cname = "peer_config.zip"
                name = "core.yaml"
            else:
                dir_node = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}/".format(
                    CELLO_HOME,
                    org,
                    org.split(".", 1)[1],
                    node.name + "." + org.split(".", 1)[1],
                )
                cname = "orderer_config.zip"
                name = "orderer.yaml"
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)
        if request.method == "GET":
            # Get the config file from local storage
            try:
                config_file = open("{}{}".format(dir_node, cname), "rb")
                response = HttpResponse(
                    config_file, content_type="application/zip"
                )
                response["Content-Disposition"] = (
                    "attachment; filename={}".format(cname)
                )
                return response
            except Exception as e:
                LOG.exception("Config File Not Found")
                raise e
        elif request.method == "POST":
            # Update yaml, zip files, and the database field
            try:
                new_config_file = request.data["file"]
                try:
                    yaml.safe_load(new_config_file)
                except yaml.YAMLError:
                    return Response(
                        err("Unable to parse this YAML file."),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if os.path.exists("{}{}".format(dir_node, name)):
                    os.remove("{}{}".format(dir_node, name))
                with open("{}{}".format(dir_node, name), "wb+") as f:
                    for chunk in new_config_file.chunks():
                        f.write(chunk)
                if os.path.exists("{}{}".format(dir_node, cname)):
                    os.remove("{}{}".format(dir_node, cname))
                zip_file(
                    "{}{}".format(dir_node, name),
                    "{}{}".format(dir_node, cname),
                )
                with open("{}{}".format(dir_node, cname), "rb") as f_cfg:
                    cfg = base64.b64encode(f_cfg.read())
                node.config_file = cfg
                node.save()
                infos = self._agent_params(pk)
                agent = AgentHandler(infos)
                agent.update_config(cfg, node.type)
                return Response(status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                LOG.exception("Update Failed")
                raise e

    @action(methods=["post"], detail=True, url_path="block", url_name="block")
    def block_file(self, request, pk=None):
        """
        Peer join channel by uploading a genesis block file
        """
        try:
            self._validate_organization(request)
            organization = request.user.organization
            org = organization.name
            try:
                node = Node.objects.get(id=pk, organization=organization)
            except ObjectDoesNotExist:
                raise ResourceNotFound("Node Not Found")
            envs = init_env_vars(node, organization)
            block_path = "{}/{}/crypto-config/peerOrganizations/{}/peers/{}/{}.block".format(
                CELLO_HOME, org, org, node.name + "." + org, "channel"
            )
            uploaded_block_file = request.data["file"]
            with open(block_path, "wb+") as f:
                for chunk in uploaded_block_file.chunks():
                    f.write(chunk)
            peer_channel_cli = PeerChannel(**envs)
            peer_channel_cli.join(block_path)
            os.remove(block_path)
            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

    def _list_user(self, request, pk=None):
        serializer = NodeUserQuerySerializer(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            page = serializer.validated_data.get("page")
            per_page = serializer.validated_data.get("per_page")
            name = serializer.validated_data.get("name")
            user_type = serializer.validated_data.get("user_type")
            user_status = serializer.validated_data.get("status")
            query_param = {"node__id": pk}
            if name is not None:
                query_param.update({"name__icontains": name})
            if user_type is not None:
                query_param.update({"user_type": user_type})
            if user_status is not None:
                query_param.update({"status": user_status})

            users = NodeUser.objects.filter(**query_param)
            p = Paginator(users, per_page)
            users = p.page(page)

            response = NodeUserListSerializer(
                {"data": users, "total": p.count}
            )
            return Response(ok(response.data), status=status.HTTP_200_OK)

    @swagger_auto_schema(
        methods=["get"],
        operation_description="List user of node",
        operation_summary="List user of node",
        query_serializer=NodeUserQuerySerializer,
        responses=with_common_response(
            {status.HTTP_200_OK: NodeUserListSerializer}
        ),
    )
    @action(
        methods=["post", "get"],
        detail=True,
        url_path="users",
        url_name="users",
    )
    def users(self, request, pk=None):
        return self._list_user(request, pk)

    @swagger_auto_schema(
        methods=["patch"],
        request_body=NodeUserPatchSerializer,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    @action(
        methods=["patch"],
        detail=True,
        url_path="users/(?P<user_pk>[^/.]+)",
        url_name="patch-user",
    )
    def patch_user(self, request, pk=None, user_pk=None):
        """
        Patch user status for node

        Patch user status for node
        """
        try:
            serializer = NodeUserPatchSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                try:
                    node_user = NodeUser.objects.get(id=user_pk, node__id=pk)
                except ObjectDoesNotExist:
                    raise ResourceNotFound("Node User Not Found")

                node_user.status = serializer.validated_data.get("status")
                node_user.save()

                return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            LOG.exception("Patch Failed")
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)

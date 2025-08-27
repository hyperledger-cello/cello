#
# SPDX-License-Identifier: Apache-2.0
#
import logging
import base64
import shutil
import os

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from api.exceptions import ResourceNotFound, ResourceExists
from api.routes.network.serializers import (
    NetworkQuery,
    NetworkListResponse,
    NetworkMemberResponse,
    NetworkCreateBody,
    NetworkIDSerializer,
)
from api.utils.common import with_common_response
from api.models import Network, Node, Port
from api.config import CELLO_HOME
from api.utils import zip_file
from api.lib.agent import AgentHandler
from api.common import ok, err
import threading

LOG = logging.getLogger(__name__)


class NetworkViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

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
                raise ResourceNotFound(detail="Organization Not Found")
            network = org.network
            if network is None:
                raise ResourceNotFound(detail="Network Not Found")
            agent = org.agent.get()
            if agent is None:
                raise ResourceNotFound(detail="Agent Not Found")
            ports = Port.objects.filter(node=node)
            if ports is None:
                raise ResourceNotFound(detail="Port Not Found")

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
            info["network_type"] = network.type
            info["agent_type"] = agent.type
            info["ports"] = ports
            return info
        except Exception as e:
            LOG.exception("Could Not Get Params")
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
                raise ResourceNotFound(detail="Container Not Built")
        except Exception as e:
            LOG.exception("Node Not Started")
            raise e

    @swagger_auto_schema(
        request_body=NetworkCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: NetworkIDSerializer}
        ),
    )
    def create(self, request):
        """
        Create Network
        :param request: create parameter
        :return: organization ID
        :rtype: uuid
        """
        try:
            serializer = NetworkCreateBody(data=request.data)
            if serializer.is_valid(raise_exception=True):
                name = serializer.validated_data.get("name")
                consensus = serializer.validated_data.get("consensus")
                database = serializer.validated_data.get("database")

                try:
                    if Network.objects.get(name=name):
                        raise ResourceExists(detail="Network exists")
                except ObjectDoesNotExist:
                    pass
                org = request.user.organization
                if org.network:
                    raise ResourceExists(
                        detail="Network exists for the organization"
                    )

                network = Network(
                    name=name, consensus=consensus, database=database
                )
                network.save()
                org.network = network
                org.save()
                nodes = Node.objects.filter(organization=org)
                for node in nodes:
                    try:
                        threading.Thread(
                            target=self._start_node, args=(node.id,)
                        ).start()
                    except Exception as e:
                        LOG.exception("Network Not Created")
                        raise e

                response = NetworkIDSerializer(data=network.__dict__)
                if response.is_valid(raise_exception=True):
                    return Response(
                        ok(response.validated_data),
                        status=status.HTTP_201_CREATED,
                    )
        except ResourceExists as e:
            LOG.exception("Network Exists")
            raise e
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_202_ACCEPTED: "No Content"}
        )
    )
    def destroy(self, request, pk=None):
        """
        Delete Network
        :param request: destory parameter
        :param pk: primary key
        :return: none
        :rtype: rest_framework.status
        """
        try:
            network = Network.objects.get(pk=pk)
            path = "{}/{}".format(CELLO_HOME, network.name)
            if os.path.exists(path):
                shutil.rmtree(path, True)
            network.delete()
            return Response(ok(None), status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)


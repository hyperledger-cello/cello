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
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator

from api.utils.common import with_common_response
from api.exceptions import ResourceExists, ResourceNotFound, ResourceInUse
from api.models import (
    Node,
    Organization,
)
from api.routes.organization.serializers import (
    OrganizationQuery,
    OrganizationCreateBody,
    OrganizationList,
    OrganizationResponse,
    OrganizationIDSerializer,
    OrganizationUpdateBody,
)
from api.routes.user.serializers import UserIDSerializer
from api.models import UserProfile
from api.routes.user.serializers import UserListSerializer, UserQuerySerializer
from api.lib.pki import CryptoGen, CryptoConfig
from api.utils import zip_dir, zip_file
from api.config import CELLO_HOME
from api.utils.node_config import NodeConfig

from api.common import (
    ok,
    # err
)

LOG = logging.getLogger(__name__)


class OrganizationViewSet(viewsets.ViewSet):
    """Class represents orgnization related operations."""

    @swagger_auto_schema(
        query_serializer=OrganizationQuery,
        responses=with_common_response(
            with_common_response({status.HTTP_200_OK: OrganizationList})
        ),
    )
    def list(self, request):
        """
        List Organizations

        :param request: query parameter
        :return: organization list
        :rtype: list
        """
        serializer = OrganizationQuery(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            page = serializer.validated_data.get("page", 1)
            per_page = serializer.validated_data.get("per_page", 10)
            name = serializer.validated_data.get("name")
            parameters = {}
            if name:
                parameters.update({"name__icontains": name})
            organizations = Organization.objects.filter(**parameters)
            p = Paginator(organizations, per_page)
            organizations = p.page(page)
            organizations = [
                {
                    "id": str(organization.id),
                    "name": organization.name,
                    "network": (
                        str(organization.network.id)
                        if organization.network
                        else None
                    ),
                    "agents": (
                        organization.agents if organization.agents else None
                    ),
                    "created_at": organization.created_at,
                }
                for organization in organizations
            ]
            response = OrganizationList(
                data={"total": p.count, "data": organizations}
            )
            if response.is_valid(raise_exception=True):
                return Response(
                    ok(response.validated_data), status=status.HTTP_200_OK
                )

    @swagger_auto_schema(
        request_body=OrganizationCreateBody,
        responses=with_common_response(
            {status.HTTP_201_CREATED: OrganizationIDSerializer}
        ),
    )
    def create(self, request):
        """
        Create Organization

        :param request: create parameter
        :return: organization ID
        :rtype: uuid
        """
        serializer = OrganizationCreateBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            name = serializer.validated_data.get("name")
            peernum = serializer.validated_data.get("org_peernum")
            orderernum = serializer.validated_data.get("org_orderernum")
            try:
                Organization.objects.get(name=name)
            except ObjectDoesNotExist:
                pass
            else:
                raise ResourceExists("Organization Exists")

            CryptoConfig(name).create(peernum, orderernum)
            CryptoGen(name).generate()

            msp, tls = self._conversion_msp_tls(name)

            organization = Organization(name=name, msp=msp, tls=tls)
            organization.save()

            # create node config
            if peernum > 0:
                self._create_node(organization, peernum, "peer")
            if orderernum > 0:
                self._create_node(organization, orderernum, "orderer")

            response = OrganizationIDSerializer(data=organization.__dict__)
            if response.is_valid(raise_exception=True):
                return Response(
                    ok(response.validated_data), status=status.HTTP_201_CREATED
                )

    def _create_node(self, org, num, nodeType):
        """
        create node

        :param org: organization
        :param num: the number of node
        :param nodeType: the type of node
        :return: null
        """
        for i in range(num):
            nodeName = (
                "peer" + str(i) if nodeType == "peer" else "orderer" + str(i)
            )
            self._generate_config(nodeType, org.name, nodeName)
            msp, tls, cfg = self._conversion_msp_tls_cfg(
                nodeType, org.name, nodeName
            )
            urls = "{}.{}".format(nodeName, org.name)
            node = Node(
                name=nodeName,
                organization=org,
                urls=urls,
                type=nodeType,
                msp=msp,
                tls=tls,
                agent=None,
                config_file=cfg,
            )
            node.save()

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
            LOG.exception("Conversion Failed: CFG from Zip To Byte")
            raise e

        return msp, tls, cfg

    def _generate_config(self, type, org, node):
        """
        generate config for node

        :param org: organization name
        :param type: node type
        :param node: node name
        :param port: node port(todo: automatic distribution port)
        :return: none
        :rtype: none
        """
        args = {}
        if type == "peer":
            args.update({"peer_id": "{}.{}".format(node, org)})
            args.update({"peer_address": "{}.{}:{}".format(node, org, 7051)})
            args.update(
                {
                    "peer_gossip_externalEndpoint": "{}.{}:{}".format(
                        node, org, 7051
                    )
                }
            )
            args.update(
                {"peer_chaincodeAddress": "{}.{}:{}".format(node, org, 7052)}
            )
            args.update({"peer_tls_enabled": True})
            args.update({"peer_localMspId": "{}MSP".format(org.capitalize())})

            a = NodeConfig(org)
            a.peer(node, **args)
        else:
            args.update({"General_ListenPort": 7050})
            args.update(
                {"General_LocalMSPID": "{}OrdererMSP".format(org.capitalize())}
            )
            args.update({"General_TLS_Enabled": True})

            a = NodeConfig(org)
            a.orderer(node, **args)

    def _conversion_msp_tls(self, name):
        """
        msp and tls from zip file to byte

        :param name: organization name
        :return: msp, tls
        :rtype: bytes
        """
        try:
            dir_org = "{}/{}/crypto-config/peerOrganizations/{}/".format(
                CELLO_HOME, name, name
            )

            zip_dir("{}msp".format(dir_org), "{}msp.zip".format(dir_org))
            with open("{}msp.zip".format(dir_org), "rb") as f_msp:
                msp = base64.b64encode(f_msp.read())

            zip_dir("{}tlsca".format(dir_org), "{}tls.zip".format(dir_org))
            with open("{}tls.zip".format(dir_org), "rb") as f_tls:
                tls = base64.b64encode(f_tls.read())
        except Exception as e:
            LOG.exception("Conversion Failed: Zip To Byte")
            raise e

        return msp, tls

    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        )
    )
    def destroy(self, request, pk=None):
        """
        Delete Organization

        :param request: destory parameter
        :param pk: primary key
        :return: none
        :rtype: rest_framework.status
        """
        try:
            organization = Organization.objects.get(id=pk)
            if organization.network:
                raise ResourceInUse("Organization In Use")

            # user_count = UserProfile.objects.filter(
            #     organization=organization
            # ).count()
            # if user_count > 0:
            #     raise ResourceInUse
            path = "{}/{}".format(CELLO_HOME, organization.name)
            if os.path.exists(path):
                shutil.rmtree(path, True)
            organization.delete()
        except ObjectDoesNotExist:
            raise ResourceNotFound("Organization Not Found")

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses=with_common_response(
            {status.HTTP_200_OK: OrganizationResponse}
        )
    )
    def retrieve(self, request, pk=None):
        """
        Retrieve Organization

        :param request: retrieve parameter
        :param pk: primary key
        :return: organization info
        :rtype: OrganizationResponse
        """
        try:
            organization = Organization.objects.get(id=pk)
        except ObjectDoesNotExist:
            raise ResourceNotFound("Organization Not Found")
        else:
            response = OrganizationResponse(data=organization.__dict__)
            if response.is_valid(raise_exception=True):
                return Response(
                    response.validated_data, status=status.HTTP_200_OK
                )

    @swagger_auto_schema(
        request_body=OrganizationUpdateBody,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    def update(self, request, pk=None):
        """
        Update Agent

        Update special agent with id.
        """
        serializer = OrganizationUpdateBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            name = serializer.validated_data.get("name")
            # agents = serializer.validated_data.get("agents")
            # network = serializer.validated_data.get("network")
            # channel = serializer.validated_data.get("channel")
            try:
                Organization.objects.get(name=name)
            except ObjectDoesNotExist:
                pass
            # organization = Organization.objects.filter(name=name).update(agents=agents, network=network.id, channel=channel.id)

            return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _list_users(request, pk=None):
        serializer = UserQuerySerializer(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            try:
                organization = Organization.objects.get(id=pk)
            except ObjectDoesNotExist:
                raise ResourceNotFound("Organization Not Found")
            page = serializer.validated_data.get("page")
            per_page = serializer.validated_data.get("per_page")
            name = serializer.validated_data.get("name")
            parameter = {"organization": organization}
            if name:
                parameter.update({"username__icontains": name})
            users = UserProfile.objects.filter(**parameter)
            p = Paginator(users, per_page)
            users = p.page(page)
            users = [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "role": user.role,
                }
                for user in users
            ]
            response = UserListSerializer(
                data={"total": p.count, "data": users}
            )
            if response.is_valid(raise_exception=True):
                return Response(
                    ok(response.validated_data), status=status.HTTP_200_OK
                )

    @staticmethod
    def _add_user(request, pk=None):
        serializer = UserIDSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get("id")
            try:
                organization = Organization.objects.get(id=pk)
                user = UserProfile.objects.get(id=user_id)
                if user.organization:
                    raise ResourceInUse("Organization In Use")
            except ObjectDoesNotExist:
                raise ResourceNotFound("Organization Not Found")
            else:
                user.organization = organization
                user.save()

                return Response(status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        method="get",
        query_serializer=UserQuerySerializer,
        responses=with_common_response(
            {status.HTTP_200_OK: UserListSerializer}
        ),
    )
    @swagger_auto_schema(
        method="post",
        request_body=UserIDSerializer,
        responses=with_common_response({status.HTTP_202_ACCEPTED: "Accepted"}),
    )
    @action(methods=["get", "post"], detail=True, url_path="users")
    def manage_users(self, request, pk=None):
        """
        get:
        List users

        List users in Organization

        post:
        Add User

        Add user into Organization
        """
        if request.method == "GET":
            return self._list_users(request, pk)
        elif request.method == "POST":
            return self._add_user(request, pk)

    @swagger_auto_schema(
        method="delete",
        responses=with_common_response(
            {status.HTTP_204_NO_CONTENT: "No Content"}
        ),
    )
    @action(
        methods=["delete"], detail=True, url_path="users/(?P<user_id>[^/.]+)"
    )
    def remove_user_from_govern(self, request, pk=None, user_id=None):
        """
        Remove user from Organization

        Remove user from Organization
        """
        try:
            user = UserProfile.objects.get(id=user_id, organization__id=pk)
        except ObjectDoesNotExist:
            raise ResourceNotFound("User Not Found")
        else:
            user.organization = None
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(method="post", responses=with_common_response())
    @action(methods=["post"], detail=True, url_path="certificates")
    def request_certificate(self, request, pk=None):
        """
        post:
        Request Certificate

        Request certificate
        """
        pass

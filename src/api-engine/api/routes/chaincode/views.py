#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
import os
import tempfile
import shutil
import tarfile
import json

from drf_yasg.utils import swagger_auto_schema
from api.config import FABRIC_CHAINCODE_STORE
from api.config import CELLO_HOME
from api.models import (
    Node,
    ChainCode
)
from api.utils.common import make_uuid
from django.core.paginator import Paginator

from api.lib.peer.chaincode import ChainCode as PeerChainCode
from api.common.serializers import PageQuerySerializer
from api.utils.common import with_common_response, init_env_vars
from api.exceptions import ResourceNotFound

from api.routes.chaincode.serializers import (
    ChainCodePackageBody,
    ChainCodeIDSerializer,
    ChainCodeCommitBody,
    ChainCodeApproveForMyOrgBody,
    ChaincodeListResponse
)
from api.common import ok, err
import threading
import hashlib
import logging


LOG = logging.getLogger(__name__)


class ChainCodeViewSet(viewsets.ViewSet):
    """Class represents Channel related operations."""
    permission_classes = [IsAuthenticated, ]

    def _read_cc_pkg(self, pk, filename, ccpackage_path):
        """
        read and extract chaincode package meta info
        :pk: chaincode id
        :filename: uploaded chaincode package filename
        :ccpackage_path: chaincode package path
        """
        try:
            meta_path = os.path.join(ccpackage_path, "metadata.json")
            # extract metadata file
            with tarfile.open(os.path.join(ccpackage_path, filename)) as tared_file:
                metadata_file = None
                for member in tared_file.getmembers():
                    if member.name.endswith("metadata.json"):
                        metadata_file = member
                        break

                if metadata_file is not None:
                    # Extract the metadata file
                    metadata_content = tared_file.extractfile(
                        metadata_file).read().decode("utf-8")
                    metadata = json.loads(metadata_content)
                    language = metadata["type"]
                    label = metadata["label"]

            if os.path.exists(meta_path):
                os.remove(meta_path)

            chaincode = ChainCode.objects.get(id=pk)
            chaincode.package_id = chaincode.package_id
            chaincode.language = language
            chaincode.label = label
            chaincode.save()

        except Exception as e:
            raise e

    @swagger_auto_schema(
        query_serializer=PageQuerySerializer,
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChaincodeListResponse}
        ),
    )
    def list(self, request):
        """
        List Chaincodes
        :param request: org_id
        :return: chaincode list
        :rtype: list
        """
        serializer = PageQuerySerializer(data=request.GET)
        if serializer.is_valid(raise_exception=True):
            page = serializer.validated_data.get("page")
            per_page = serializer.validated_data.get("per_page")

            try:
                org = request.user.organization
                chaincodes = ChainCode.objects.filter(
                    creator=org.name).order_by("create_ts")
                p = Paginator(chaincodes, per_page)
                chaincodes_pages = p.page(page)
                chanincodes_list = [
                    {
                        "id": chaincode.id,
                        "package_id": chaincode.package_id,
                        "label": chaincode.label,
                        "creator": chaincode.creator,
                        "language": chaincode.language,
                        "create_ts": chaincode.create_ts,
                        "description": chaincode.description,
                    }
                    for chaincode in chaincodes_pages
                ]
                response = ChaincodeListResponse(
                    {"data": chanincodes_list, "total": chaincodes.count()})
                return Response(
                    data=ok(
                        response.data),
                    status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    err(e.args), status=status.HTTP_400_BAD_REQUEST
                )

    @swagger_auto_schema(
        method="post",
        query_serializer=PageQuerySerializer,
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['post'], url_path="chaincodeRepo")
    def package(self, request):
        serializer = ChainCodePackageBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            file = serializer.validated_data.get("file")
            description = serializer.validated_data.get("description")
            uuid = make_uuid()
            try:
                fd, temp_cc_path = tempfile.mkstemp()
                # try to calculate packageid
                with open(fd, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)

                with tarfile.open(temp_cc_path, "r:gz") as tar:
                    # Locate the metadata file
                    metadata_file = None
                    for member in tar.getmembers():
                        if member.name.endswith("metadata.json"):
                            metadata_file = member
                            break

                    if metadata_file is not None:
                        # Extract the metadata file
                        metadata_content = tar.extractfile(
                            metadata_file).read().decode("utf-8")
                        metadata = json.loads(metadata_content)
                        label = metadata.get("label")
                    else:
                        return Response(
                            err("Metadata file not found in the chaincode package."),
                            status=status.HTTP_400_BAD_REQUEST)

                org = request.user.organization
                # qs = Node.objects.filter(type="peer", organization=org)
                # if not qs.exists():
                #     return Response(
                #         err("at least 1 peer node is required for the chaincode package upload."),
                #         status=status.HTTP_400_BAD_REQUEST
                #     )
                # peer_node = qs.first()
                # envs = init_env_vars(peer_node, org)
                # peer_channel_cli = PeerChainCode("v2.5.10", **envs)
                # return_code, content = peer_channel_cli.lifecycle_calculatepackageid(temp_cc_path)
                # if (return_code != 0):
                #     return Response(
                #         err("calculate packageid failed for {}.".format(content)),
                #         status=status.HTTP_400_BAD_REQUEST
                #     )
                # packageid = content.strip()

                # manually calculate the package id
                sha256_hash = hashlib.sha256()
                with open(temp_cc_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                packageid = label + ":" + sha256_hash.hexdigest()

                # check if packageid exists
                cc = ChainCode.objects.filter(package_id=packageid)
                if cc.exists():
                    return Response(
                        err("package with id {} already exists.".format(packageid)),
                        status=status.HTTP_400_BAD_REQUEST
                    )

                chaincode = ChainCode(
                    id=uuid,
                    package_id=packageid,
                    creator=org.name,
                    description=description,
                )
                chaincode.save()

                # save chaincode package locally
                ccpackage_path = os.path.join(FABRIC_CHAINCODE_STORE, packageid)
                if not os.path.exists(ccpackage_path):
                    os.makedirs(ccpackage_path)
                ccpackage = os.path.join(ccpackage_path, file.name)
                shutil.copy(temp_cc_path, ccpackage)

                # start thread to read package meta info, update db
                try:
                    threading.Thread(
                        target=self._read_cc_pkg,
                        args=(uuid, file.name, ccpackage_path)).start()
                except Exception as e:
                    raise e

                return Response(
                    ok("success"), status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    err(e.args), status=status.HTTP_400_BAD_REQUEST
                )
            finally:
                os.remove(temp_cc_path)

    @swagger_auto_schema(
        method="post",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['post'])
    def install(self, request):
        chaincode_id = request.data.get("id")
        # Get the selected node ID from request
        node_id = request.data.get("node")
        try:
            cc_targz = ""
            file_path = os.path.join(FABRIC_CHAINCODE_STORE, chaincode_id)
            for _, _, files in os.walk(file_path):
                cc_targz = os.path.join(file_path + "/" + files[0])
                break

            org = request.user.organization

            # If node_id is provided, get that specific node
            if node_id:
                try:
                    peer_node = Node.objects.get(
                        id=node_id, type="peer", organization=org)
                except Node.DoesNotExist:
                    return Response(
                        err("Selected peer node not found or not authorized."),
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Fallback to first peer if no node selected
                qs = Node.objects.filter(type="peer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                peer_node = qs.first()

            envs = init_env_vars(peer_node, org)
            peer_channel_cli = PeerChainCode(**envs)
            res = peer_channel_cli.lifecycle_install(cc_targz)
            if res != 0:
                return Response(
                    err("install chaincode failed."),
                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                err(e.args), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ok("success"), status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="get",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['get'])
    def query_installed(self, request):
        try:
            org = request.user.organization
            qs = Node.objects.filter(type="peer", organization=org)
            if not qs.exists():
                raise ResourceNotFound
            peer_node = qs.first()
            envs = init_env_vars(peer_node, org)

            timeout = "5s"
            peer_channel_cli = PeerChainCode(**envs)
            res, installed_chaincodes = peer_channel_cli.lifecycle_query_installed(
                timeout)
            if res != 0:
                return Response(err("query installed chaincode failed."), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                err(e.args), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ok(installed_chaincodes), status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="get",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['get'])
    def get_installed_package(self, request):
        try:
            org = request.user.organization
            qs = Node.objects.filter(type="peer", organization=org)
            if not qs.exists():
                raise ResourceNotFound
            peer_node = qs.first()
            envs = init_env_vars(peer_node, org)

            timeout = "5s"
            peer_channel_cli = PeerChainCode(**envs)
            res = peer_channel_cli.lifecycle_get_installed_package(timeout)
            if res != 0:
                return Response(err("get installed package failed."), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                err(e.args), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ok("success"), status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="post",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['post'])
    def approve_for_my_org(self, request):
        serializer = ChainCodeApproveForMyOrgBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                channel_name = serializer.validated_data.get("channel_name")
                chaincode_name = serializer.validated_data.get("chaincode_name")
                chaincode_version = serializer.validated_data.get(
                    "chaincode_version")
                policy = serializer.validated_data.get("policy")
                # Perhaps the orderer's port is best stored in the database
                orderer_url = serializer.validated_data.get("orderer_url")
                sequence = serializer.validated_data.get("sequence")

                org = request.user.organization
                qs = Node.objects.filter(type="orderer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                orderer_node = qs.first()

                orderer_tls_dir = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}/msp/tlscacerts" \
                                  .format(CELLO_HOME, org.name, org.name.split(".", 1)[1], orderer_node.name + "." +
                                          org.name.split(".", 1)[1])
                orderer_tls_root_cert = ""
                for _, _, files in os.walk(orderer_tls_dir):
                    orderer_tls_root_cert = orderer_tls_dir + "/" + files[0]
                    break
                qs = Node.objects.filter(type="peer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                peer_node = qs.first()
                envs = init_env_vars(peer_node, org)

                peer_channel_cli = PeerChainCode(**envs)
                code, content = peer_channel_cli.lifecycle_approve_for_my_org(orderer_url, orderer_tls_root_cert, channel_name,
                                                                              chaincode_name, chaincode_version, policy, sequence)
                if code != 0:
                    return Response(err(" lifecycle_approve_for_my_org failed. err: " + content), status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    err(e.args), status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                ok("success"), status=status.HTTP_200_OK
            )

    @swagger_auto_schema(
        method="get",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['get'])
    def query_approved(self, request):
        try:
            org = request.user.organization
            qs = Node.objects.filter(type="peer", organization=org)
            if not qs.exists():
                raise ResourceNotFound
            peer_node = qs.first()
            envs = init_env_vars(peer_node, org)

            channel_name = request.data.get("channel_name")
            cc_name = request.data.get("chaincode_name")

            peer_channel_cli = PeerChainCode(**envs)
            code, content = peer_channel_cli.lifecycle_query_approved(
                channel_name, cc_name)
            if code != 0:
                return Response(err("query_approved failed."), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                err(e.args), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ok(content), status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="post",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['post'])
    def check_commit_readiness(self, request):
        serializer = ChainCodeApproveForMyOrgBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                channel_name = serializer.validated_data.get("channel_name")
                chaincode_name = serializer.validated_data.get("chaincode_name")
                chaincode_version = serializer.validated_data.get(
                    "chaincode_version")
                policy = serializer.validated_data.get("policy")
                # Perhaps the orderer's port is best stored in the database
                orderer_url = serializer.validated_data.get("orderer_url")
                sequence = serializer.validated_data.get("sequence")
                org = request.user.organization
                qs = Node.objects.filter(type="orderer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                orderer_node = qs.first()

                orderer_tls_dir = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}/msp/tlscacerts" \
                    .format(CELLO_HOME, org.name, org.name.split(".", 1)[1], orderer_node.name + "." +
                            org.name.split(".", 1)[1])

                orderer_tls_root_cert = ""
                for _, _, files in os.walk(orderer_tls_dir):
                    orderer_tls_root_cert = orderer_tls_dir + "/" + files[0]
                    break

                qs = Node.objects.filter(type="peer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                peer_node = qs.first()
                envs = init_env_vars(peer_node, org)

                peer_channel_cli = PeerChainCode(**envs)
                code, content = peer_channel_cli.lifecycle_check_commit_readiness(orderer_url, orderer_tls_root_cert,
                                                                                  channel_name, chaincode_name,
                                                                                  chaincode_version, policy, sequence)
                if code != 0:
                    return Response(err("check_commit_readiness failed."), status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response(
                    err(e.args), status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                ok(content), status=status.HTTP_200_OK
            )

    @swagger_auto_schema(
        method="post",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['post'])
    def commit(self, request):
        serializer = ChainCodeCommitBody(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                channel_name = serializer.validated_data.get("channel_name")
                chaincode_name = serializer.validated_data.get("chaincode_name")
                chaincode_version = serializer.validated_data.get(
                    "chaincode_version")
                policy = serializer.validated_data.get("policy")
                # Perhaps the orderer's port is best stored in the database
                orderer_url = serializer.validated_data.get("orderer_url")
                sequence = serializer.validated_data.get("sequence")
                peer_list = serializer.validated_data.get("peer_list")
                org = request.user.organization
                qs = Node.objects.filter(type="orderer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                orderer_node = qs.first()

                orderer_tls_dir = "{}/{}/crypto-config/ordererOrganizations/{}/orderers/{}/msp/tlscacerts" \
                    .format(CELLO_HOME, org.name, org.name.split(".", 1)[1], orderer_node.name + "." +
                            org.name.split(".", 1)[1])
                orderer_tls_root_cert = ""
                for _, _, files in os.walk(orderer_tls_dir):
                    orderer_tls_root_cert = orderer_tls_dir + "/" + files[0]
                    break

                qs = Node.objects.filter(type="peer", organization=org)
                if not qs.exists():
                    raise ResourceNotFound
                peer_node = qs.first()
                envs = init_env_vars(peer_node, org)

                peer_root_certs = []
                peer_address_list = []
                for each in peer_list:
                    peer_node = Node.objects.get(id=each)
                    peer_tls_cert = "{}/{}/crypto-config/peerOrganizations/{}/peers/{}/tls/ca.crt" \
                                    .format(CELLO_HOME, org.name, org.name, peer_node.name + "." + org.name)
                    print(peer_node.port)
                    # port = peer_node.port.all()[0].internal
                    # port = ports[0].internal
                    peer_address = peer_node.name + \
                        "." + org.name + ":" + str(7051)
                    peer_address_list.append(peer_address)
                    peer_root_certs.append(peer_tls_cert)

                peer_channel_cli = PeerChainCode(**envs)
                code = peer_channel_cli.lifecycle_commit(orderer_url, orderer_tls_root_cert, channel_name,
                                                         chaincode_name, chaincode_version, policy,
                                                         peer_address_list, peer_root_certs, sequence)
                if code != 0:
                    return Response(err("commit failed."), status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response(
                    err(e.args), status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                ok("commit success."), status=status.HTTP_200_OK
            )

    @swagger_auto_schema(
        method="get",
        responses=with_common_response(
            {status.HTTP_201_CREATED: ChainCodeIDSerializer}
        ),
    )
    @action(detail=False, methods=['get'])
    def query_committed(self, request):
        try:
            channel_name = request.data.get("channel_name")
            chaincode_name = request.data.get("chaincode_name")
            org = request.user.organization
            qs = Node.objects.filter(type="peer", organization=org)
            if not qs.exists():
                raise ResourceNotFound
            peer_node = qs.first()
            envs = init_env_vars(peer_node, org)
            peer_channel_cli = PeerChainCode(**envs)
            code, chaincodes_commited = peer_channel_cli.lifecycle_query_committed(
                channel_name, chaincode_name)
            if code != 0:
                return Response(err("query committed failed."), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                err(e.args), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ok(chaincodes_commited), status=status.HTTP_200_OK
        )

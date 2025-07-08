#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from rest_framework import serializers
from api.common.enums import (
    Operation,
)
from api.common.serializers import PageQuerySerializer
from api.models import (
    Node,
    Port,
    FabricCA,
    NodeUser,
    FabricPeer,
    PeerCa,
    PeerCaUser,
)

LOG = logging.getLogger(__name__)


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ("external", "internal")
        extra_kwargs = {
            "external": {"required": True},
            "internal": {"required": True},
        }


class NodeQuery(PageQuerySerializer, serializers.ModelSerializer):
    agent_id = serializers.UUIDField(
        help_text="Agent ID, only operator can use this field",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Node
        fields = (
            "page",
            "per_page",
            "type",
            "name",
            "agent_id",
        )
        extra_kwargs = {"type": {"required": False}}


class NodeIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of node")


class NodeCIDSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="containter ID of node")


class FabricCASerializer(serializers.ModelSerializer):
    hosts = serializers.ListField(
        help_text="Hosts for ca support",
        child=serializers.CharField(help_text="Host name", max_length=64),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = FabricCA
        fields = ("admin_name", "admin_password", "hosts", "type")


class PeerCaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeerCaUser
        fields = ("user", "username", "password", "type")

    def validate(self, attrs):
        user = attrs.get("user")
        username = attrs.get("username")
        password = attrs.get("password")
        user_type = attrs.get("type")

        if user is None and (
            username is None or password is None or user_type is None
        ):
            raise serializers.ValidationError(
                "Input user or username,password,type"
            )

        if user is not None and (
            username is not None
            or password is not None
            or user_type is not None
        ):
            raise serializers.ValidationError(
                "Input user or username,password,type"
            )

        return attrs


class PeerCaSerializer(serializers.ModelSerializer):
    users = PeerCaUserSerializer(
        help_text="Users of ca node, "
        "can only set user or set username,password,type together",
        many=True,
    )

    class Meta:
        model = PeerCa
        fields = ("node", "address", "certificate", "type", "users")

    def validate(self, attrs):
        node = attrs.get("node")
        address = attrs.get("address")
        certificate = attrs.get("certificate")
        ca_type = attrs.get("type")

        # check ether set node or set address,certificate,type together
        if (
            node is None
            and (address is None or certificate is None or ca_type is None)
        ) or (
            node is not None
            and (
                address is not None
                or certificate is not None
                or ca_type is not None
            )
        ):
            raise serializers.ValidationError(
                "Input node or address,certificate"
            )

        return attrs


class FabricPeerSerializer(serializers.ModelSerializer):
    ca_nodes = PeerCaSerializer(
        help_text="CA nodes for peer node, "
        "can only set node or set address,certificate,type together",
        many=True,
    )

    class Meta:
        model = FabricPeer
        fields = (
            "name",
            "gossip_use_leader_reflection",
            "gossip_org_leader",
            "gossip_skip_handshake",
            "local_msp_id",
            "ca_nodes",
        )
        extra_kwargs = {
            "name": {"required": True},
            "local_msp_id": {"required": True},
            "ca_nodes": {"required": True},
            "gossip_use_leader_reflection": {"default": True},
            "gossip_skip_handshake": {"default": True},
            "gossip_org_leader": {"default": False},
        }


class NodeInListSerializer(NodeIDSerializer, serializers.ModelSerializer):
    # agent_id = serializers.UUIDField(
    #     help_text="Agent ID", required=False, allow_null=True
    # )
    ports = PortSerializer(
        help_text="Port mapping for node", many=True, required=False
    )
    network_id = serializers.UUIDField(
        help_text="Network ID", required=False, allow_null=True
    )

    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            "urls",
            "created_at",
            "status",
            "network_id",
            "organization",
            "cid",
            "ports",
        )
        extra_kwargs = {
            "id": {"required": True, "read_only": False},
            "created_at": {"required": True, "read_only": False},
            # "ca": {"required": False, "allow_null": True},
        }


class NodeListSerializer(serializers.Serializer):
    data = NodeInListSerializer(many=True, help_text="Nodes list")
    total = serializers.IntegerField(
        help_text="Total number of node", min_value=0
    )


class NodeUrlSerializer(serializers.Serializer):
    internal_port = serializers.IntegerField(
        min_value=1,
        max_value=65535,
        required=True,
        help_text="Port number of node service",
    )
    url = serializers.CharField(help_text="Url of node service", required=True)


class NodeInfoSerializer(NodeIDSerializer, serializers.ModelSerializer):
    # ca = FabricCASerializer(
    #     help_text="CA configuration for node", required=False, allow_null=True
    # )
    # file = serializers.URLField(help_text="File url of node", required=False)
    # links = NodeUrlSerializer(help_text="Links of node service", many=True)
    agent_id = serializers.UUIDField(
        help_text="Agent ID", required=False, allow_null=True
    )

    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            # "network_type",
            # "network_version",
            "created_at",
            "agent_id",
            # "network_id",
            "status",
            # "ca",
            # "file",
            # "links",
        )
        extra_kwargs = {
            "id": {"required": True, "read_only": False},
            "created_at": {"required": True, "read_only": False},
        }


class NodeStatusSerializer(NodeIDSerializer, serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ("status",)
        extra_kwargs = {
            "id": {"required": True, "read_only": False},
            "created_at": {"required": True, "read_only": False},
        }


class NodeCreateBody(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = (
            "name",
            "type",
        )
        extra_kwargs = {
            "name": {"required": True},
            "type": {"required": True},
        }

    def validate(self, attrs):
        # network_type = attrs.get("network_type")
        # node_type = attrs.get("type")
        # network_version = attrs.get("network_version")
        # agent_type = attrs.get("agent_type")
        # agent = attrs.get("agent")
        # ca = attrs.get("ca")
        # peer = attrs.get("peer")
        # if network_type == NetworkType.Fabric.value:
        #     if network_version not in FabricVersions.values():
        #         raise serializers.ValidationError("Not valid fabric version")
        #     if node_type not in FabricNodeType.names():
        #         raise serializers.ValidationError(
        #             "Not valid node type for %s" % network_type
        #         )
        #     if node_type == FabricNodeType.Ca.name.lower() and ca is None:
        #         raise serializers.ValidationError(
        #             "Please input ca configuration for ca node"
        #         )
        #     elif (
        #         node_type == FabricNodeType.Peer.name.lower() and peer is None
        #     ):
        #         raise serializers.ValidationError(
        #             "Please input peer configuration for peer node"
        #         )
        #
        # if agent_type is None and agent is None:
        #     raise serializers.ValidationError("Please set agent_type or agent")
        #
        # if agent_type and agent:
        #     if agent_type != agent.type:
        #         raise serializers.ValidationError(
        #             "agent type not equal to agent"
        #         )

        return attrs


class NodeUpdateBody(serializers.ModelSerializer):
    ports = PortSerializer(
        help_text="Port mapping for node", many=True, required=False
    )

    class Meta:
        model = Node
        fields = ("status", "ports")


class NodeOperationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        help_text=Operation.get_info("Operation for node:", list_str=True),
        choices=Operation.to_choices(True),
    )


class NodeConfigFileSerializer(serializers.ModelSerializer):
    files = serializers.FileField()

    class Meta:
        model = Node
        fields = ("files",)


# class NodeFileCreateSerializer(serializers.ModelSerializer):
#     def to_form_paras(self):
#         custom_paras = to_form_paras(self)

#         return custom_paras

#     class Meta:
#         model = Node
#         fields = ("file",)
#         extra_kwargs = {
#             "file": {
#                 "required": True,
#                 "validators": [
#                     FileExtensionValidator(
#                         allowed_extensions=["tar.gz", "tgz"]
#                     ),
#                     validate_file,
#                 ],
#             }
#         }


class NodeUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("name", "user_type", "secret", "attrs")
        extra_kwargs = {
            "name": {"required": True},
            "user_type": {"required": True},
            "secret": {"required": True},
        }


class NodeUserQuerySerializer(
    PageQuerySerializer, serializers.ModelSerializer
):
    class Meta:
        model = NodeUser
        fields = ("name", "user_type", "page", "per_page", "status")


class UserInListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("id", "name", "user_type", "status")


class NodeUserListSerializer(serializers.Serializer):
    data = UserInListSerializer(many=True, help_text="Users list")
    total = serializers.IntegerField(
        help_text="Total number of node", min_value=0
    )


class NodeUserIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("id",)


class NodeUserPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("status",)
        extra_kwargs = {"status": {"required": True}}

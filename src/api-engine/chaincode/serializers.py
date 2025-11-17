import tarfile
from typing import List, Dict, Any

from django.core.validators import MinValueValidator
from rest_framework import serializers
from chaincode.models import Chaincode
from chaincode.service import ChaincodeAction, create_chaincode, get_chaincode, get_metadata, install_chaincode, approve_chaincode, commit_chaincode, send_chaincode_request
from channel.models import Channel
from channel.serializers import ChannelID
from common.serializers import ListResponseSerializer
from node.models import Node
from user.serializers import UserID


class ChaincodeID(serializers.ModelSerializer):
    class Meta:
        model = Chaincode
        fields = ("id",)

    def create(self, validated_data: Dict[str, Any]) -> Chaincode:
        return get_chaincode(validated_data["id"])


class ChaincodeResponse(ChaincodeID):
    channel = ChannelID()
    creator = UserID()

    class Meta:
        model = Chaincode
        fields = (
            "id",
            "package_id",
            "label",
            "creator",
            "channel",
            "language",
            "status",
            "created_at",
            "description",
        )


class ChaincodeList(ListResponseSerializer):
    data = ChaincodeResponse(many=True, help_text="Chaincode data")


class ChaincodeCreateBody(serializers.ModelSerializer):
    peers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Node.objects.filter(type=Node.Type.PEER),
        help_text="Chaincode Peers"
    )

    class Meta:
        model = Chaincode
        fields = (
            "name",
            "version",
            "sequence",
            "init_required",
            "signature_policy",
            "package",
            "channel",
            "peers",
            "description",
        )
        extra_kwargs = {
            "sequence": {
                "validators": [MinValueValidator(1)]
            },
            "init_required": {"required": False},
            "signature_policy": {"required": False},
        }

    @staticmethod
    def validate_package(value):
        if not value.name.endswith(".tar.gz"):
            raise serializers.ValidationError("Chaincode Package must be a '.tar.gz' file.")

        if value.content_type != "application/gzip":
            raise serializers.ValidationError(
                "Chaincode Package is not a 'application/gzip' file but {} instead."
                .format(value.content_type)
            )

        try:
            metadata = get_metadata(value)
            if metadata is None:
                raise serializers.ValidationError("Metadata not found.")
        except tarfile.TarError:
            raise serializers.ValidationError("Failed to open the chaincode tar package.")

        return value

    def validate_channel(self, value: Channel):
        if not value.organizations.contains(self.context["organization"]):
            raise serializers.ValidationError("You can only install chaincodes on your organization.")
        return value

    def validate_peers(self, value: List[Node]):
        for node in value:
            if Node.Type.PEER != node.type:
                raise serializers.ValidationError(
                    "Node {} is not a peer but a/an {} instead.".format(node.id, node.type)
                )
            if node.organization != self.context["organization"]:
                raise serializers.ValidationError(
                    "Node {} does not belong to your organization.".format(node.id)
                )
        return value

    def create(self, validated_data: Dict[str, Any]) -> ChaincodeID:
        validated_data["user"] = self.context["user"]
        validated_data["organization"] = self.context["organization"]
        return ChaincodeID({"id": create_chaincode(**validated_data).id})


class ChaincodeInstallBody(ChaincodeID):
    def create(self, validated_data: Dict[str, Any]):
        install_chaincode(
            self.context["organization"],
            super().create(validated_data)
        )


class ChaincodeApproveBody(ChaincodeID):
    def create(self, validated_data: Dict[str, Any]):
        approve_chaincode(
            self.context["organization"],
            super().create(validated_data)
        )

class ChaincodeCommitBody(ChaincodeID):
    def create(self, validated_data: Dict[str, Any]):
        commit_chaincode(
            self.context["organization"],
            super().create(validated_data)
        )

class ChaincodeRequestBody(ChaincodeID):
    action = serializers.ChoiceField(choices=[(tag.name, tag.name) for tag in ChaincodeAction])
    function = serializers.CharField()
    args = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )

    def create(self, validated_data: Dict[str, Any]):
        send_chaincode_request(
            self.context["organization"],
            super().create(validated_data),
            validated_data["action"],
            validated_data["function"],
            validated_data["args"]
        )

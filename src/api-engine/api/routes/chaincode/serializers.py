#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers
from api.config import FABRIC_CHAINCODE_STORE

from api.models import ChainCode
from api.common.serializers import ListResponseSerializer
import os


def upload_to(instance, filename):
    return '/'.join([FABRIC_CHAINCODE_STORE, instance.user_name, filename])


class ChainCodeIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ChainCode ID")


class ChainCodePackageBody(serializers.Serializer):
    file = serializers.FileField()

    description = serializers.CharField(max_length=128, required=False)

    def validate(self, attrs):
        extension_get = self.extension_for_file(attrs["file"])
        if not extension_get:
            raise serializers.ValidationError("unsupported package type")
        return super().validate(attrs)

    @staticmethod
    def extension_for_file(file):
            extension = file.name.endswith('.tar.gz')
            return extension

class ChainCodeNetworkSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Network ID")
    name = serializers.CharField(max_length=128, help_text="name of Network")


class ChainCodeOrgListSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Organization ID")
    name = serializers.CharField(
        max_length=128, help_text="name of Organization")


class ChainCodeResponseSerializer(ChainCodeIDSerializer, serializers.ModelSerializer):
    id = serializers.UUIDField(help_text="ID of ChainCode")
    # network = ChainCodeNetworkSerializer()
    # organizations = ChainCodeOrgListSerializer(many=True)

    class Meta:
        model = ChainCode
        fields = ("id", "package_id", "label", "creator", "language", "create_ts", "description")


class ChaincodeListResponse(ListResponseSerializer):
    data = ChainCodeResponseSerializer(many=True, help_text="ChianCode data")


class ChainCodeApproveForMyOrgBody(serializers.Serializer):
    channel_name = serializers.CharField(max_length=128, required=True)
    chaincode_name = serializers.CharField(max_length=128, required=True)
    chaincode_version = serializers.CharField(max_length=128, required=True)
    policy = serializers.CharField(max_length=128, required=True)
    sequence = serializers.IntegerField(min_value=1, required=True)
    init_flag = serializers.BooleanField(required=True)


class ChainCodeCommitBody(ChainCodeApproveForMyOrgBody):
    peer_list = serializers.ListField(allow_empty=False, required=True)

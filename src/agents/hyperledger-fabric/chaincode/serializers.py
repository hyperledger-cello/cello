import os
import threading

from django.contrib.sessions.backends import file
from django.core.files.storage import FileSystemStorage
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from chaincode.service import create_chaincode, install_chaincode, approve_chaincode, get_chaincode_package_id, \
    commit_chaincode
from hyperledger_fabric.settings import CELLO_HOME


class ChaincodeCreationSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    channel_name = serializers.CharField(help_text="Chaincode Channel Name")
    file = serializers.FileField(help_text="Chaincode File")
    init_required = serializers.BooleanField(help_text="Chaincode Required Initialization")
    signature_policy = serializers.CharField(help_text="Chaincode Signature Policy", required=False)

    def create(self, validated_data):
        name = validated_data["name"]
        version = validated_data["version"]
        sequence = validated_data["sequence"]
        channel_name = validated_data["channel_name"]
        file_obj = validated_data["file"]
        chaincode_dir = os.path.join(CELLO_HOME, channel_name, "chaincodes")
        os.makedirs(chaincode_dir, exist_ok=True)
        fs = FileSystemStorage(location=chaincode_dir)
        filename = fs.save("{}_{}_{}.tar.gz".format(name, version, sequence), file_obj)

        threading.Thread(
            target=create_chaincode,
            args=(
                name,
                version,
                sequence,
                channel_name,
                fs.path(filename),
                validated_data["init_required"],
                validated_data.get("signature_policy")),
            daemon=True).start()
        return self


class ChaincodeInstallationSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    channel_name = serializers.CharField(help_text="Chaincode Channel Name")
    file = serializers.FileField(help_text="Chaincode File")

    def create(self, validated_data):
        chaincode_dir = os.path.join(CELLO_HOME, validated_data["channel_name"], "chaincodes")
        os.makedirs(chaincode_dir, exist_ok=True)
        fs = FileSystemStorage(location=chaincode_dir)
        filename = fs.save(
            "{}_{}_{}.tar.gz".format(
                validated_data["name"],
                validated_data["version"],
                validated_data["sequence"]),
            validated_data["file"])

        threading.Thread(
            target=install_chaincode,
            args=(fs.path(filename)),
            daemon=True).start()
        return self

class ChaincodeApprovementSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    channel_name = serializers.CharField(help_text="Chaincode Channel Name")
    init_required = serializers.BooleanField(help_text="Chaincode Required Initialization")
    signature_policy = serializers.CharField(help_text="Chaincode Signature Policy", required=False, allow_null=True)

    def create(self, validated_data):
        name = validated_data["name"]
        version = validated_data["version"]
        sequence = validated_data["sequence"]
        channel_name = validated_data["channel_name"]
        chaincode_dir = os.path.join(CELLO_HOME, channel_name, "chaincodes")
        os.makedirs(chaincode_dir, exist_ok=True)
        fs = FileSystemStorage(location=chaincode_dir)

        package_id = get_chaincode_package_id(fs.path("{}_{}_{}.tar.gz".format(name, version, sequence)))
        approve_chaincode(
            name,
            channel_name,
            version,
            package_id,
            sequence,
            validated_data["init_required"],
            validated_data["signature_policy"])
        return self


class ChaincodeCommitSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    channel_name = serializers.CharField(help_text="Chaincode Channel Name")

    def create(self, validated_data):
        commit_chaincode(
            validated_data["name"],
            validated_data["channel_name"],
            validated_data["version"],
            validated_data["sequence"])
        return self

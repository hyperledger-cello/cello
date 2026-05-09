import os
import threading

from django.core.files.storage import FileSystemStorage
from rest_framework import serializers

from chaincode.service import create_chaincode, install_chaincode, approve_chaincode, get_chaincode_package_id, \
    commit_chaincode, get_metadata, get_chaincode_status, get_chaincode_commit_readiness
from hyperledger_fabric.settings import CELLO_HOME


class ChaincodeCommitReadinessResponse(serializers.Serializer):
    approvals = serializers.DictField(help_text="Chaincode Commit Readiness")


class ChaincodeCommitReadinessRequest(serializers.Serializer):
    channel = serializers.CharField(help_text="Chaincode Channel Name")
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    init_required = serializers.BooleanField(help_text="Chaincode Required Initialization")

    def create(self, validated_data):
        return ChaincodeCommitReadinessResponse(dict(
            approvals=get_chaincode_commit_readiness(
                validated_data["channel"],
                validated_data["name"],
                validated_data["version"],
                validated_data["sequence"],
                validated_data["init_required"])))


class ChaincodeStatusResponse(serializers.Serializer):
    status = serializers.CharField(help_text="Chaincode Status")


class ChaincodeStatusRequest(serializers.Serializer):
    package_id = serializers.CharField(help_text="Chaincode Package ID")
    channel = serializers.CharField(help_text="Chaincode Channel Name")
    name = serializers.CharField(help_text="Chaincode Name")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")

    def create(self, validated_data):
        return ChaincodeStatusResponse(dict(
            status=get_chaincode_status(
                validated_data["package_id"],
                validated_data["channel"],
                validated_data["name"],
                validated_data["sequence"]).name))


class ChaincodeResponseSerializer(serializers.Serializer):
    label = serializers.CharField(help_text="Chaincode Label")
    language = serializers.CharField(help_text="Chaincode Language")
    package_id = serializers.CharField(help_text="Chaincode Package ID")


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
        file_path = fs.path(filename)

        metadata = get_metadata(file_path)
        package_id = get_chaincode_package_id(file_path)
        threading.Thread(
            target=create_chaincode,
            args=(
                name,
                version,
                sequence,
                channel_name,
                file_path,
                package_id,
                validated_data["init_required"],
                validated_data.get("signature_policy")),
            daemon=True).start()
        return ChaincodeResponseSerializer(dict(
            label=metadata["label"],
            language=metadata["type"],
            package_id=package_id,
        ))


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
            args=(fs.path(filename),),
            daemon=True).start()
        return self

class ChaincodeApprovementSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Chaincode Name")
    version = serializers.CharField(help_text="Chaincode Version")
    sequence = serializers.IntegerField(help_text="Chaincode Sequence")
    package_id = serializers.CharField(help_text="Chaincode Package ID")
    channel_name = serializers.CharField(help_text="Chaincode Channel Name")
    init_required = serializers.BooleanField(help_text="Chaincode Required Initialization")
    signature_policy = serializers.CharField(help_text="Chaincode Signature Policy", required=False, allow_null=True)

    def create(self, validated_data):
        approve_chaincode(
            validated_data["name"],
            validated_data["channel_name"],
            validated_data["version"],
            validated_data["package_id"],
            validated_data["sequence"],
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

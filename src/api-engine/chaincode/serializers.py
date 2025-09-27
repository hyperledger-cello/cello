import tarfile

from rest_framework import serializers

from chaincode.models import Chaincode
from common.serializers import ListResponseSerializer

class ChaincodeID(serializers.ModelSerializer):
    class Meta:
        model = Chaincode
        fields = ("id",)

class ChaincodeResponse(ChaincodeID):
    class Meta:
        model = Chaincode
        fields = (
            "id",
            "package_id",
            "label",
            "creator",
            "language",
            "created_at",
            "description",
        )

class ChaincodeList(ListResponseSerializer):
    data = ChaincodeResponse(many=True, help_text="Chaincode data")

class ChaincodeCreateBody(serializers.Serializer):
    file = serializers.FileField()
    description = serializers.CharField(max_length=128, required=False)

    @staticmethod
    def validate_file(value):
        if not value.name.endswith(".tar.gz"):
            raise serializers.ValidationError("Chaincode Package must be a '.tar.gz' file.")

        if value.content_type != "application/gzip":
            raise serializers.ValidationError(
                "Chaincode Package is not a 'application/gzip' file but {} instead."
                    .format(value.content_type)
            )

        try:
            value.seek(0)
            with tarfile.open(fileobj=value, mode='r:gz') as tar:
                tar.getmembers()
            value.seek(0)
        except tarfile.TarError:
            raise serializers.ValidationError("Failed to open the chaincode tar package.")

        return value

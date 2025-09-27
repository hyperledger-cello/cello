from rest_framework import serializers

from chaincode.models import Chaincode
from common.serializers import ListResponseSerializer

class ChaincodeID(serializers.Serializer):
    id = serializers.UUIDField(help_text="ChainCode ID")

class ChaincodeResponse(
    ChaincodeID, serializers.ModelSerializer):
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


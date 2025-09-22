from typing import Dict, Any
from rest_framework import serializers
from api.common.serializers import ListResponseSerializer
from api.lib.pki import CryptoConfig, CryptoGen
from node import service
from node.models import Node


class NodeIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of node")


class NodeResponseSerializer(NodeIDSerializer, serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            "created_at",
            "status",
            "cid",
        )


class NodeListSerializer(ListResponseSerializer):
    data = NodeResponseSerializer(many=True, help_text="Node list")


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

    def validate(self, data: Dict[str, Any]):
        if any(node.name == data["name"] for node in self.context["organization"].nodes.all()):
            raise serializers.ValidationError("Node Exists")
        return data

    def create(self, validated_data: Dict[str, Any]) -> Node:
        return service.create(self.context["organization"], validated_data["type"], validated_data["name"])

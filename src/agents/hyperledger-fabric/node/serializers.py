from rest_framework import serializers

from node.enums import NodeType
from node.service import create_node, get_node_status


class NodeRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        help_text="Node Type",
        choices=[(node_type.name, node_type.name) for node_type in NodeType])
    name = serializers.CharField(help_text="Node Name")

    def create(self, validated_data):
        return NodeResponseSerializer({
            "type": validated_data["type"],
            "name": validated_data["name"],
            "tls": create_node(validated_data["type"], validated_data["name"])
        })

class NodeResponseSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        help_text="Node Type",
        choices=[(node_type.name, node_type.name) for node_type in NodeType])
    name = serializers.CharField(help_text="Node Name")
    tls = serializers.CharField(help_text="Node TLS")


class NodeStatusSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Node Status")


class NodeStatusRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        help_text="Node Type",
        choices=[(node_type.name, node_type.name) for node_type in NodeType])
    name = serializers.CharField(help_text="Node Name")

    def create(self, validated_data) -> NodeStatusSerializer:
        status = get_node_status(validated_data["type"], validated_data["name"])
        return NodeStatusSerializer(dict(status=status))


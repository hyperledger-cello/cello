from rest_framework import serializers

from node.enums import NodeType
from node.service import create_node


class NodeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(help_text="Node Type", choices=[(node_type.name, node_type.name) for node_type in NodeType])
    name = serializers.CharField(help_text="Node Name")

    def create(self, validated_data):
        create_node(validated_data["type"], validated_data["name"])
        return self

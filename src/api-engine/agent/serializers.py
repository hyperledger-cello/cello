#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    ROLE_CHOICES = ("user", "assistant")
    role = serializers.ChoiceField(choices=ROLE_CHOICES)
    content = serializers.CharField(allow_blank=False, trim_whitespace=False)


class ChatRequestBody(serializers.Serializer):
    """Request body for POST /api/v1/agent/chat.

    The full conversation is sent each turn (stateless server). The last
    message must come from the user.
    """

    messages = serializers.ListField(
        child=ChatMessageSerializer(),
        allow_empty=False,
        min_length=1,
        help_text="Conversation so far, oldest first.",
    )

    def validate_messages(self, value):
        if value[-1]["role"] != "user":
            raise serializers.ValidationError(
                "The last message must have role 'user'."
            )
        return value


class ToolCallSerializer(serializers.Serializer):
    name = serializers.CharField()
    input = serializers.DictField()
    output = serializers.DictField()


class ChatResponse(serializers.Serializer):
    reply = serializers.CharField()
    stop_reason = serializers.CharField()
    tool_calls = ToolCallSerializer(many=True)

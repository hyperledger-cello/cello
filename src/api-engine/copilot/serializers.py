#
# SPDX-License-Identifier: Apache-2.0
#
from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    ROLE_CHOICES = ("user", "assistant")
    role = serializers.ChoiceField(choices=ROLE_CHOICES)
    content = serializers.CharField(allow_blank=False, trim_whitespace=False)


class ChatRequestBody(serializers.Serializer):
    """Request body for POST /api/v1/copilot/chat.

    The client sends the whole conversation each turn and the server keeps no
    state between requests. The last message has to come from the user, since
    there is nothing for the model to answer otherwise.
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


class ChatDoneEvent(serializers.Serializer):
    """Payload of the final ``done`` frame.

    Declared for the generated API docs, which cannot describe an event stream.
    A client that only wants the answer can read this frame and skip the rest.
    """

    reply = serializers.CharField()
    stop_reason = serializers.CharField()
    tool_calls = ToolCallSerializer(many=True)

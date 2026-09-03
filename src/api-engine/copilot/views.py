#
# SPDX-License-Identifier: Apache-2.0
#
"""Chat endpoint for the Cello copilot.

``POST /api/v1/copilot/chat``, JWT protected, answering as a server-sent event
stream. The contract the dashboard panel is built against is written up in #813.

The copilot forwards the caller's own ``Authorization`` header to Cello's REST
API, so it sees exactly what that user is allowed to see. Scoping is inherited
from the existing API rather than reimplemented here, and there is no service
account to over-privilege.

Errors land in one of two places. Until the first byte goes out the status line
is still ours, so a bad body is a 400, missing auth a 401, a missing API key a
503 and an unreachable provider a 502. After that the response is already a 200
and a failure can only arrive as an ``error`` frame.
"""
from django.conf import settings
from django.http import StreamingHttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.common import err
from copilot import sse
from copilot.llm import AgentConfigError, AgentUpstreamError, stream_agent
from copilot.serializers import ChatDoneEvent, ChatRequestBody
from copilot.tools import ToolContext


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Chat with the Cello copilot (read-only)",
        operation_description=(
            "Answers as a text/event-stream. Frames are `token`, `tool_call`, "
            "`tool_result` and a final `done`, or a single `error` frame if the "
            "turn fails after the stream has opened. The schema below is the "
            "body of the `done` frame."
        ),
        request_body=ChatRequestBody,
        responses={status.HTTP_200_OK: ChatDoneEvent},
    )
    def post(self, request):
        body = ChatRequestBody(data=request.data)
        body.is_valid(raise_exception=True)

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data=err("Missing Authorization header."),
            )

        context = ToolContext(
            auth_header=auth_header,
            api_base=settings.CELLO_COPILOT_API_BASE,
        )

        try:
            events = stream_agent(
                messages=body.validated_data["messages"], context=context
            )
        except AgentConfigError as exc:
            return Response(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                data=err("The copilot is not configured: %s" % exc),
            )

        stream = sse.EventStream(events)
        stream.start()

        # Give the turn a moment to fail before committing to a status code.
        # Most failures (missing key, bad key, unreachable endpoint) happen on
        # the first provider call, so this catches them while a JSON error is
        # still possible.
        opening = stream.first()
        if opening is not None and opening[0] == "error":
            failure = opening[1]
            if isinstance(failure, AgentConfigError):
                return Response(
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    data=err("The copilot is not configured: %s" % failure),
                )
            if isinstance(failure, AgentUpstreamError):
                return Response(
                    status=status.HTTP_502_BAD_GATEWAY,
                    data=err(
                        "The LLM provider could not be reached: %s" % failure
                    ),
                )
            raise failure

        response = StreamingHttpResponse(
            stream.frames(), content_type="text/event-stream; charset=utf-8"
        )
        response["Cache-Control"] = "no-cache"
        # uWSGI and nginx both buffer by default, which would hold the whole
        # answer until the turn ends and defeat the point of streaming.
        response["X-Accel-Buffering"] = "no"
        return response

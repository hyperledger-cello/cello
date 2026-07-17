#
# SPDX-License-Identifier: Apache-2.0
#
"""Chat endpoint for the Cello AI operations agent.

POST /api/v1/agent/chat -- JWT-protected. The agent forwards the caller's own
``Authorization`` header to Cello's REST API, so it can only ever see and do what
that user is allowed to -- scoping is inherited from the existing API, not
re-implemented here. Phase 1 returns a single JSON reply (no streaming).
"""
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.common import err, ok
from agent.llm import AgentConfigError, AgentUpstreamError, run_agent
from agent.serializers import ChatRequestBody, ChatResponse
from agent.tools import ToolContext


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Chat with the Cello operations agent (read-only)",
        request_body=ChatRequestBody,
        responses={status.HTTP_200_OK: ChatResponse},
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
            api_base=settings.CELLO_AGENT_API_BASE,
        )

        try:
            result = run_agent(
                messages=body.validated_data["messages"],
                context=context,
            )
        except AgentConfigError as exc:
            return Response(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                data=err(f"Agent is not configured: {exc}"),
            )
        except AgentUpstreamError as exc:
            return Response(
                status=status.HTTP_502_BAD_GATEWAY,
                data=err(f"The LLM provider could not be reached: {exc}"),
            )

        return Response(
            status=status.HTTP_200_OK,
            data=ok(
                ChatResponse(
                    {
                        "reply": result.reply,
                        "stop_reason": result.stop_reason,
                        "tool_calls": [
                            {
                                "name": t.name,
                                "input": t.input,
                                "output": t.output,
                            }
                            for t in result.tool_calls
                        ],
                    }
                ).data
            ),
        )

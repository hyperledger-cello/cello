#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for the read-only AI operations agent.

Nothing here touches the network or needs an API key: the LLM client is always
mocked, and the tools' HTTP calls to Cello's REST API are mocked too. We assert
that (a) the tool issues the right authenticated GET and parses Cello's response
envelope, (b) the tool-calling loop drives tools then answers, (c) the provider
is selected from a registry rather than hardcoded, and (d) the base URL is
forwarded, which is what lets one provider serve many vendors.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from organization.models import Organization
from user.models import UserProfile
from agent import llm, tools
from agent.llm import (
    AgentConfigError,
    AgentResult,
    AgentUpstreamError,
    run_agent,
)


def _ctx():
    return tools.ToolContext(
        auth_header="JWT test-token", api_base="http://api/api/v1"
    )


def _rest_response(status_code=200, payload=None, text=""):
    """A fake ``requests`` response with just what the tools read."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if payload is None:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = payload
    return resp


def _list_envelope(items, total=None):
    """Cello's list envelope: {status, msg, data:{total, data:[...]}}."""
    return {
        "status": "SUCCESSFUL",
        "msg": None,
        "data": {"total": total if total is not None else len(items),
                 "data": items},
    }


def _completion(message, finish_reason="stop"):
    """A fake chat-completions response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)]
    )


def _answer(text):
    """An assistant turn with no tool calls."""
    return SimpleNamespace(tool_calls=None, content=text)


def _tool_call(name, params, call_id="call_1"):
    """An assistant turn asking for one tool call."""
    message = MagicMock()
    message.content = None
    message.tool_calls = [
        SimpleNamespace(
            id=call_id,
            function=SimpleNamespace(name=name, arguments=json.dumps(params)),
        )
    ]
    message.model_dump.return_value = {"role": "assistant", "tool_calls": []}
    return message


class ToolRegistryTests(TestCase):
    @patch("agent.tools.requests.get")
    def test_list_nodes_forwards_jwt_and_parses_envelope(self, get):
        get.return_value = _rest_response(
            payload=_list_envelope(
                [{"name": "peer0", "type": "peer"},
                 {"name": "orderer0", "type": "orderer"}]
            )
        )
        out = tools.run_tool("list_nodes", {}, _ctx())

        self.assertTrue(out["ok"])
        self.assertEqual(out["count"], 2)
        self.assertEqual(out["total"], 2)
        self.assertEqual({n["name"] for n in out["nodes"]},
                         {"peer0", "orderer0"})
        # Correct URL, forwarded auth header, capped pagination.
        args, kwargs = get.call_args
        self.assertEqual(args[0], "http://api/api/v1/nodes")
        self.assertEqual(kwargs["headers"], {"Authorization": "JWT test-token"})
        self.assertLessEqual(kwargs["params"]["per_page"], 100)

    @patch("agent.tools.requests.get")
    def test_limit_caps_per_page_at_100(self, get):
        get.return_value = _rest_response(payload=_list_envelope([]))
        tools.run_tool("list_nodes", {"limit": 5000}, _ctx())
        self.assertEqual(get.call_args.kwargs["params"]["per_page"], 100)

    @patch("agent.tools.requests.get")
    def test_http_error_becomes_structured_error(self, get):
        get.return_value = _rest_response(status_code=403, text="forbidden")
        out = tools.run_tool("list_nodes", {}, _ctx())
        self.assertFalse(out["ok"])
        self.assertIn("403", out["error"])

    def test_missing_auth_header_is_an_error(self):
        ctx = tools.ToolContext(auth_header="", api_base="http://api/api/v1")
        out = tools.run_tool("list_nodes", {}, ctx)
        self.assertFalse(out["ok"])

    def test_unknown_tool_raises(self):
        with self.assertRaises(tools.UnknownToolError):
            tools.run_tool("delete_everything", {}, _ctx())

    def test_tool_schemas_shape(self):
        schemas = tools.openai_tool_schemas()
        names = {s["function"]["name"] for s in schemas}
        self.assertIn("list_nodes", names)
        for s in schemas:
            self.assertEqual(s["type"], "function")
            self.assertIn("parameters", s["function"])
            self.assertIn("description", s["function"])


class RunAgentTests(TestCase):
    @patch("agent.tools.requests.get")
    @patch("agent.llm._get_client")
    def test_tool_loop_runs_tool_then_answers(self, get_client, http_get):
        http_get.return_value = _rest_response(
            payload=_list_envelope([{"name": "peer0"}])
        )
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _completion(_tool_call("list_nodes", {}), finish_reason="tool_calls"),
            _completion(_answer("You have 1 node: peer0.")),
        ]
        get_client.return_value = client

        result = run_agent(
            messages=[{"role": "user", "content": "list my nodes"}],
            context=_ctx(),
        )

        self.assertEqual(result.stop_reason, "stop")
        self.assertIn("peer0", result.reply)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "list_nodes")
        self.assertTrue(result.tool_calls[0].output["ok"])
        self.assertEqual(client.chat.completions.create.call_count, 2)

    @patch("agent.llm._get_client")
    def test_direct_answer_without_tools(self, get_client):
        client = MagicMock()
        client.chat.completions.create.return_value = _completion(
            _answer("I can list nodes and channels.")
        )
        get_client.return_value = client

        result = run_agent(
            messages=[{"role": "user", "content": "what can you do?"}],
            context=_ctx(),
        )
        self.assertEqual(result.tool_calls, [])
        self.assertIn("list", result.reply.lower())

    @patch("agent.tools.requests.get")
    @patch("agent.llm._get_client")
    def test_max_iterations_guard(self, get_client, http_get):
        http_get.return_value = _rest_response(payload=_list_envelope([]))
        client = MagicMock()
        client.chat.completions.create.return_value = _completion(
            _tool_call("list_nodes", {}), finish_reason="tool_calls"
        )
        get_client.return_value = client

        with self.settings(CELLO_AGENT_MAX_TOOL_ITERATIONS=3):
            result = run_agent(
                messages=[{"role": "user", "content": "loop forever"}],
                context=_ctx(),
            )
        self.assertEqual(result.stop_reason, "max_iterations")
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_missing_api_key_raises_config_error(self):
        with self.settings(CELLO_AGENT_LLM_API_KEY=""):
            with self.assertRaises(AgentConfigError):
                run_agent(
                    messages=[{"role": "user", "content": "hi"}],
                    context=_ctx(),
                )


class ClientConfigTests(TestCase):
    """The base URL is what makes the provider vendor-agnostic, so pin it."""

    @patch("openai.OpenAI")
    def test_base_url_is_forwarded_when_set(self, openai_cls):
        with self.settings(
            CELLO_AGENT_LLM_API_KEY="k",
            CELLO_AGENT_LLM_BASE_URL="https://api.deepseek.com",
        ):
            llm._get_client()
        self.assertEqual(
            openai_cls.call_args.kwargs["base_url"], "https://api.deepseek.com"
        )

    @patch("openai.OpenAI")
    def test_base_url_omitted_when_empty(self, openai_cls):
        """An empty base URL must fall through to the SDK default, not be
        passed as an empty string (which the client would reject)."""
        with self.settings(
            CELLO_AGENT_LLM_API_KEY="k", CELLO_AGENT_LLM_BASE_URL=""
        ):
            llm._get_client()
        self.assertNotIn("base_url", openai_cls.call_args.kwargs)


class ProviderSelectionTests(TestCase):
    def test_registered_provider_is_dispatched_to(self):
        """A provider is selected by name from the registry -- the seam a
        second provider plugs into without touching the tool layer."""
        sentinel = AgentResult(reply="from the stub provider")
        with patch.dict(llm._PROVIDERS, {"stub": lambda m, c: sentinel}):
            with self.settings(CELLO_AGENT_LLM_PROVIDER="stub"):
                result = run_agent(
                    messages=[{"role": "user", "content": "hi"}],
                    context=_ctx(),
                )
        self.assertEqual(result.reply, "from the stub provider")

    def test_unknown_provider_raises_config_error(self):
        with self.settings(CELLO_AGENT_LLM_PROVIDER="does-not-exist"):
            with self.assertRaises(AgentConfigError):
                run_agent(
                    messages=[{"role": "user", "content": "hi"}],
                    context=_ctx(),
                )


class ChatEndpointTests(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="OrgA", agent_url="http://agent.example.com:5001"
        )
        self.user = UserProfile.objects.create(
            username="alice", email="alice@example.com", organization=self.org
        )
        token = str(AccessToken.for_user(self.user))
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    def test_requires_auth(self):
        self.client.credentials()  # drop the token
        resp = self.client.post(
            "/api/v1/agent/chat",
            {"messages": [{"role": "user", "content": "hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_rejects_empty_messages(self):
        resp = self.client.post(
            "/api/v1/agent/chat", {"messages": []}, format="json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_last_message_must_be_user(self):
        resp = self.client.post(
            "/api/v1/agent/chat",
            {"messages": [{"role": "assistant", "content": "hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("agent.views.run_agent")
    def test_happy_path(self, run_agent_mock):
        run_agent_mock.return_value = SimpleNamespace(
            reply="You have 1 node.",
            stop_reason="end_turn",
            tool_calls=[],
        )
        resp = self.client.post(
            "/api/v1/agent/chat",
            {"messages": [{"role": "user", "content": "how many nodes?"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "SUCCESSFUL")
        self.assertEqual(resp.data["data"]["reply"], "You have 1 node.")
        # The caller's JWT is forwarded into the tool context.
        self.assertTrue(
            run_agent_mock.call_args.kwargs["context"].auth_header.startswith(
                "JWT "
            )
        )

    @patch("agent.views.run_agent", side_effect=AgentConfigError("no key"))
    def test_unconfigured_returns_503(self, _):
        resp = self.client.post(
            "/api/v1/agent/chat",
            {"messages": [{"role": "user", "content": "hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 503)

    @patch(
        "agent.views.run_agent",
        side_effect=AgentUpstreamError("Error code: 401 - invalid api key"),
    )
    def test_upstream_failure_returns_502_not_a_traceback(self, _):
        """A bad key/rate limit must not surface as an unhandled 500 -- with
        DEBUG on, Django's error page would echo settings back to the caller."""
        resp = self.client.post(
            "/api/v1/agent/chat",
            {"messages": [{"role": "user", "content": "hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.data["status"], "FAILED")

#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for the read-only Cello copilot.

Nothing here touches the network or needs an API key. The LLM client is always a
stub and the tools' HTTP calls to Cello are mocked. What is asserted:

* the client issues the right authenticated GET and unwraps Cello's envelope
* streamed tool calls are reassembled from deltas split across chunks
* the loop drives tools and then answers, in the frame order the contract states
* the provider comes from a registry rather than being hardcoded
* the base URL is forwarded, which is what lets one runner serve many vendors
* a failure before the first byte is a status code, and after it a frame
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from organization.models import Organization
from user.models import UserProfile
from copilot import client, llm, sse, tools
from copilot.llm import (
    AgentConfigError,
    AgentUpstreamError,
    Event,
    run_agent,
    stream_agent,
)

SETTINGS = {
    "CELLO_COPILOT_LLM_API_KEY": "k",
    "CELLO_COPILOT_LLM_MODEL": "deepseek-chat",
}


def _ctx():
    return tools.ToolContext(
        auth_header="JWT test-token", api_base="http://api/api/v1"
    )


def _rest_response(status_code=200, payload=None, text=""):
    """A fake ``requests`` response carrying only what the client reads."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if payload is None:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = payload
    return resp


def _list_envelope(items, total=None):
    """Cello's list envelope: {status, msg, data: {total, data: [...]}}."""
    return {
        "status": "SUCCESSFUL",
        "msg": None,
        "data": {
            "total": total if total is not None else len(items),
            "data": items,
        },
    }


def _chunk(content=None, tool_calls=None, finish_reason=None):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=delta, finish_reason=finish_reason)]
    )


def _call_delta(index=0, call_id=None, name=None, arguments=None):
    return SimpleNamespace(
        index=index,
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _text_turn(text, finish_reason="stop"):
    """A plain answer, split so the streaming path is actually exercised."""
    return [_chunk(content=part) for part in text.split(" ")] + [
        _chunk(finish_reason=finish_reason)
    ]


def _tool_turn(name, params, call_id="call_1"):
    """A tool-call turn with the arguments split across two chunks.

    Providers send the id and name once and then dribble the JSON in, so
    splitting here is what the accumulator has to survive.
    """
    arguments = json.dumps(params)
    half = len(arguments) // 2
    return [
        _chunk(tool_calls=[_call_delta(call_id=call_id, name=name)]),
        _chunk(tool_calls=[_call_delta(arguments=arguments[:half])]),
        _chunk(tool_calls=[_call_delta(arguments=arguments[half:])]),
        _chunk(finish_reason="tool_calls"),
    ]


def _stub_client(*turns):
    stub = MagicMock()
    stub.chat.completions.create.side_effect = list(turns)
    return stub


class ClientTests(TestCase):
    @patch("copilot.client.requests.get")
    def test_list_nodes_forwards_auth_and_unwraps_envelope(self, get):
        get.return_value = _rest_response(
            payload=_list_envelope(
                [{"name": "peer0", "type": "peer"},
                 {"name": "orderer0", "type": "orderer"}]
            )
        )
        out = client.list_nodes("http://api/api/v1", "JWT test-token")

        self.assertTrue(out["ok"])
        self.assertEqual(out["count"], 2)
        self.assertEqual(out["total"], 2)
        self.assertEqual(
            {n["name"] for n in out["nodes"]}, {"peer0", "orderer0"}
        )
        args, kwargs = get.call_args
        self.assertEqual(args[0], "http://api/api/v1/nodes")
        self.assertEqual(kwargs["headers"], {"Authorization": "JWT test-token"})

    @patch("copilot.client.requests.get")
    def test_limit_is_capped_at_the_server_maximum(self, get):
        get.return_value = _rest_response(payload=_list_envelope([]))
        client.list_nodes("http://api/api/v1", "JWT t", limit=5000)
        self.assertEqual(get.call_args.kwargs["params"]["per_page"], 100)

    @patch("copilot.client.requests.get")
    def test_http_error_becomes_a_structured_error(self, get):
        get.return_value = _rest_response(status_code=403, text="forbidden")
        out = client.list_nodes("http://api/api/v1", "JWT t")
        self.assertFalse(out["ok"])
        self.assertIn("403", out["error"])

    @patch("copilot.client.requests.get")
    def test_non_json_body_becomes_a_structured_error(self, get):
        get.return_value = _rest_response(text="<html>nope</html>")
        out = client.list_nodes("http://api/api/v1", "JWT t")
        self.assertFalse(out["ok"])

    def test_missing_auth_header_is_an_error(self):
        out = client.list_nodes("http://api/api/v1", "")
        self.assertFalse(out["ok"])

    @patch("copilot.client.requests.get")
    def test_health_check_needs_no_token(self, get):
        get.return_value = _rest_response(payload={})
        out = client.check_health("http://api/api/v1")
        self.assertTrue(out["ok"])
        self.assertNotIn("headers", get.call_args.kwargs)


class ToolRegistryTests(TestCase):
    def test_every_registered_tool_is_read_only(self):
        names = {t.name for t in tools.get_tools()}
        self.assertEqual(
            names,
            {
                "list_nodes",
                "list_channels",
                "list_chaincodes",
                "list_organizations",
                "check_health",
            },
        )

    def test_unknown_tool_raises(self):
        with self.assertRaises(tools.UnknownToolError):
            tools.run_tool("delete_everything", {}, _ctx())

    @patch("copilot.tools.client.list_nodes", side_effect=RuntimeError("boom"))
    def test_a_failing_tool_does_not_abort_the_turn(self, _):
        out = tools.run_tool("list_nodes", {}, _ctx())
        self.assertFalse(out["ok"])
        self.assertIn("boom", out["detail"])

    def test_schemas_are_well_formed(self):
        schemas = tools.openai_tool_schemas()
        self.assertEqual(len(schemas), len(tools.get_tools()))
        for schema in schemas:
            self.assertEqual(schema["type"], "function")
            self.assertIn("description", schema["function"])
            self.assertEqual(schema["function"]["parameters"]["type"], "object")


class StreamAgentTests(TestCase):
    def _events(self, *turns):
        with self.settings(**SETTINGS):
            with patch("copilot.llm._get_client", return_value=_stub_client(*turns)):
                return list(stream_agent([{"role": "user", "content": "hi"}], _ctx()))

    @patch("copilot.client.requests.get")
    def test_tool_call_is_reassembled_from_split_deltas(self, get):
        get.return_value = _rest_response(
            payload=_list_envelope([{"name": "peer0"}])
        )
        events = self._events(
            _tool_turn("list_nodes", {"limit": 10}),
            _text_turn("You have one node."),
        )
        call = next(e for e in events if e.name == "tool_call")
        self.assertEqual(call.data["name"], "list_nodes")
        self.assertEqual(call.data["input"], {"limit": 10})

    @patch("copilot.client.requests.get")
    def test_frame_order_matches_the_contract(self, get):
        get.return_value = _rest_response(payload=_list_envelope([]))
        events = self._events(
            _tool_turn("list_nodes", {}), _text_turn("No nodes.")
        )
        order = [e.name for e in events]
        self.assertEqual(order[0], "tool_call")
        self.assertEqual(order[1], "tool_result")
        self.assertEqual(order[-1], "done")
        # tool_result carries the id of the tool_call it answers.
        self.assertEqual(events[0].data["id"], events[1].data["id"])
        # Tokens only ever appear before the done frame.
        self.assertTrue(all(e.name == "token" for e in events[2:-1]))

    def test_tokens_stream_before_the_done_frame(self):
        events = self._events(_text_turn("two peers are up"))
        tokens = [e.data["text"] for e in events if e.name == "token"]
        self.assertEqual(len(tokens), 4)
        done = events[-1]
        self.assertEqual(done.name, "done")
        self.assertEqual(done.data["reply"], "twopeersareup")
        self.assertEqual(done.data["stop_reason"], "stop")

    @patch("copilot.client.requests.get")
    def test_max_iterations_guard_ends_the_turn(self, get):
        get.return_value = _rest_response(payload=_list_envelope([]))
        stub = MagicMock()
        stub.chat.completions.create.side_effect = (
            lambda **kwargs: iter(_tool_turn("list_nodes", {}))
        )
        with self.settings(CELLO_COPILOT_MAX_TOOL_ITERATIONS=3, **SETTINGS):
            with patch("copilot.llm._get_client", return_value=stub):
                events = list(
                    stream_agent([{"role": "user", "content": "loop"}], _ctx())
                )
        self.assertEqual(events[-1].data["stop_reason"], "max_iterations")
        self.assertEqual(stub.chat.completions.create.call_count, 3)

    def test_unexpected_finish_reason_is_normalized(self):
        events = self._events(_text_turn("hi", finish_reason="content_filter"))
        self.assertEqual(events[-1].data["stop_reason"], "stop")

    def test_truncation_is_reported_rather_than_hidden(self):
        events = self._events(_text_turn("hi", finish_reason="length"))
        self.assertEqual(events[-1].data["stop_reason"], "length")

    def test_provider_errors_become_upstream_errors(self):
        import openai

        stub = MagicMock()
        stub.chat.completions.create.side_effect = openai.APIError(
            "bad key", request=MagicMock(), body=None
        )
        with self.settings(**SETTINGS):
            with patch("copilot.llm._get_client", return_value=stub):
                with self.assertRaises(AgentUpstreamError):
                    list(stream_agent([{"role": "user", "content": "hi"}], _ctx()))

    def test_missing_api_key_raises_config_error(self):
        with self.settings(CELLO_COPILOT_LLM_API_KEY=""):
            with self.assertRaises(AgentConfigError):
                list(stream_agent([{"role": "user", "content": "hi"}], _ctx()))

    def test_missing_model_raises_config_error(self):
        """No default model is possible: it depends on the base URL's vendor."""
        with self.settings(
            CELLO_COPILOT_LLM_API_KEY="k", CELLO_COPILOT_LLM_MODEL=""
        ):
            with self.assertRaises(AgentConfigError):
                list(stream_agent([{"role": "user", "content": "hi"}], _ctx()))


class RunAgentTests(TestCase):
    """The blocking helper has to agree with the stream it drains."""

    @patch("copilot.client.requests.get")
    def test_returns_the_final_answer_and_the_trace(self, get):
        get.return_value = _rest_response(
            payload=_list_envelope([{"name": "peer0"}])
        )
        stub = _stub_client(
            _tool_turn("list_nodes", {}), _text_turn("One node: peer0.")
        )
        with self.settings(**SETTINGS):
            with patch("copilot.llm._get_client", return_value=stub):
                result = run_agent([{"role": "user", "content": "nodes?"}], _ctx())

        self.assertEqual(result.stop_reason, "stop")
        self.assertIn("peer0", result.reply)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "list_nodes")


class ClientConfigTests(TestCase):
    """The base URL is what makes the runner vendor-agnostic, so pin it."""

    @patch("openai.OpenAI")
    def test_base_url_is_forwarded_when_set(self, openai_cls):
        with self.settings(
            CELLO_COPILOT_LLM_API_KEY="k",
            CELLO_COPILOT_LLM_BASE_URL="https://api.deepseek.com",
        ):
            llm._get_client()
        self.assertEqual(
            openai_cls.call_args.kwargs["base_url"], "https://api.deepseek.com"
        )

    @patch("openai.OpenAI")
    def test_base_url_is_omitted_when_empty(self, openai_cls):
        """An empty base URL has to fall through to the SDK default rather than
        be passed as an empty string, which the client rejects."""
        with self.settings(
            CELLO_COPILOT_LLM_API_KEY="k", CELLO_COPILOT_LLM_BASE_URL=""
        ):
            llm._get_client()
        self.assertNotIn("base_url", openai_cls.call_args.kwargs)


class ProviderSelectionTests(TestCase):
    def test_registered_provider_is_dispatched_to(self):
        """Providers are looked up by name. This is the seam a second protocol
        plugs into without the tool layer changing."""
        sentinel = [Event("done", {"reply": "stub", "stop_reason": "stop",
                                   "tool_calls": []})]
        with patch.dict(llm._PROVIDERS, {"stub": lambda m, c: iter(sentinel)}):
            with self.settings(CELLO_COPILOT_LLM_PROVIDER="stub"):
                result = run_agent([{"role": "user", "content": "hi"}], _ctx())
        self.assertEqual(result.reply, "stub")

    def test_unknown_provider_raises_config_error(self):
        with self.settings(CELLO_COPILOT_LLM_PROVIDER="does-not-exist"):
            with self.assertRaises(AgentConfigError):
                stream_agent([{"role": "user", "content": "hi"}], _ctx())


class SseFramingTests(TestCase):
    def test_frame_shape(self):
        text = sse.frame("token", {"text": "hi"})
        self.assertEqual(text, 'event: token\ndata: {"text":"hi"}\n\n')

    def test_comments_are_not_events(self):
        self.assertEqual(sse.comment(), ": ping\n\n")

    def test_keepalive_is_emitted_while_the_worker_is_quiet(self):
        import time

        def slow():
            time.sleep(0.25)
            yield Event("done", {"reply": "late"})

        stream = sse.EventStream(slow(), keepalive=0.05)
        stream.start()
        output = list(stream.frames())
        self.assertIn(": ping\n\n", output)
        self.assertTrue(output[-1].startswith("event: done"))

    def test_a_failure_mid_stream_becomes_an_error_frame(self):
        def explodes():
            yield Event("token", {"text": "hi"})
            raise AgentUpstreamError("provider went away")

        stream = sse.EventStream(explodes())
        stream.start()
        output = "".join(stream.frames())
        self.assertIn("event: error", output)
        self.assertIn("upstream_error", output)
        self.assertNotIn("event: done", output)


class ChatEndpointTests(APITestCase):
    url = "/api/v1/copilot/chat"

    def setUp(self):
        self.org = Organization.objects.create(
            name="OrgA", agent_url="http://agent.example.com:5001"
        )
        self.user = UserProfile.objects.create(
            username="alice", email="alice@example.com", organization=self.org
        )
        token = str(AccessToken.for_user(self.user))
        self.client.credentials(HTTP_AUTHORIZATION="JWT %s" % token)

    def _post(self, content="hi"):
        return self.client.post(
            self.url,
            {"messages": [{"role": "user", "content": content}]},
            format="json",
        )

    def _body(self, response):
        return b"".join(response.streaming_content).decode()

    def test_requires_auth(self):
        self.client.credentials()
        self.assertEqual(self._post().status_code, 401)

    def test_rejects_empty_messages(self):
        resp = self.client.post(self.url, {"messages": []}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_last_message_must_be_from_the_user(self):
        resp = self.client.post(
            self.url,
            {"messages": [{"role": "assistant", "content": "hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("copilot.views.stream_agent")
    def test_happy_path_streams_sse(self, stream):
        stream.return_value = iter(
            [
                Event("token", {"text": "two peers"}),
                Event(
                    "done",
                    {
                        "reply": "two peers",
                        "stop_reason": "stop",
                        "tool_calls": [],
                    },
                ),
            ]
        )
        resp = self._post("how many peers?")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Type"], "text/event-stream; charset=utf-8"
        )
        self.assertEqual(resp["Cache-Control"], "no-cache")
        self.assertEqual(resp["X-Accel-Buffering"], "no")

        body = self._body(resp)
        self.assertIn("event: token", body)
        self.assertTrue(body.rstrip().endswith('"tool_calls":[]}'))
        # The caller's own JWT reaches the tool context.
        self.assertTrue(
            stream.call_args.kwargs["context"].auth_header.startswith("JWT ")
        )

    @patch("copilot.views.stream_agent")
    def test_unconfigured_is_a_503_before_the_stream_opens(self, stream):
        def unconfigured():
            raise AgentConfigError("no key")
            yield  # pragma: no cover - makes this a generator

        stream.return_value = unconfigured()
        resp = self._post()
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.data["status"], "FAILED")

    @patch("copilot.views.stream_agent")
    def test_upstream_failure_is_a_502_not_a_traceback(self, stream):
        """A bad key must not surface as an unhandled 500. With DEBUG on,
        Django's error page would echo settings back to the caller."""

        def unreachable():
            raise AgentUpstreamError("Error code: 401 - invalid api key")
            yield  # pragma: no cover - makes this a generator

        stream.return_value = unreachable()
        resp = self._post()
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.data["status"], "FAILED")

    @patch("copilot.views.stream_agent")
    def test_failure_after_the_first_token_arrives_as_a_frame(self, stream):
        """Once the status line is out, an error can only be an event."""

        def dies_midway():
            yield Event("token", {"text": "checking"})
            raise AgentUpstreamError("connection reset")

        stream.return_value = dies_midway()
        resp = self._post()
        self.assertEqual(resp.status_code, 200)
        body = self._body(resp)
        self.assertIn("event: error", body)
        self.assertIn("upstream_error", body)

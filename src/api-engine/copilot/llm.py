#
# SPDX-License-Identifier: Apache-2.0
#
"""Tool-calling loop for the Cello copilot.

The provider is not fixed. ``CELLO_COPILOT_LLM_PROVIDER`` picks a runner out of
``_PROVIDERS`` and the SDK is imported lazily, so only the configured provider's
package has to be installed. The bundled runner speaks the OpenAI
chat-completions protocol, which most vendors implement, so pointing
``CELLO_COPILOT_LLM_BASE_URL`` at DeepSeek, OpenRouter, Together, Groq or a local
Ollama is a config change rather than a code change. A vendor with its own
protocol adds one ``_stream_x`` function here plus a schema converter in
``copilot.tools``.

The loop is a generator of events:

    user message
      -> model (with tool schemas), streaming text back token by token
        -> while the model asks for a tool: run it, feed the result back
          -> a final ``done`` event carrying the whole reply

``run_agent`` drains that generator for callers that only want the final answer,
so there is one loop rather than a streaming copy and a blocking copy.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List

from django.conf import settings

from copilot.tools import ToolContext, openai_tool_schemas, run_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the Cello operations assistant, embedded in the Hyperledger "
    "Cello dashboard. You help an operator inspect their Hyperledger Fabric "
    "deployment (nodes, channels, chaincodes, organizations). "
    "You are READ-ONLY: you can look things up via tools but cannot create, "
    "modify or delete anything. If asked to make a change, explain that "
    "write operations are not yet supported and point to the dashboard. "
    "Prefer calling a tool over guessing. Answer concisely; when you list "
    "resources, summarize counts and notable items rather than dumping raw "
    "JSON."
)

# The values the ``done`` frame may carry, per the contract in #813. Anything
# else a provider reports is normalized to "stop" so clients can switch on a
# closed set. "length" means the model was cut off by max_tokens.
STOP_REASONS = frozenset(
    ["stop", "end_turn", "length", "max_iterations", "error"]
)


class AgentConfigError(RuntimeError):
    """Misconfiguration, such as a missing API key. A 5xx, not a user error."""


class AgentUpstreamError(RuntimeError):
    """The LLM provider rejected or failed the call.

    Bad key, rate limit, unknown model, unreachable endpoint. Providers raise
    their own SDK exceptions and each runner translates them into this one, so
    the view never imports a provider SDK just to catch its errors.
    """


@dataclass
class ToolCallTrace:
    name: str
    input: dict
    output: dict


@dataclass
class AgentResult:
    reply: str
    tool_calls: List[ToolCallTrace] = field(default_factory=list)
    stop_reason: str = "end_turn"


@dataclass
class Event:
    """One SSE frame: ``name`` is the event type, ``data`` its JSON payload."""

    name: str
    data: Dict[str, Any]


@dataclass
class _Config:
    model: str
    max_tokens: int
    max_iterations: int


def _config() -> _Config:
    model = getattr(settings, "CELLO_COPILOT_LLM_MODEL", "")
    if not model:
        raise AgentConfigError(
            "CELLO_COPILOT_LLM_MODEL is not set. It has no safe default: the "
            "right value depends on which vendor CELLO_COPILOT_LLM_BASE_URL "
            "points at."
        )
    return _Config(
        model=model,
        max_tokens=int(getattr(settings, "CELLO_COPILOT_MAX_TOKENS", 1024)),
        max_iterations=int(
            getattr(settings, "CELLO_COPILOT_MAX_TOOL_ITERATIONS", 8)
        ),
    )


def _normalize_stop(reason: str) -> str:
    return reason if reason in STOP_REASONS else "stop"


# --------------------------------------------------------------------------
# OpenAI-compatible provider, against any vendor implementing the
# chat-completions protocol at CELLO_COPILOT_LLM_BASE_URL.
# --------------------------------------------------------------------------


def _get_client():
    """Build the chat-completions client, or raise ``AgentConfigError``."""
    api_key = getattr(settings, "CELLO_COPILOT_LLM_API_KEY", "")
    if not api_key:
        raise AgentConfigError(
            "CELLO_COPILOT_LLM_API_KEY is not set; the copilot cannot reach "
            "the LLM."
        )
    try:
        import openai
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise AgentConfigError("The 'openai' package is not installed.") from exc

    kwargs = {"api_key": api_key}
    # An empty base URL means "use the SDK default" (api.openai.com). Any other
    # value points at a compatible vendor.
    base_url = getattr(settings, "CELLO_COPILOT_LLM_BASE_URL", "")
    if base_url:
        kwargs["base_url"] = base_url
    return openai.OpenAI(**kwargs)


def _drain(stream, state: dict) -> Iterator[str]:
    """Yield assistant text as it arrives, collecting tool calls into ``state``.

    Tool calls arrive split across chunks: the id and function name land in the
    first delta for a given index and the JSON arguments dribble in after, so
    each field is concatenated rather than assigned.
    """
    calls = state.setdefault("calls", {})
    for chunk in stream:
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        if choice.finish_reason:
            state["finish_reason"] = choice.finish_reason
        delta = choice.delta
        if delta is None:
            continue

        text = getattr(delta, "content", None)
        if text:
            state["content"] = state.get("content", "") + text
            yield text

        for part in getattr(delta, "tool_calls", None) or []:
            slot = calls.setdefault(
                part.index, {"id": "", "name": "", "arguments": ""}
            )
            if part.id:
                slot["id"] = part.id
            function = getattr(part, "function", None)
            if function is None:
                continue
            if function.name:
                slot["name"] += function.name
            if function.arguments:
                slot["arguments"] += function.arguments


def _stream_openai_compatible(
    messages: List[dict], context: ToolContext
) -> Iterator[Event]:
    client = _get_client()
    cfg = _config()
    schemas = openai_tool_schemas()
    convo = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
    trace: List[ToolCallTrace] = []

    import openai  # _get_client already proved this imports

    for _ in range(cfg.max_iterations):
        try:
            stream = client.chat.completions.create(
                model=cfg.model,
                max_tokens=cfg.max_tokens,
                tools=schemas,
                messages=convo,
                stream=True,
            )
            state: dict = {}
            for text in _drain(stream, state):
                yield Event("token", {"text": text})
        except openai.APIError as exc:
            # Covers auth, rate limit, unknown model and connection failures.
            logger.warning("Cello copilot LLM call failed: %s", exc)
            raise AgentUpstreamError(str(exc)) from exc

        calls = [state["calls"][i] for i in sorted(state.get("calls", {}))]
        content = state.get("content", "")

        if not calls:
            yield Event(
                "done",
                _done_payload(
                    content.strip(),
                    trace,
                    _normalize_stop(state.get("finish_reason") or "stop"),
                ),
            )
            return

        # Echo the assistant's tool-call turn back, then answer each call.
        convo.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {
                        "id": call["id"],
                        "type": "function",
                        "function": {
                            "name": call["name"],
                            "arguments": call["arguments"] or "{}",
                        },
                    }
                    for call in calls
                ],
            }
        )
        for call in calls:
            try:
                params = json.loads(call["arguments"] or "{}")
            except ValueError:
                # A model can emit malformed JSON. Run the tool with no
                # arguments rather than dropping the call.
                params = {}
            yield Event(
                "tool_call",
                {"id": call["id"], "name": call["name"], "input": params},
            )
            output = run_tool(call["name"], params, context)
            trace.append(
                ToolCallTrace(name=call["name"], input=params, output=output)
            )
            yield Event(
                "tool_result",
                {
                    "id": call["id"],
                    "name": call["name"],
                    "ok": bool(output.get("ok", True)),
                    "output": output,
                },
            )
            convo.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(output),
                }
            )

    logger.warning(
        "Cello copilot hit max tool iterations (%s) without finishing",
        cfg.max_iterations,
    )
    yield Event(
        "done",
        _done_payload(
            "I wasn't able to finish that within the allowed number of steps. "
            "Please narrow the question and try again.",
            trace,
            "max_iterations",
        ),
    )


def _done_payload(reply, trace, stop_reason):
    return {
        "reply": reply,
        "stop_reason": stop_reason,
        "tool_calls": [
            {"name": t.name, "input": t.input, "output": t.output} for t in trace
        ],
    }


# --------------------------------------------------------------------------
# Provider registry. A vendor with its own protocol adds a runner here and a
# schema converter in copilot.tools; the tool layer itself does not change.
# --------------------------------------------------------------------------

_PROVIDERS: Dict[str, Callable[[List[dict], ToolContext], Iterator[Event]]] = {
    "openai_compatible": _stream_openai_compatible,
}


def stream_agent(messages: List[dict], context: ToolContext) -> Iterator[Event]:
    """Run the tool-calling loop, yielding events as they happen.

    ``messages`` is the running conversation in role/content form. ``context``
    carries the caller's auth header and the Cello API root, and scopes every
    tool call. The last event of a successful turn is always ``done``.
    """
    provider = getattr(
        settings, "CELLO_COPILOT_LLM_PROVIDER", "openai_compatible"
    )
    runner = _PROVIDERS.get(provider)
    if runner is None:
        raise AgentConfigError(
            "Unsupported CELLO_COPILOT_LLM_PROVIDER '%s'. Supported: %s."
            % (provider, ", ".join(sorted(_PROVIDERS)))
        )
    return runner(messages, context)


def run_agent(messages: List[dict], context: ToolContext) -> AgentResult:
    """Run the loop to completion and return only the final answer.

    Kept for callers that have no use for intermediate events. It drives the
    same generator as the streaming path, so the two cannot drift.
    """
    final = None
    for event in stream_agent(messages, context):
        if event.name == "done":
            final = event.data
    if final is None:  # pragma: no cover - a runner that never finishes
        raise AgentUpstreamError("The provider ended the turn without a reply.")
    return AgentResult(
        reply=final["reply"],
        tool_calls=[
            ToolCallTrace(name=c["name"], input=c["input"], output=c["output"])
            for c in final["tool_calls"]
        ],
        stop_reason=final["stop_reason"],
    )

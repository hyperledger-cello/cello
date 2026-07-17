#
# SPDX-License-Identifier: Apache-2.0
#
"""LLM tool-calling loop for the Cello operations agent.

A synchronous, non-streaming loop. The **provider is not fixed**:
``CELLO_AGENT_LLM_PROVIDER`` selects a runner from ``_PROVIDERS``, and the SDK is
imported lazily so only the configured provider's package must be installed.

The bundled provider speaks the OpenAI chat-completions protocol, which most
vendors implement. Pointing ``CELLO_AGENT_LLM_BASE_URL`` at a different endpoint
is enough to run against DeepSeek, OpenRouter, Together, Groq or a local Ollama
-- no code change. A vendor with its own protocol adds one ``_run_x`` function
here plus a schema converter in ``agent.tools``; nothing else moves. Streaming is
a follow-up.

    user message
      -> model (with tool schemas)
        -> while the model asks for a tool: run it, feed the result back
          -> return the final assistant text + a trace of tool calls

Every provider drives the **same** read-only tool registry in ``agent.tools``,
which calls Cello's REST API as the logged-in user.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from django.conf import settings

from agent.tools import ToolContext, openai_tool_schemas, run_tool

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


class AgentConfigError(RuntimeError):
    """Misconfiguration (e.g. missing API key) -- a 5xx, not a user error."""


class AgentUpstreamError(RuntimeError):
    """The LLM provider rejected or failed the call (bad key, rate limit,
    unknown model, unreachable endpoint).

    Providers raise their own SDK exceptions; each runner translates them into
    this one so the view never imports a provider SDK to handle errors.
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
class _Config:
    model: str
    max_tokens: int
    max_iterations: int


def _config() -> _Config:
    return _Config(
        model=getattr(settings, "CELLO_AGENT_LLM_MODEL", ""),
        max_tokens=int(getattr(settings, "CELLO_AGENT_MAX_TOKENS", 1024)),
        max_iterations=int(
            getattr(settings, "CELLO_AGENT_MAX_TOOL_ITERATIONS", 8)
        ),
    )


def _hit_max(trace: List[ToolCallTrace], max_iterations: int) -> AgentResult:
    logger.warning(
        "Cello agent hit max tool iterations (%s) without finishing",
        max_iterations,
    )
    return AgentResult(
        reply=(
            "I wasn't able to finish that within the allowed number of steps. "
            "Please narrow the question and try again."
        ),
        tool_calls=trace,
        stop_reason="max_iterations",
    )


# --------------------------------------------------------------------------
# OpenAI-compatible provider. Works against any vendor implementing the
# chat-completions protocol; the endpoint is CELLO_AGENT_LLM_BASE_URL.
# --------------------------------------------------------------------------


def _get_client():
    """Build the chat-completions client, or raise AgentConfigError."""
    api_key = getattr(settings, "CELLO_AGENT_LLM_API_KEY", "")
    if not api_key:
        raise AgentConfigError(
            "CELLO_AGENT_LLM_API_KEY is not set; the agent cannot reach the LLM."
        )
    try:
        import openai
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise AgentConfigError(
            "The 'openai' package is not installed."
        ) from exc

    kwargs = {"api_key": api_key}
    # Empty base URL means "use the SDK default" (api.openai.com); any other
    # value points at a compatible vendor (DeepSeek, OpenRouter, Ollama, ...).
    base_url = getattr(settings, "CELLO_AGENT_LLM_BASE_URL", "")
    if base_url:
        kwargs["base_url"] = base_url
    return openai.OpenAI(**kwargs)


def _run_openai_compatible(
    messages: List[dict], context: ToolContext
) -> AgentResult:
    client = _get_client()
    cfg = _config()
    tools = openai_tool_schemas()
    convo = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
    trace: List[ToolCallTrace] = []

    import openai  # _get_client already proved this imports

    for _ in range(cfg.max_iterations):
        try:
            resp = client.chat.completions.create(
                model=cfg.model,
                max_tokens=cfg.max_tokens,
                tools=tools,
                messages=convo,
            )
        except openai.APIError as exc:
            # Covers auth, rate limit, unknown model and connection failures.
            logger.warning("Cello agent LLM call failed: %s", exc)
            raise AgentUpstreamError(str(exc)) from exc
        message = resp.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if not tool_calls:
            return AgentResult(
                reply=(message.content or "").strip(),
                tool_calls=trace,
                stop_reason=resp.choices[0].finish_reason or "stop",
            )

        # Echo the assistant's tool-call turn, then answer each call.
        convo.append(message.model_dump(exclude_none=True))
        for call in tool_calls:
            try:
                params = json.loads(call.function.arguments or "{}")
            except ValueError:
                params = {}
            output = run_tool(call.function.name, params, context)
            trace.append(
                ToolCallTrace(
                    name=call.function.name, input=params, output=output
                )
            )
            convo.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(output),
                }
            )

    return _hit_max(trace, cfg.max_iterations)


# --------------------------------------------------------------------------
# Provider registry. A vendor with its own protocol adds one runner here and a
# schema converter in agent.tools -- the tool layer itself does not change.
# --------------------------------------------------------------------------

_PROVIDERS: Dict[str, Callable[[List[dict], ToolContext], AgentResult]] = {
    "openai_compatible": _run_openai_compatible,
}


def run_agent(messages: List[dict], context: ToolContext) -> AgentResult:
    """Run the tool-calling loop to completion against the configured provider.

    ``messages`` is the running conversation in role/content form
    ([{"role": "user"|"assistant", "content": ...}]). ``context`` (a
    ``ToolContext``) carries the caller's auth header + API base and scopes every
    tool call. Returns the final assistant text and a tool-call trace.
    """
    provider = getattr(settings, "CELLO_AGENT_LLM_PROVIDER", "openai_compatible")
    runner = _PROVIDERS.get(provider)
    if runner is None:
        raise AgentConfigError(
            f"Unsupported CELLO_AGENT_LLM_PROVIDER '{provider}'. "
            f"Supported: {', '.join(sorted(_PROVIDERS))}."
        )
    return runner(messages, context)

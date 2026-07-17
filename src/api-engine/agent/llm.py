#
# SPDX-License-Identifier: Apache-2.0
#
"""LLM tool-calling loop for the Cello operations agent.

A synchronous, non-streaming loop. The **provider is swappable**:
``CELLO_AGENT_LLM_PROVIDER`` selects a backend from ``_PROVIDERS`` and each SDK
is imported lazily, so only the configured provider's package must be installed.
Anthropic is the only one implemented here -- a second provider is a follow-up
that adds one function, which is the point of the seam. Streaming is a separate
follow-up. The loop is deliberately small:

    user message
      -> model (with tool schemas)
        -> while the model asks for a tool: run it, feed the result back
          -> return the final assistant text + a trace of tool calls

Providers drive the **same** read-only tool registry in ``agent.tools``, which
calls Cello's REST API as the logged-in user.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from django.conf import settings

from agent.tools import ToolContext, anthropic_tool_schemas, run_tool

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
        model=getattr(settings, "CELLO_AGENT_LLM_MODEL", "claude-sonnet-4-6"),
        max_tokens=int(getattr(settings, "CELLO_AGENT_MAX_TOKENS", 1024)),
        max_iterations=int(
            getattr(settings, "CELLO_AGENT_MAX_TOOL_ITERATIONS", 8)
        ),
    )


def _api_key(*names: str) -> str:
    for name in names:
        key = getattr(settings, name, "")
        if key:
            return key
    return ""


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
# Anthropic provider
# --------------------------------------------------------------------------


def _get_client():
    """Build the Anthropic client, or raise AgentConfigError."""
    api_key = _api_key("ANTHROPIC_API_KEY")
    if not api_key:
        raise AgentConfigError(
            "ANTHROPIC_API_KEY is not set; the agent cannot reach the LLM."
        )
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise AgentConfigError(
            "The 'anthropic' package is not installed."
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


def _run_anthropic(messages: List[dict], context: ToolContext) -> AgentResult:
    client = _get_client()
    cfg = _config()
    tools = anthropic_tool_schemas()
    convo = list(messages)
    trace: List[ToolCallTrace] = []

    for _ in range(cfg.max_iterations):
        resp = client.messages.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=convo,
        )

        if resp.stop_reason != "tool_use":
            text = "".join(
                block.text
                for block in resp.content
                if getattr(block, "type", None) == "text"
            )
            return AgentResult(
                reply=text.strip(),
                tool_calls=trace,
                stop_reason=resp.stop_reason,
            )

        # Record the assistant's tool-use turn verbatim, then answer each call.
        convo.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            output = run_tool(block.name, block.input, context)
            trace.append(
                ToolCallTrace(name=block.name, input=block.input, output=output)
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                }
            )
        convo.append({"role": "user", "content": tool_results})

    return _hit_max(trace, cfg.max_iterations)


# --------------------------------------------------------------------------
# Provider registry. Adding a provider means writing one ``_run_x`` that drives
# the same tool registry and registering it here -- nothing else changes.
# --------------------------------------------------------------------------

_PROVIDERS: Dict[str, Callable[[List[dict], ToolContext], AgentResult]] = {
    "anthropic": _run_anthropic,
}


def run_agent(messages: List[dict], context: ToolContext) -> AgentResult:
    """Run the tool-calling loop to completion against the configured provider.

    ``messages`` is the running conversation in role/content form
    ([{"role": "user"|"assistant", "content": ...}]). ``context`` (a
    ``ToolContext``) carries the caller's auth header + API base and scopes every
    tool call. Returns the final assistant text and a tool-call trace.
    """
    provider = getattr(settings, "CELLO_AGENT_LLM_PROVIDER", "anthropic")
    runner = _PROVIDERS.get(provider)
    if runner is None:
        raise AgentConfigError(
            f"Unsupported CELLO_AGENT_LLM_PROVIDER '{provider}'. "
            f"Supported: {', '.join(sorted(_PROVIDERS))}."
        )
    return runner(messages, context)

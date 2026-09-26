#
# SPDX-License-Identifier: Apache-2.0
#
"""Tool registry the copilot exposes to the model.

The registry holds names, descriptions and JSON schemas. The queries themselves
are in ``copilot.client``, which knows nothing about LLMs, so a second caller
(the MCP server) can use them without dragging this layer along.

Every tool is read-only. Write tools stay out until API-key auth and RBAC land
(#764, #798), which is the posture agreed in #813.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List

from copilot import client


@dataclass
class ToolContext:
    """What a tool needs from the request, without the request itself.

    ``auth_header`` is the caller's own ``Authorization`` header, forwarded
    verbatim, so Cello scopes every response by the logged-in user exactly as it
    does for the dashboard. ``api_base`` is the API root, for example
    ``http://localhost:8080/api/v1``.
    """

    auth_header: str
    api_base: str


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    func: Callable[..., dict]


class UnknownToolError(KeyError):
    pass


_REGISTRY: Dict[str, Tool] = {}

_LIMIT_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "Maximum items to return (default 50).",
        }
    },
    "required": [],
}

_NO_ARGS_SCHEMA = {"type": "object", "properties": {}, "required": []}


def tool(name, description, input_schema=None):
    """Register a tool callable as ``func(context, **params)``."""

    def decorator(func):
        _REGISTRY[name] = Tool(
            name=name,
            description=description,
            input_schema=input_schema or _NO_ARGS_SCHEMA,
            func=func,
        )
        return func

    return decorator


def get_tools() -> List[Tool]:
    return list(_REGISTRY.values())


def openai_tool_schemas() -> List[dict]:
    """Tool definitions shaped for the OpenAI chat-completions API.

    This sits beside the registry rather than inside the provider runner so a
    vendor with a different schema format adds one converter over the same
    ``Tool`` objects and nothing else moves.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in _REGISTRY.values()
    ]


def run_tool(name: str, params: dict, context: ToolContext) -> dict:
    """Execute a registered tool, or raise ``UnknownToolError``.

    A tool that blows up returns a structured error instead of propagating, so
    one bad call does not abort the turn. The model reads the error and can say
    what went wrong or try something else.
    """
    if name not in _REGISTRY:
        raise UnknownToolError(name)
    try:
        return _REGISTRY[name].func(context, **(params or {}))
    except Exception as exc:  # noqa: BLE001 - handed to the model, not raised
        return {
            "ok": False,
            "error": "tool '%s' failed" % name,
            "detail": str(exc),
        }


@tool(
    "list_nodes",
    "List the blockchain nodes (peers and orderers) visible to the caller, "
    "with name, type and status.",
    _LIMIT_SCHEMA,
)
def list_nodes(context, limit=50):
    return client.list_nodes(context.api_base, context.auth_header, limit)


@tool(
    "list_channels",
    "List the Fabric channels visible to the caller.",
    _LIMIT_SCHEMA,
)
def list_channels(context, limit=50):
    return client.list_channels(context.api_base, context.auth_header, limit)


@tool(
    "list_chaincodes",
    "List the deployed chaincodes visible to the caller, with name and version.",
    _LIMIT_SCHEMA,
)
def list_chaincodes(context, limit=50):
    return client.list_chaincodes(context.api_base, context.auth_header, limit)


@tool(
    "list_organizations",
    "List the organizations visible to the caller.",
    _LIMIT_SCHEMA,
)
def list_organizations(context, limit=50):
    return client.list_organizations(context.api_base, context.auth_header, limit)


@tool(
    "check_health",
    "Check whether the Cello API Engine is reachable and answering. Use this "
    "when another tool reports a connection failure.",
    _NO_ARGS_SCHEMA,
)
def check_health(context):
    return client.check_health(context.api_base)

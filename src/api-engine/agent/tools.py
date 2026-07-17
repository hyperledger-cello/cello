#
# SPDX-License-Identifier: Apache-2.0
#
"""Read-only tool registry for the Cello AI operations agent.

Each tool calls Cello's **REST API over HTTP**, forwarding the caller's JWT, so
the agent acts as the logged-in user and every response is scoped server-side by
``request.user`` -- exactly like the dashboard. This mirrors the read-only
posture of the MCP server POC (``src/mcp-server/server.py``), whose ``_get`` /
error-handling shape this reuses. The difference: the MCP server logs in with a
service account, whereas this agent forwards the caller's existing token, so
there is no login/token-cache logic here.

Write tools are intentionally absent until API-key auth + RBAC land
(see #764 / #798).
"""
from dataclasses import dataclass
from typing import Callable, Dict, List

import requests


@dataclass
class ToolContext:
    """Everything a tool needs from the request, decoupled from HTTP handling.

    ``auth_header`` is the caller's ``Authorization`` header, forwarded verbatim
    to the REST API so scoping/permissions are inherited. ``api_base`` is the
    Cello API root, e.g. ``http://localhost:8080/api/v1``.
    """

    auth_header: str
    api_base: str


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    func: Callable[..., dict]


_REGISTRY: Dict[str, Tool] = {}

_TIMEOUT = 30.0


def tool(name: str, description: str, input_schema: dict = None):
    """Register a read-only tool callable as ``func(context, **params)``."""

    def decorator(func: Callable[..., dict]) -> Callable[..., dict]:
        _REGISTRY[name] = Tool(
            name=name,
            description=description,
            input_schema=input_schema
            or {"type": "object", "properties": {}, "required": []},
            func=func,
        )
        return func

    return decorator


def get_tools() -> List[Tool]:
    return list(_REGISTRY.values())


def anthropic_tool_schemas() -> List[dict]:
    """Tool definitions in the shape the Anthropic API expects."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        }
        for t in _REGISTRY.values()
    ]


class UnknownToolError(KeyError):
    pass


def run_tool(name: str, params: dict, context: ToolContext) -> dict:
    """Execute a registered tool. Raises UnknownToolError if not found.

    Tool exceptions are caught and returned as a structured error dict so a
    single failing call never aborts the whole agent turn.
    """
    if name not in _REGISTRY:
        raise UnknownToolError(name)
    try:
        return _REGISTRY[name].func(context, **(params or {}))
    except Exception as exc:  # noqa: BLE001 - surfaced to the LLM, not raised
        return {
            "ok": False,
            "error": f"tool '{name}' failed",
            "detail": str(exc),
        }


# --------------------------------------------------------------------------
# HTTP helper -- lifted from mcp-server/server.py ``_get`` / ``_error``, but
# forwarding the caller's JWT instead of logging in. Never raises; returns a
# structured error dict so the LLM sees a message rather than the turn aborting.
# --------------------------------------------------------------------------


def _error(message: str, detail: str = "", hint: str = "") -> dict:
    payload = {"ok": False, "error": message}
    if detail:
        payload["detail"] = detail
    if hint:
        payload["hint"] = hint
    return payload


def _get(context: ToolContext, path: str, params: dict = None) -> dict:
    """Authenticated GET against the Cello REST API. Returns a dict.

    On success the parsed JSON body is returned under ``{"ok": True, ...}``;
    on any failure a structured ``{"ok": False, "error": ...}`` dict is returned.
    """
    url = f"{context.api_base.rstrip('/')}/{path.lstrip('/')}"
    if not context.auth_header:
        return _error(
            "No Authorization header to forward",
            hint="The agent must be called by an authenticated user.",
        )
    try:
        resp = requests.get(
            url,
            headers={"Authorization": context.auth_header},
            params=params,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.ConnectionError as exc:
        return _error(
            "Cello API is not reachable",
            detail=str(exc),
            hint="Verify the API Engine is running and CELLO_AGENT_API_BASE.",
        )
    except requests.exceptions.Timeout as exc:
        return _error("Cello API request timed out", detail=str(exc))
    except requests.exceptions.RequestException as exc:
        return _error("Cello API request failed", detail=str(exc))

    if resp.status_code == 401:
        return _error(
            "Cello rejected the request (HTTP 401)",
            detail=resp.text[:500],
            hint="The session token may be expired or lack permission.",
        )
    if resp.status_code >= 400:
        return _error(
            f"Cello API returned HTTP {resp.status_code}",
            detail=resp.text[:500],
            hint="Check the request and the Cello server state.",
        )
    try:
        return {"ok": True, "data": resp.json()}
    except ValueError:
        return _error(
            "Cello returned a non-JSON response",
            detail=resp.text[:500],
            hint="Check CELLO_AGENT_API_BASE points at the API root.",
        )


_MAX_PER_PAGE = 100  # common.serializers.PageQuerySerializer caps per_page at 100


def _envelope(body: dict) -> dict:
    """The list payload ``{"total": N, "data": [...]}`` from Cello's envelope.

    Cello returns ``{"status", "msg", "data": {"total": N, "data": [...]}}`` (via
    ``ok()``). ``_get`` nests the parsed JSON under ``body["data"]``. Be lenient
    so a shape tweak upstream degrades gracefully rather than raising.
    """
    payload = body.get("data", {})
    inner = payload.get("data", payload) if isinstance(payload, dict) else {}
    return inner if isinstance(inner, dict) else {}


def _items(body: dict) -> list:
    inner = _envelope(body).get("data", [])
    return inner if isinstance(inner, list) else []


def _total(body: dict) -> int:
    """Total count from the list envelope, falling back to the page length."""
    inner = _envelope(body)
    total = inner.get("total")
    return int(total) if isinstance(total, int) else len(_items(body))


# --------------------------------------------------------------------------
# Read-only tools. ``list_nodes`` is the only one here on purpose: it proves the
# whole path (chat -> LLM -> tool -> REST -> back). Channels, chaincodes and
# organizations are the same shape against ``channels`` / ``chaincodes`` /
# ``organizations`` and follow once this shape is agreed.
# --------------------------------------------------------------------------

_PAGINATION_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "Max items to return (default 50).",
        }
    },
    "required": [],
}


@tool(
    "list_nodes",
    "List the blockchain nodes (peers/orderers) in the caller's "
    "organization, with name, type and status.",
    _PAGINATION_SCHEMA,
)
def list_nodes(context: ToolContext, limit: int = 50) -> dict:
    body = _get(context, "nodes", params={"per_page": min(limit, _MAX_PER_PAGE)})
    if not body.get("ok"):
        return body
    nodes = _items(body)[:limit]
    return {"ok": True, "count": len(nodes), "total": _total(body), "nodes": nodes}

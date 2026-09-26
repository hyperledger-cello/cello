#
# SPDX-License-Identifier: Apache-2.0
#
"""Read-only queries against Cello's REST API.

The caller supplies the API root and an ``Authorization`` header value, so this
module has no opinion about where the token comes from. The copilot forwards the
end user's JWT; the MCP server in ``src/mcp-server/`` logs in with a service
account and holds its own. Both need the same five queries, which is why they
live here rather than inside either caller.

No function raises. Failures come back as ``{"ok": False, "error": ...}`` so an
LLM sees a message it can explain instead of the request aborting. Callers that
want an exception can check the flag.
"""
import requests

TIMEOUT = 30.0
HEALTH_TIMEOUT = 10.0

# common.serializers.PageQuerySerializer rejects a per_page above this.
MAX_PER_PAGE = 100


def error(message, detail="", hint=""):
    payload = {"ok": False, "error": message}
    if detail:
        payload["detail"] = detail
    if hint:
        payload["hint"] = hint
    return payload


def get(api_base, auth_header, path, params=None):
    """Authenticated GET against the Cello REST API.

    Returns ``{"ok": True, "data": <parsed body>}`` or an error dict.
    """
    if not auth_header:
        return error(
            "No Authorization header to forward",
            hint="This client must be called on behalf of an authenticated user.",
        )
    url = "%s/%s" % (api_base.rstrip("/"), path.lstrip("/"))
    try:
        resp = requests.get(
            url,
            headers={"Authorization": auth_header},
            params=params,
            timeout=TIMEOUT,
        )
    except requests.exceptions.ConnectionError as exc:
        return error(
            "Cello API is not reachable",
            detail=str(exc),
            hint="Verify the API Engine is running and the API base is correct.",
        )
    except requests.exceptions.Timeout as exc:
        return error("Cello API request timed out", detail=str(exc))
    except requests.exceptions.RequestException as exc:
        return error("Cello API request failed", detail=str(exc))

    if resp.status_code == 401:
        return error(
            "Cello rejected the request (HTTP 401)",
            detail=resp.text[:500],
            hint="The session token may be expired or lack permission.",
        )
    if resp.status_code >= 400:
        return error(
            "Cello API returned HTTP %s" % resp.status_code,
            detail=resp.text[:500],
            hint="Check the request and the Cello server state.",
        )
    try:
        return {"ok": True, "data": resp.json()}
    except ValueError:
        return error(
            "Cello returned a non-JSON response",
            detail=resp.text[:500],
            hint="Check the API base points at the API root.",
        )


# --------------------------------------------------------------------------
# List envelope. Cello wraps list payloads as
# {"status", "msg", "data": {"total": N, "data": [...]}} via common.responses.ok.
# ``get`` nests that under body["data"], so unwrapping is two levels. The lookups
# below are deliberately lenient: an upstream shape change should degrade to an
# empty list rather than raise inside a tool call.
# --------------------------------------------------------------------------


def _envelope(body):
    payload = body.get("data", {})
    inner = payload.get("data", payload) if isinstance(payload, dict) else {}
    return inner if isinstance(inner, dict) else {}


def items(body):
    inner = _envelope(body).get("data", [])
    return inner if isinstance(inner, list) else []


def total(body):
    """Total count reported by Cello, falling back to the page length."""
    reported = _envelope(body).get("total")
    return int(reported) if isinstance(reported, int) else len(items(body))


def _listing(api_base, auth_header, path, key, limit):
    body = get(
        api_base, auth_header, path, params={"per_page": min(limit, MAX_PER_PAGE)}
    )
    if not body.get("ok"):
        return body
    page = items(body)[:limit]
    return {"ok": True, "count": len(page), "total": total(body), key: page}


def list_nodes(api_base, auth_header, limit=50):
    return _listing(api_base, auth_header, "nodes", "nodes", limit)


def list_channels(api_base, auth_header, limit=50):
    return _listing(api_base, auth_header, "channels", "channels", limit)


def list_chaincodes(api_base, auth_header, limit=50):
    return _listing(api_base, auth_header, "chaincodes", "chaincodes", limit)


def list_organizations(api_base, auth_header, limit=50):
    return _listing(api_base, auth_header, "organizations", "organizations", limit)


def check_health(api_base):
    """Is the API Engine answering? Unauthenticated, so it works before login."""
    url = "%s/docs" % api_base.rstrip("/")
    try:
        resp = requests.get(url, timeout=HEALTH_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        return error(
            "Cello API health check timed out",
            detail=str(exc),
            hint="The API Engine may be starting up or overloaded.",
        )
    except requests.exceptions.RequestException as exc:
        return error(
            "Cello API is not reachable",
            detail=str(exc),
            hint="Start Cello with `make local` and verify the API base.",
        )

    healthy = 200 <= resp.status_code < 400
    payload = {"ok": healthy, "reachable": True, "status": resp.status_code}
    if not healthy:
        payload["hint"] = (
            "Reachable but returning server errors; check the API Engine logs."
            if resp.status_code >= 500
            else "Reachable but returned a client error; verify the API base."
        )
    return payload

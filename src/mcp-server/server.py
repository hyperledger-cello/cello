"""
Hyperledger Cello MCP Server

Read-only tools for querying the Cello API Engine
via JWT authentication.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Cello")

CELLO_API_BASE = os.environ.get(
    "CELLO_API_BASE", "http://localhost:8080/api/v1"
)
CELLO_CREDENTIALS_FILE = Path(
    os.environ.get("CELLO_CREDENTIALS_FILE", "~/.cello/credentials")
).expanduser()
CELLO_TOKEN_FILE = Path(
    os.environ.get("CELLO_TOKEN_FILE", "~/.cello/token")
).expanduser()

_TOKEN: Optional[str] = None


class CelloAuthError(RuntimeError):
    """Raised when credentials are missing/invalid or Cello rejects
    the login. Distinct from server/config failures that also occur
    while obtaining a token (5xx, non-JSON, missing token field)."""


def _json(data: dict) -> str:
    return json.dumps(data, indent=2)


def _error(message: str, detail: str = "", hint: str = "") -> str:
    payload = {"ok": False, "error": message}
    if detail:
        payload["detail"] = detail
    if hint:
        payload["hint"] = hint
    return _json(payload)


def _load_credentials() -> Tuple[str, str]:
    """Load service-account credentials from env or credentials file."""
    email = os.environ.get("CELLO_EMAIL")
    password = os.environ.get("CELLO_PASSWORD")
    if email and password:
        return email, password

    if CELLO_CREDENTIALS_FILE.exists():
        try:
            raw = CELLO_CREDENTIALS_FILE.read_text()
        except OSError as exc:
            raise CelloAuthError(
                f"Cannot read credentials file "
                f"{CELLO_CREDENTIALS_FILE}: {exc}"
            ) from exc

        values = {}
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

        email = values.get("CELLO_EMAIL")
        password = values.get("CELLO_PASSWORD")
        if email and password:
            return email, password

        raise CelloAuthError(
            f"Credentials file {CELLO_CREDENTIALS_FILE} exists but is "
            "missing CELLO_EMAIL and/or CELLO_PASSWORD."
        )

    raise CelloAuthError(
        "Cello credentials are missing. Set CELLO_EMAIL and "
        "CELLO_PASSWORD environment variables, or create a "
        f"credentials file at {CELLO_CREDENTIALS_FILE} with "
        "CELLO_EMAIL=... and CELLO_PASSWORD=... lines."
    )


def _read_token() -> Optional[str]:
    token = os.environ.get("CELLO_TOKEN")
    if token and token.lower() != "null":
        return token

    if not CELLO_TOKEN_FILE.exists():
        return None

    try:
        token = CELLO_TOKEN_FILE.read_text().strip()
    except OSError:
        # Cached token unreadable -> treat as a cache miss and let the
        # caller log in again rather than crash the tool.
        return None
    return token if token and token.lower() != "null" else None


def _write_token(token: str) -> None:
    try:
        CELLO_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        CELLO_TOKEN_FILE.write_text(token)
        CELLO_TOKEN_FILE.chmod(0o600)
    except OSError as exc:
        print(
            f"warning: could not cache token to {CELLO_TOKEN_FILE}: {exc}",
            file=sys.stderr,
        )


def _login() -> str:
    email, password = _load_credentials()
    url = f"{CELLO_API_BASE.rstrip('/')}/login"
    resp = httpx.post(
        url,
        json={"email": email, "password": password},
        timeout=30.0,
    )
    if resp.status_code in (400, 401, 403):
        raise CelloAuthError(
            f"Cello rejected login for '{email}' (HTTP "
            f"{resp.status_code}). Either the password is wrong, or "
            "the account was never registered. Try registering or fix the "
            f"credentials at {CELLO_CREDENTIALS_FILE}."
        )
    if resp.status_code >= 500:
        raise RuntimeError(
            f"Cello server error during login (HTTP "
            f"{resp.status_code}). The API Engine is reachable but "
            "unhealthy; check its logs and database connection."
        )
    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(
            "Cello login returned a non-JSON response. Verify "
            f"CELLO_API_BASE points at the API root ({CELLO_API_BASE})."
        ) from exc

    token = data.get("data", {}).get("token")
    if not token or token == "null":
        raise RuntimeError(
            "Cello login succeeded but returned no token; the API "
            "response shape may have changed (expected data.token)."
        )
    _write_token(token)
    return token


def _get_token(force_login: bool = False) -> str:
    global _TOKEN

    if not force_login and _TOKEN:
        return _TOKEN

    if not force_login:
        _TOKEN = _read_token()
        if _TOKEN:
            return _TOKEN

    _TOKEN = _login()
    return _TOKEN


def _get(path: str, params: dict = None) -> str:
    """Send authenticated GET request to Cello API."""
    url = f"{CELLO_API_BASE.rstrip('/')}/{path}"
    try:
        headers = {"Authorization": f"JWT {_get_token()}"}
        resp = httpx.get(url, headers=headers, params=params, timeout=30.0)
        if resp.status_code == 401:
            headers = {"Authorization": f"JWT {_get_token(force_login=True)}"}
            resp = httpx.get(url, headers=headers, params=params, timeout=30.0)
        if resp.status_code == 401:
            return _error(
                "Cello rejected the request after re-login (HTTP 401)",
                detail=resp.text[:500],
                hint=(
                    "Login works, but this account may lack "
                    "permission for this resource."
                ),
            )
        resp.raise_for_status()
        try:
            return _json(resp.json())
        except ValueError:
            return _error(
                "Cello returned a non-JSON response",
                detail=resp.text[:500],
                hint=(
                    "Check CELLO_API_BASE; the endpoint may have "
                    "returned HTML instead of JSON."
                ),
            )
    except CelloAuthError as exc:
        return _error(
            "Cello authentication failed",
            detail=str(exc),
        )
    except RuntimeError as exc:
        return _error(
            "Cello login could not complete",
            detail=str(exc),
        )
    except httpx.ConnectError as exc:
        return _error(
            "Cello API is not reachable",
            detail=str(exc),
            hint="Start Cello with `make local` and verify CELLO_API_BASE.",
        )
    except httpx.TimeoutException as exc:
        return _error(
            "Cello API request timed out",
            detail=str(exc),
            hint="Check that the API Engine is healthy and reachable.",
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        return _error(
            f"Cello API returned HTTP {status}",
            detail=exc.response.text,
            hint="Check the request parameters and the Cello server state.",
        )
    except httpx.RequestError as exc:
        return _error(
            "Cello API request failed",
            detail=str(exc),
            hint="Verify CELLO_API_BASE and local network connectivity.",
        )


@mcp.tool()
def list_nodes(page: int = 1, per_page: int = 100) -> str:
    """List all blockchain nodes in the organization.

    Returns node names, types (PEER/ORDERER),
    and creation timestamps.
    """
    return _get("nodes", {"page": page, "per_page": per_page})


@mcp.tool()
def list_channels(page: int = 1, per_page: int = 100) -> str:
    """List all channels in the organization."""
    return _get(
        "channels",
        {"page": page, "per_page": per_page},
    )


@mcp.tool()
def list_chaincodes(page: int = 1, per_page: int = 100) -> str:
    """List all deployed chaincodes."""
    return _get(
        "chaincodes",
        {"page": page, "per_page": per_page},
    )


@mcp.tool()
def list_organizations(page: int = 1, per_page: int = 100) -> str:
    """List all organizations."""
    return _get(
        "organizations",
        {"page": page, "per_page": per_page},
    )


@mcp.tool()
def check_health() -> str:
    """Check if the Cello API Engine is reachable."""
    url = f"{CELLO_API_BASE.rstrip('/')}/docs"
    try:
        resp = httpx.get(url, timeout=10.0)
        status = resp.status_code
        healthy = 200 <= status < 400
        payload = {
            "ok": healthy,
            "reachable": True,
            "status": status,
        }
        if not healthy:
            if status >= 500:
                payload["hint"] = (
                    "API is reachable but returning server errors; "
                    "check the API Engine logs."
                )
            else:
                payload["hint"] = (
                    "Reachable but returned a client error; verify "
                    "CELLO_API_BASE points at the API root."
                )
        return _json(payload)
    except httpx.TimeoutException as exc:
        return _error(
            "Cello API health check timed out",
            detail=str(exc),
            hint="The API Engine may be starting up or overloaded.",
        )
    except httpx.RequestError as exc:
        return _error(
            "Cello API is not reachable",
            detail=str(exc),
            hint="Start Cello with `make local` and verify CELLO_API_BASE.",
        )


if __name__ == "__main__":
    mcp.run()

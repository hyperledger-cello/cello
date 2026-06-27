# Cello MCP Server

A read-only MCP server for inspecting a Hyperledger Cello API Engine.
It logs in with `/api/v1/login`, caches the JWT, and exposes a few
query tools. It never creates, updates, or deletes anything.

## Tools

- `check_health`
- `list_nodes`
- `list_channels`
- `list_chaincodes`
- `list_organizations`

## Setup

Requires Python 3.10+.

```bash
cd src/mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Credentials

Provide a Cello account via environment variables:

```bash
export CELLO_EMAIL=user@example.com
export CELLO_PASSWORD=change_me
export CELLO_API_BASE=http://localhost:8080/api/v1 # optional
```

Or via `~/.cello/credentials`:

```bash
mkdir -p ~/.cello
cat > ~/.cello/credentials <<'EOF'
CELLO_EMAIL=user@example.com
CELLO_PASSWORD=change_me
EOF
chmod 600 ~/.cello/credentials
```

The JWT is cached at `~/.cello/token` (mode `0600`) and refreshed
automatically when it expires.

## MCP client config

Copy the example and replace the placeholder paths with absolute paths
on your machine:

```bash
cp .mcp.example.json .mcp.json
```

## Test

1. Start Cello: `make local`
2. Reload your MCP client and confirm the `cello` server is connected.
3. Ask, in plain language:

   - "Is the Cello API healthy?"
   - "List the nodes in Cello."
   - "Show all channels and chaincodes."

The client picks the right tool automatically. If a call fails, the
tool returns a structured error (`ok`, `error`, `detail`, `hint`) that
explains what went wrong and what to do next.

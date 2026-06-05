---
name: cello
description: Read the status of a Hyperledger Cello deployment through its REST API. Use when the user asks to inspect Cello, Fabric networks, nodes, peers, orderers, channels, chaincodes, or organizations.
---

# Cello API

Read-only inspection of a running Cello API Engine.

## Setup

- **Base URL**: `http://localhost:8080/api/v1`
- **Credentials**: read from `~/.cello/credentials`, an env-style file
  with `CELLO_EMAIL=...` and `CELLO_PASSWORD=...` (create it once,
  `chmod 600`).
- **Auth**: send the JWT from `~/.cello/token` as the
  `Authorization: JWT <token>` header. If `~/.cello/token` is
  missing, run the login helper below first. Tokens expire after ~1
  hour, so on any `401` re-run the helper and retry the request.

Login helper:
```bash
mkdir -p ~/.cello
set -a; . ~/.cello/credentials; set +a
curl -s -X POST http://localhost:8080/api/v1/login \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"$CELLO_EMAIL\",\"password\":\"$CELLO_PASSWORD\"}" \
  | jq -r '.data.token' > ~/.cello/token
```

If `~/.cello/credentials` does not exist, ask the user to create it
instead of guessing. If it exists but the helper writes an empty
or `null` token, login failed — stop and ask the user to verify the
credentials in that file and that the API Engine is reachable. Don't
retry blindly.

All responses are wrapped as `{status, msg, data}`. List endpoints
paginate with `?page=1&per_page=10` (max per_page=100).

## Topics — load the matching file as needed

| User mentions… | Read this file |
|----------------|----------------|
| nodes, peers, orderers | `nodes.md` |
| channels | `channels.md` |
| chaincodes, smart contracts | `chaincodes.md` |
| organizations, members | `organizations.md` |

Load only the file relevant to the user's question, not all of them.

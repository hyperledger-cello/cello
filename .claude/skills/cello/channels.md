# Channels

A channel is a private communication subnet between organizations.
Fields: `id`, `name`, `organizations` (list of `{id}` objects),
`created_at`.

### List channels (names)
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/channels | jq -r '.data.data[] | .name'
```

### Count
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/channels | jq '.data.total'
```

### Full details
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/channels
```

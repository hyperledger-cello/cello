# Nodes

A node is a peer or orderer in the Fabric network.
Fields: `id`, `name`, `type` (PEER | ORDERER),
`status` (CREATED | RUNNING | FAILED), `created_at`.

### List nodes (summary)
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/nodes \
  | jq -r '.data.data[] | "\(.name) (\(.type), \(.status))"'
```

### Running peers only
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/nodes \
  | jq -r '.data.data[]
          | select(.type=="PEER" and .status=="RUNNING") | .name'
```

### Count
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/nodes | jq '.data.total'
```

### Full details (use only when fields above are insufficient)
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/nodes
```

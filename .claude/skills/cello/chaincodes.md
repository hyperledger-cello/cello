# Chaincodes

A chaincode is a smart contract deployed to a channel.
Fields: `id`, `name`, `version`, `sequence`, `init_required`,
`signature_policy`, `package_id`, `label`, `creator`, `channel`,
`language`, `description`, `status`, `approvals`, `created_at`.

### List chaincodes (name + version + status)
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/chaincodes \
  | jq -r '.data.data[] | "\(.name) v\(.version) [\(.status)]"'
```

### Count
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/chaincodes | jq '.data.total'
```

### Full details
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/chaincodes
```

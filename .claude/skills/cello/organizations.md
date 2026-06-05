# Organizations

An organization is the top-level tenant. Each user and resource
belongs to one. Fields exposed by the API: `id`, `name`, `created_at`.

### List organizations
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     'http://localhost:8080/api/v1/organizations?page=1&per_page=100' \
  | jq -r '.data.data[] | "\(.name) [\(.id)]"'
```

### Get one
```bash
curl -s -H "Authorization: JWT $(cat ~/.cello/token)" \
     http://localhost:8080/api/v1/organizations/<ORG_ID>
```

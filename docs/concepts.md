hero: All concepts related to cello

# Concepts

```mermaid
graph LR
    subgraph Network
        subgraph Channel
            subgraph Org A
                USER_A[User A]
                AGENT_A[Agent A]
                NODE_A[Node A]
            end

            subgraph Org B
                USER_B[User B]
                AGENT_B[Agent B]
                NODE_B[Node B]
            end

            subgraph Org C
                USER_C[User C]
                AGENT_C[Agent C]
                NODE_C[Node C]
            end
        end
    end

    subgraph Hyperledger Cello Server
        DASHBOARD[Dashboard]
        APIENGINE[API Engine]
        DB[(Database)]
    end

    USER_A --> DASHBOARD
    USER_B --> DASHBOARD
    USER_C --> DASHBOARD
    DASHBOARD --> APIENGINE
    APIENGINE --> DB
    APIENGINE --> AGENT_A
    APIENGINE --> AGENT_B
    APIENGINE --> AGENT_C
    AGENT_A --> |Create via CRI| NODE_A
    AGENT_B --> |Create via CRI| NODE_B
    AGENT_C --> |Create via CRI| NODE_C

```

## Server

### Components

*Components* are all the containers you need to run a Cello Server.

#### Dashboard

The Web UI of Cello.

#### API Engine

Api engine supply the core function, all operations through the api service.

Host path mappings:

* /opt/cello/api-engine/media:/var/www/media {>>store all media files<<}
* /var/run/docker.sock:/var/run/docker.sock {>>Used for agent containers launch, which will deploy fabric, eg. network<<}
* (==optional==) $ROOT_PATH/src/api-engine:/var/www/server {>>When run in debug mode, MODE=dev, will mapping the source code into container, ROOT_PATH is the source code path.<<}

#### Database

Store all the data in a postgres database, and the storage path is mapping out on the host.

Host path mappings:

* /opt/cello/postgres:/var/lib/postgresql/data {>>Store all db data.<<}

## Agent

### Kubernetes

### Fabric Operator

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
```

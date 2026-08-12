!!! example "How to config"

    ```bash
    $ CONFIG_VAR=xxx make start
    ```

## 1. Api Engine

all related configuration variable is written in ==.makerc/api-engine==.

???+ info "API_ENGINE_WEBROOT"

    **default**: `/engine`

    **description**: {>>Web ROOT for api engine, which defined the url where user can visit to api engine.<<}

    **usage**:
    ```bash
    $ API_ENGINE_WEBROOT=/engine make start
    ```


???+ info "API_ENGINE_SERVICE_PORT"

    **default**: `8085`

    **description**: {>>External port of api engine, only work for docker-compose deploy.<<}

    **usage**:
    ```bash
    $ API_ENGINE_SERVICE_PORT=8085 make start
    ```

???+ info "API_ENGINE_ADMIN_TOKEN"

    **default**: `administrator`

    **description**: {>>Default operator token of api engine, which have the maximum rights.<<}

    **usage**:
    ```bash
    $ API_ENGINE_ADMIN_TOKEN=administrator make start
    ```

???+ info "API_ENGINE_ADMIN_USERNAME"

    **default**: `admin`

    **description**: {>>Default operator username of api engine, who have the maximum rights.<<}

    **usage**:
    ```bash
    $ API_ENGINE_ADMIN_USERNAME=admin make start
    ```

???+ info "API_ENGINE_ADMIN_PASSWORD"

    **default**: `pass`

    **description**: {>>Default operator pass of api engine, who have the maximum rights.<<}

    **usage**:
    ```bash
    $ API_ENGINE_ADMIN_PASSWORD=pass make start
    ```

???+ info "API_ENGINE_ADMIN_EMAIL"

    **default**: `admin@cello.com`

    **description**: {>>Default admin email of api engine, who have the maximum rights.<<}

    **usage**:
    ```bash
    $ API_ENGINE_ADMIN_EMAIL=admin@cello.com make start
    ```

???+ info "API_DOCKER_HOST"

    **default**: `unix://var/run/docker.sock`

    **description**: {>>Docker host for launch agent container, can be unix socket or ip:port,
    if use remote docker host, remember download all agent images.<<}

    **usage**:
    ```bash
    $ API_DOCKER_HOST=unix://var/run/docker.sock make start
    ```

???+ info "API_VERSION"

    **default**: `master`

    **description**: {>>API version shown in swagger.<<}

    **usage**:
    ```bash
    $ API_VERSION=master make start
    ```

## 2. Dashboard

???+ info "DASHBOARD_SERVICE_PORT"

    **default**: `8085`

    **description**: {>>External port for dashboard, only work for docker-compose.<<}

    **usage**:
    ```bash
    $ DASHBOARD_SERVICE_PORT=8085 make start
    ```

Below configurations only work for `make start-dashboard-dev`, and must install all need node modules under the src/dashboard folder.

???+ info "MOCK"

    **default**: `True`

    **description**: {>>Whether start the dashboard with mock mode, all the data is mock.<<}

    **usage**:
    ```bash
    $ Mock=True make start-dashboard-dev
    ```

???+ info "PROXY"

    **default**: `empty`

    **description**: {>>When MOCK=False, this variable will have effect,
    set the api engine server url, where the api request will redirect to.<<}

    **usage**:
    ```bash
    $ PROXY=http://api-engine-server:8085/engine make start-dashboard-dev
    ```

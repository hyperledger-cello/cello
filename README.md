![Cello](docs/images/favicon.png)

[![Release](https://img.shields.io/github/v/release/hyperledger-cello/cello)](https://github.com/hyperledger-cello/cello/releases)
[![Build Status](https://github.com/hyperledger/cello/actions/workflows/docker-image.yml/badge.svg)](https://github.com/hyperledger/cello/actions/workflows/docker-image.yml)
[![License](https://img.shields.io/github/license/hyperledger-cello/cello)](https://github.com/hyperledger-cello/cello/blob/main/LICENSE)

Hyperledger Cello is a blockchain provision and operation system, which helps manage blockchain networks in an efficient way.

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Main Features](#main-features)
4. [Documentation](#documentation-getting-started-and-develop-guideline)
5. [Why named cello?](#why-named-cello)
6. [Notice](#incubation-notice)
7. [Inclusive Language Statement](#inclusive-language-statement)
   
## Introduction

Using Cello, everyone can easily:

* Build up a Blockchain as a Service (BaaS) platform quickly from scratch.
* Provision customizable Blockchains instantly, e.g., a Hyperledger fabric network v1.0.
* Maintain a pool of running blockchain networks on top of baremetals, Virtual Clouds (e.g., virtual machines, vsphere Clouds), Container clusters (e.g., Docker, Swarm, Kubernetes).
* Check the system status, adjust the chain numbers, scale resources... through dashboards.

A typical usage scenario is illustrated as:

![Typical Scenario](docs/images/scenario.png)

## Quick Start

Environmental preparation:

1. docker [how install](https://get.docker.com)
2. docker compose(`we switched to` [Docker Compose V2](https://docs.docker.com/compose/#compose-v2-and-the-new-docker-compose-command)) [how install](https://docs.docker.com/compose/install/)
3. make `all script for cello service management is written in Makefile`
4. kubernetes (`optional`) [how install](https://kubernetes.io/docs/setup/)
5. node [how install](https://nodejs.org/en/download/)

If environment is prepared, then we can start cello service.

* Set local storage environment variable, e.g. Use current path as storage path

  ```bash
  $  export CELLO_STORAGE_PATH=$(pwd)/cello
  ```


* Start service locally

  ```bash
  $ make local
  ```

* Optional: Build essential images for cello service (the docker hub image auto build haven't ready, in the future you can ignore this step.)

  * Build docker images
    ```bash
    $ make docker
    ```
  * Then run services locally then

    ```bash
    $ make start
    ```

* After service started up, if use docker-compose method, you can see output:

  ```bash
  CONTAINER ID   IMAGE                            COMMAND                  CREATED         STATUS         PORTS                                                                                  NAMES
  81e6459965ec   hyperledger/cello-agent-docker   "gunicorn server:app…"   4 seconds ago   Up 2 seconds   0.0.0.0:2375->2375/tcp, :::2375->2375/tcp, 0.0.0.0:5001->5001/tcp, :::5001->5001/tcp   cello.docker.agent
  04367ab6bd5e   postgres:11.1                    "docker-entrypoint.s…"   4 seconds ago   Up 2 seconds   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp                                              cello-postgres
  29b56a279893   hyperledger/cello-api-engine     "/bin/sh -c 'bash /e…"   4 seconds ago   Up 2 seconds   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp                                              cello-api-engine
  a272a06d8280   hyperledger/cello-dashboard      "bash -c 'nginx -g '…"   4 seconds ago   Up 2 seconds   80/tcp, 0.0.0.0:8081->8081/tcp, :::8081->8081/tcp                                      cello-dashboard
  ```

* Stop cello service.<!---, same as start, need set the `DEPLOY_METHOD` variable.-->

  ```bash
  $ make stop
  ```

* Clean all containers

  ```bash
  $ make clean
  ```

* Check available make rules

  ```bash
  $ make help
  ```

* Visit Cello dashboard at `localhost:8081`

* Check [troubleshoot](https://github.com/hyperledger/cello/blob/main/docs/setup/server.md#3-troubleshoot) section if you get any question.

## Main Features

* Manage the lifecycle of blockchains, e.g., create/start/stop/delete/keep health automatically.

* Support customized (e.g., size, consensus) blockchains request, currently we mainly support [Hyperledger fabric](https://github.com/hyperledger/fabric).

* Support native Docker host, swarm or Kubernetes as the worker nodes. More supports on the way.

* Support heterogeneous architecture, e.g., X86, POWER and Z, from bare-metal servers to virtual machines.

* Extend with monitor, log, health and analytics features by employing additional components.

## Documentation, Getting Started and Develop Guideline

For new users, it is highly recommended to read the [documentation](docs/index.md) first.

And feel free to visit the [online documentation](http://cello.readthedocs.io/en/latest/) for more information. You can also run `make doc` to start a local documentation website (Listen at [localhost:8000](http://127.0.0.1:8000).

## Why named Cello?

Can you find anyone better at playing chains? :)

## Incubation Notice

This project is a Hyperledger project in _Incubation_. It was proposed to the community and documented [here](https://docs.google.com/document/d/1E2i5GRqWsIag7KTxjQ_jQdDiWcuikv3KqXeuw7NaceM/edit), and was approved by [Hyperledger TSC at 2017-01-07](https://lists.hyperledger.org/pipermail/hyperledger-tsc/2017-January/000535.html). Information on what _Incubation_ entails can be found in the [Hyperledger Project Lifecycle document](https://goo.gl/4edNRc).

## Inclusive Language Statement

These guiding principles are very important to the maintainers and therefore
we respectfully ask all contributors to abide by them as well:

* Consider that users who will read the docs are from different backgrounds and
  cultures and that they have different preferences.
* Avoid potential offensive terms and, for instance, prefer "allow list and
  deny list" to "white list and black list".
* We believe that we all have a role to play to improve our world, and even if
  writing inclusive documentation might not look like a huge improvement, it's a
  first step in the right direction.
* We suggest to refer to
  [Microsoft bias free writing guidelines](https://docs.microsoft.com/en-us/style-guide/bias-free-communication)
  and
  [Google inclusive doc writing guide](https://developers.google.com/style/inclusive-documentation)
  as starting points.

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.

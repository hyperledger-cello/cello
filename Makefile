# Copyright IBM Corp, All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# -------------------------------------------------------------
# This makefile defines targets for Hyperledger Cello management.

# --- Configuration ---
DOCKER_NS ?= hyperledger
VERSION   ?= 0.9.0
IS_RELEASE ?= false

# Detect architecture and handle Mac arm64 compatibility
ARCH := $(shell uname -m)
ifeq ($(ARCH), arm64)
    ARCH := amd64
endif

# Tagging logic for local builds vs releases
ifeq ($(IS_RELEASE),false)
    EXTRA_VERSION ?= snapshot-$(shell git rev-parse --short HEAD)
    IMG_TAG := $(ARCH)-$(VERSION)-$(EXTRA_VERSION)
else
    IMG_TAG := $(ARCH)-$(VERSION)
endif

# Deployment mode: dev (default) or prod
MODE ?= dev
ifeq ($(MODE),prod)
    COMPOSE_FILE := bootup/docker-compose-files/docker-compose.yml
else
    COMPOSE_FILE := docker-compose.dev.yaml
endif

# Exports for Docker Compose and tests
export ROOT_PATH := $(shell pwd)
export IMG_TAG
.EXPORT_ALL_VARIABLES:

# Optional user-defined overrides
-include .config
-include .makerc/api-engine
-include .makerc/dashboard

# Tooling colors
GREEN  := $(shell tput -Txterm setaf 2)
WHITE  := $(shell tput -Txterm setaf 7)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

# --- General Targets ---

.PHONY: all help license check docker start stop restart clean deep-clean doc check-api check-dashboard local reset start-server start-agent

all: check

help: ##@Help Show this help instructions.
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

HELP_FUN = \
	%help; \
	while(<>) { push @{$$help{$$2 // 'options'}}, [$$1, $$3] if /^([a-zA-Z\-]+)\s*:.*\#\#(?:@([a-zA-Z\-]+))?\s(.*)$$/ }; \
	print "usage: make [target]\n\n"; \
	for (sort keys %help) { \
		print "${WHITE}$$_:${RESET}\n"; \
		for (@{$$help{$$_}}) { \
			$$sep = " " x (32 - length $$_->[0]); \
			print "  ${YELLOW}$$_->[0]${RESET}$$sep${GREEN}$$_->[1]${RESET}\n"; \
	}; \
	print "\n"; }

license: ##@Code Check source files for Apache license header.
	@scripts/check_license.sh

check: license ##@Code Run code format and style checks (license, tox, yarn lint).
	@find ./docs -type f -name "*.md" -exec egrep -l " +$$" {} \;
	@cd src/api-engine && tox
	@cd src/dashboard && yarn lint

doc: ##@Documentation Build local documentation and start serve.
	@command -v mkdocs >/dev/null 2>&1 || pip install -r docs/requirements.txt
	@mkdocs serve -f mkdocs.yml

# --- Build Targets ---

docker: api-engine dashboard agent fabric ##@Build Build all required docker images locally.

api-engine: ##@Build Build api-engine image.
	docker build -t $(DOCKER_NS)/cello-api-engine:$(IMG_TAG) -t $(DOCKER_NS)/cello-api-engine:latest ./src/api-engine --platform linux/$(ARCH)

dashboard: ##@Build Build dashboard image.
	docker build -t $(DOCKER_NS)/cello-dashboard:$(IMG_TAG) -t $(DOCKER_NS)/cello-dashboard:latest ./src/dashboard

agent: ##@Build Build agent image.
	docker build -t $(DOCKER_NS)/cello-agent-fabric:$(IMG_TAG) -t $(DOCKER_NS)/cello-agent-fabric:latest ./src/agents/hyperledger-fabric --platform linux/$(ARCH)

fabric: ##@Build Build fabric image.
	docker build -t $(DOCKER_NS)/fabric:2.5.14 ./src/nodes/hyperledger-fabric

# --- Service Management ---

start: ##@Service Start cello services using docker compose.
	docker compose -f $(COMPOSE_FILE) up -d --build --force-recreate --remove-orphans

stop: ##@Service Stop cello services.
	docker compose -f $(COMPOSE_FILE) down --remove-orphans

restart: stop start ##@Service Restart cello services.

local: start ##@Development Alias for start.

clean: ##@Clean Stop services and remove containers/volumes.
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

reset: clean ##@Development Alias for clean.

deep-clean: clean ##@Clean Stop services, remove images and local storage.
	@docker images --filter=reference='$(DOCKER_NS)/cello-*' --format '{{.ID}}' | xargs -r docker rmi -f 2>/dev/null || true
	@docker image prune -f
	@rm -rf /opt/cello

# --- Advanced Service/Test ---

start-server: ##@Service Start only the server-side services.
	docker compose -f bootup/docker-compose-files/docker-compose.server.dev.yml up -d --force-recreate --remove-orphans

start-agent: ##@Service Start only the agent-side services.
	docker compose -f bootup/docker-compose-files/docker-compose.agent.dev.yml up -d --force-recreate --remove-orphans

check-api: ##@Test Run Newman-based API tests.
	@cd tests/postman && docker compose -f docker-compose.dev.yml up --abort-on-container-exit

check-dashboard: ##@Test Run dashboard-specific tests.
	@docker compose -f tests/dashboard/docker-compose.yml up --abort-on-container-exit

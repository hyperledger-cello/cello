# Copyright IBM Corp, All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
#
# -------------------------------------------------------------
# This makefile defines the following targets, feel free to run "make help" to see help info
#
#   - all (default):  Builds all targets and runs all tests/checks
#   - clean:          Cleans the docker containers.
#   - check:          Setup as master node, and runs all tests/checks, will be triggered by CI
#   - deep-clean:     Clean up all docker images and local storage.
#   - doc:            Start a local web service to explore the documentation
#   - docker[-clean]: Build/clean docker images locally
#   - docker-compose: Start development docker-compose.
#   - help:           Output the help instructions for each command
#   - license:        Checks source files for Apache license header
#   - local:          Run all services ad-hoc
#   - reset:          Clean up and remove local storage (only use for development)
#   - restart:        Stop the cello service and then start
#   - setup-master:   Setup the host as a master node, install pkg and download docker images
#   - setup-worker:   Setup the host as a worker node, install pkg and download docker images
#   - start:          Start the cello service
#   - stop:           Stop the cello service, and remove all service containers

GREEN  := $(shell tput -Txterm setaf 2)
WHITE  := $(shell tput -Txterm setaf 7)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)
ARCH   := $(shell uname -m)

# set the arm64 ARCH to amd64 for compatibility reason
ifeq ($(ARCH), arm64)
    ARCH := amd64
endif

#Set the source of PIP in docker agent image
PIP=pip.conf.bak

# changelog specific version tags
PREV_VERSION?=0.9.0

# Building image usage
DOCKER_NS ?= hyperledger
BASENAME ?= $(DOCKER_NS)/cello
AGENT_BASENAME ?= $(DOCKER_NS)/cello-agent
VERSION ?= 0.9.0
IS_RELEASE=false

DOCKER_BASE_x86_64=python:3.6
DOCKER_BASE_ppc64le=ppc64le/python:3.6
DOCKER_BASE_s390x=s390x/python:3.6
DOCKER_BASE_arm64=python:3.6
DOCKER_BASE_amd64=python:3.6
DOCKER_BASE=$(DOCKER_BASE_$(ARCH))
BASE_VERSION ?= $(ARCH)-$(VERSION)

ifeq ($(IS_RELEASE),false)
	EXTRA_VERSION ?= snapshot-$(shell git rev-parse --short HEAD)
	IMG_TAG=$(BASE_VERSION)-$(EXTRA_VERSION)
else
	IMG_TAG=$(BASE_VERSION)
endif

# The Cello service listen interface, please use the public available IP.
SERVER_PUBLIC_IP ?= 127.0.0.1

LOCAL_STORAGE_PATH=/opt/cello

# Docker images needed to run cello services
COMMON_DOCKER_IMAGES = api-engine nginx dashboard
AGENT_DOCKER_IMAGES = ansible kubernetes
DUMMY = .$(IMG_TAG)

ifeq ($(DOCKER_BASE), )
	$(error "Architecture \"$(ARCH)\" is unsupported")
endif

# Frontend needed
SLASH:=/
REPLACE_SLASH:=\/

# deploy method docker-compose/k8s
export DEPLOY_METHOD?=docker-compose
export CONFIG_DOCKER_COMPOSE_DEPLOY=y

-include .config
-include .makerc/api-engine
-include .makerc/dashboard

.EXPORT_ALL_VARIABLES:

export ROOT_PATH = ${PWD}
ROOT_PATH_REPLACE=$(subst $(SLASH),$(REPLACE_SLASH),$(ROOT_PATH))

# macOS has diff `sed` usage from Linux
SYSTEM=$(shell uname)
ifeq ($(SYSTEM), Darwin)
	SED = sed -ix
else
	SED = sed -i
endif

# Specify what type the worker node is setup as
WORKER_TYPE ?= docker

# Specify the running mode, prod or dev
MODE ?= prod
ifeq ($(CONFIG_PROD_MODE),y)
	COMPOSE_FILE=docker-compose.yml
	export DEPLOY_TEMPLATE_NAME=deploy.tmpl
	export DEBUG?=False
else
	COMPOSE_FILE=docker-compose.dev.yml
	export DEPLOY_TEMPLATE_NAME=deploy-dev.tmpl
	export DEBUG?=True
endif

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

all: check

clean: ##@Clean Stop services and clean docker containers.
	make stop
	@-docker ps -a --filter "name=cello-" --format "{{.ID}}" | xargs docker rm -f >/dev/null 2>&1
	@echo "Cleared out containers"
	
check: ##@Code Check code format
	@$(MAKE) license
	find ./docs -type f -name "*.md" -exec egrep -l " +$$" {} \;
	cd src/api-engine && tox && cd ${ROOT_PATH}
	cd src/dashboard && yarn lint && cd ${ROOT_PATH}

deep-clean: ##@Clean Stop services, clean docker images and remove mounted local storage.
	make clean-images
	rm -rf $(LOCAL_STORAGE_PATH)

docs:
	make doc

doc: ##@Documentation Build local online documentation and start serve
	command -v mkdocs >/dev/null 2>&1 || pip install -r docs/requirements.txt || pip3 -r docs/requirements.txt
	mkdocs serve -f mkdocs.yml

docker: images ##@Build Build all required docker images locally

docker-clean:##@Clean Clean docker images locally
	make clean-images

docker-compose: api-engine fabric docker-rest-agent dashboard ##@Development Start development docker-compose

help: ##@Help Show this help.
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

license:  ##@Code Check source files for Apache license header
	scripts/check_license.sh

local:##@Development Run all services ad-hoc
	make docker-compose start-docker-compose 

reset:##@Development Clean up and remove local storage (only use for development)
	make clean 
	echo "Clean up and remove all local storage..."
	rm -rf ${LOCAL_STORAGE_PATH}/*

restart: stop start ##@Service Restart services

setup-master: ##@Environment Setup dependency for master node
	cd scripts/master_node && bash setup.sh

setup-worker: ##@Environment Setup dependency for worker node
	cd scripts/worker_node && bash setup.sh $(WORKER_TYPE)

start: ##@Service Start service
	make start-docker-compose

stop: ##@Service Stop service
	@if [ "$(CONFIG_DOCKER_COMPOSE_DEPLOY)" = "y" ]; then \
		make stop-docker-compose; \
	else \
		make stop-k8s; \
	fi

## Help rules
clean-images: 
	@echo "Clean all cello related images, may need to remove all containers"
	make clean
	@-docker images --filter=reference='hyperledger/*cello*' --format '{{.ID}}' | xargs -r docker rmi -f 2>/dev/null  
	@echo "Images deleted!"
	@echo "Pruning dangling images..."
	docker image prune
	@echo "Dangling images pruned, cleanup finished!"

check-dashboard:
	docker compose -f tests/dashboard/docker-compose.yml up --abort-on-container-exit || (echo "check dashboard failed $$?"; exit 1)

start-docker-compose:
	docker compose -f bootup/docker-compose-files/${COMPOSE_FILE} up -d --force-recreate --remove-orphans

stop-docker-compose:
	echo "Stop all services with bootup/docker-compose-files/${COMPOSE_FILE}..."
	docker compose -f bootup/docker-compose-files/${COMPOSE_FILE} stop
	echo "Stop all services successfully"

images: api-engine docker-rest-agent fabric dashboard

api-engine: 
	docker build -t hyperledger/cello-api-engine:latest -f build_image/docker/common/api-engine/Dockerfile.in ./ --platform linux/$(ARCH)
	
docker-rest-agent:
	docker build -t hyperledger/cello-agent-docker:latest -f build_image/docker/agent/docker-rest-agent/Dockerfile.in ./ --build-arg pip=$(PIP) --platform linux/$(ARCH)

fabric:
	docker build -t hyperledger/fabric:2.5.10 -f build_image/docker/cello-hlf/Dockerfile build_image/docker/cello-hlf/

dashboard:
	docker build -t hyperledger/cello-dashboard:latest -f build_image/docker/common/dashboard/Dockerfile.in ./

server:
	docker compose -f bootup/docker-compose-files/docker-compose.server.dev.yml up -d --force-recreate --remove-orphans

.PHONY: \
	all \
	license \
	check \
	docs \
	doc \ 
	help \
	docker \
	docker-clean \
	start \
	stop \
	restart \
	clean \
	deep-clean \
	api-engine \
	fabric \
	dashboard \
	docker-compose \
	reset \
	local \
	clean-images \
	start-docker-compose \
	stop-docker-compose \
	images \
	server\

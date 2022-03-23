SHELL:=bash
.ONESHELL:
.PHONY: env


COMMITID=$(shell git rev-parse --short HEAD)

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/

# Qgis version flavor
FLAVOR:=3.16

BECOME_USER:=$(shell id -u)
BECOME_GROUP:=$(shell id -g)

QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

SRCDIR=$(shell realpath ..)

test:
	mkdir -p $$(pwd)/.local $$(pwd)/.cache
	docker run --rm --name qgis-wfsoutputextension-test-$(FLAVOR)-$(COMMITID) -w /src/tests \
		-u $(BECOME_USER):$(BECOME_GROUP) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $$(pwd)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		$(QGIS_IMAGE) ./run-tests.sh $(PYTEST_ADDOPTS)

clean:
	rm -rf $$(pwd)/.local $$(pwd)/.cache

run: env
	docker compose up -V --force-recreate

stop:
	docker compose down -v --remove-orphans

env:
	@echo "Creating environment file for docker-compose"
	@cat <<-EOF > .env
		WORKDIR=$(shell pwd)
		QGIS_VERSION=$(FLAVOR)
		QGIS_USER_ID=$(BECOME_USER)
		QGIS_USER_GID=$(BECOME_GROUP)
		SERVER_HTTP_PORT=127.0.0.1:8888
		SERVER_MANAGEMENT_PORT=127.0.0.1:19876
		EOF


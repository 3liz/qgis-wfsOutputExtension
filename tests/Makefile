SHELL:=bash

COMMITID=$(shell git rev-parse --short HEAD)

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/

# Qgis version flavor
FLAVOR:=3.22

BECOME_USER:=$(shell id -u)

QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

LOCAL_HOME ?= $(shell pwd)

SRCDIR=$(shell realpath ..)

test:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	@echo Do not forget to run docker pull $(QGIS_IMAGE) from time to time
	docker run --rm --name qgis-wfsoutputextension-test-$(FLAVOR)-$(COMMITID) -w /src/tests \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e PYTEST_ADDOPTS="$(TEST_OPTS)" \
		$(QGIS_IMAGE) ./run-tests.sh

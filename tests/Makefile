SHELL:=bash

DEPTH=..

topsrcdir=$(shell realpath $(DEPTH))

COMMITID=$(shell git rev-parse --short HEAD)

install-requirements:
	pip install -U --upgrade-strategy=eager -r requirements.txt

# Use local qgis installation
test: export QGIS_SERVER_LOG_FILE="/src/tests/qgis_server.log"
test: export QGIS_SERVER_LOG_LEVEL=0
test: install-requirements
	pytest -v --qgis-plugins=$(topsrcdir)
clean:
	rm -r ./tmp/test-*


# Use docker image
docker-test: FLAVOR:=ltr
docker-test: REGISTRY_URL ?= 3liz
docker-test: REGISTRY_PREFIX=$(REGISTRY_URL)/
docker-test: QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)
docker-test: BECOME_USER:=$(shell id -u)
docker-test: LOCAL_HOME ?= $(shell pwd)
docker-test: SRCDIR=$(shell realpath ..)
docker-test:
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

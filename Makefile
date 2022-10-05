SHELL = bash
.ONESHELL:
.PHONY: env

#
#  plugin makefile
#

COMMITID=$(shell git rev-parse --short HEAD)

PYTHON:=python3

BUILDDIR:=build
DIST:=${BUILDDIR}/dist

manifest:

dirs:
	mkdir -p $(DIST)

# Build dependencies
wheel-deps: dirs
	pip wheel -w $(DIST) -r requirements.txt

wheel:
	mkdir -p $(DIST)
	$(PYTHON) setup.py bdist_wheel --dist-dir=$(DIST)

deliver:
	twine upload -r storage $(DIST)/*

dist: dirs
	rm -rf *.egg-info
	$(PYTHON) setup.py sdist --dist-dir=$(DIST)

clean:
	rm -rf *.egg-info
	rm -rf $(BUILDDIR)

# Checke setup.cfg for flake8 configuration
lint:
	@flake8

test: lint
	$(MAKE) -C tests



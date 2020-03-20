#
# Makefile for building/packaging qgis for lizmap hosting
#

ifndef FABRIC
FABRIC:=$(shell [ -e .fabricrc ] && echo "fab -c .fabricrc" || echo "fab")
endif

VERSION=$(shell ./metadata_key ../wfsOutputExtension/metadata.txt version)

main:
	echo "Makefile for packaging infra components: select a task"

PACKAGE=qgis3_wfsoutput
FILES = ../wfsOutputExtension/* ../README.md
PACKAGEDIR=wfsOutputExtension

build2/$(PACKAGEDIR):
	@rm -rf build2/$(PACKAGEDIR)
	@mkdir -p build2/$(PACKAGEDIR)
	@cp -rLp $(FILES) build2/$(PACKAGEDIR)/

dist: build2/$(PACKAGEDIR)

.PHONY: package
package: dist
	@echo "Building package $(PACKAGE)"
	$(FABRIC) package:$(PACKAGE),versiontag=$(VERSION),files=$(PACKAGEDIR),directory=./build2


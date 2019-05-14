#
# Makefile for building/packaging qgis for lizmap hosting
#

ifndef FABRIC
FABRIC:=$(shell [ -e .fabricrc ] && echo "fab -c .fabricrc" || echo "fab")
endif

VERSION=$(shell ./metadata_key ../metadata.txt version)

main:
	echo "Makefile for packaging infra components: select a task"

PACKAGE=qgis_wfsoutput
FILES = ../*.py ../metadata.txt ../README.md
PACKAGEDIR=wfsOutputExtension

build/$(PACKAGEDIR):
	@rm -rf build/$(PACKAGEDIR)
	@mkdir -p build/$(PACKAGEDIR)


.PHONY: package
package: build/$(PACKAGEDIR)
	@echo "Building package $(PACKAGE)"
	@cp -rLp $(FILES) build/$(PACKAGEDIR)/
	$(FABRIC) package:$(PACKAGE),versiontag=$(VERSION),files=$(PACKAGEDIR),directory=./build


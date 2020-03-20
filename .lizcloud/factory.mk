#
# Makefile for building/packaging qgis for lizmap hosting
#

VERSION=$(shell ./metadata_key ../wfsOutputExtension/metadata.txt version)

main:
	echo "Makefile for packaging infra components: select a task"

PACKAGE=qgis_wfsoutput
FILES = ../wfsOutputExtension/* ../README.md
PACKAGEDIR=wfsOutputExtension

build/$(PACKAGEDIR):
	@rm -rf build/$(PACKAGEDIR)
	@mkdir -p build/$(PACKAGEDIR)
	@cp -rLp $(FILES) build/$(PACKAGEDIR)/

dist: build/$(PACKAGEDIR)

.PHONY: package
package: dist
	@echo "Building package $(PACKAGE)"
	$(FACTORY_SCRIPTS)/make-package $(PACKAGE) $(VERSION) $(PACKAGEDIR) ./build


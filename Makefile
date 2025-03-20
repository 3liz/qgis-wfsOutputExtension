.PHONY: tests

PYTHON_PKG=wfsOutputExtension

test:
	$(MAKE) -C tests test

lint:
	@ruff check --output-format=concise $(PYTHON_PKG)

lint-preview:
	@ruff check --preview $(PYTHON_PKG)

lint-fix:
	@ruff check --preview --fix $(PYTHON_PKG)

install-dev:
	$(MAKE) -C tests install-requirements
	pip install -U --upgrade-strategy=eager ruff mypy

typing:
	mypy --config-file=mypy.ini -p $(PYTHON_PKG)

# Cyber Kitchen — run `make` or `make help` to see the commands.

VENV    := .venv
PYTHON  := $(VENV)/bin/python
PORT    ?= 8000

.DEFAULT_GOAL := help
.PHONY: help setup serve test test-py test-js coverage clean

help:  ## Show this list of commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

$(VENV)/.installed: requirements-dev.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --quiet --upgrade pip
	$(PYTHON) -m pip install --quiet -r requirements-dev.txt
	$(PYTHON) -m playwright install chromium
	@touch $@

setup: $(VENV)/.installed  ## Install the test tools (pytest, coverage, Playwright Chromium) into .venv

serve:  ## Start the live-reload web server (PORT=8000); needs only Python
	python3 server.py $(PORT)

test: setup  ## Run every test, both coverage checks (100% each), refresh tests/screenshots, print a summary
	@$(PYTHON) -m coverage run -m pytest tests -q; tests=$$?; \
	$(PYTHON) -m coverage json -o coverage/python.json --quiet; cover=$$?; \
	$(PYTHON) -m coverage html --directory coverage/python --quiet; \
	$(PYTHON) tests/summary.py; \
	[ $$tests -eq 0 ] && [ $$cover -eq 0 ]

test-py: setup  ## Run only the Python server tests, with coverage
	$(PYTHON) -m coverage run -m pytest tests/test_server.py
	$(PYTHON) -m coverage report

test-js: setup  ## Run only the browser tests, with JavaScript coverage
	$(PYTHON) -m pytest tests/test_page.py

coverage: test  ## Run all tests, then open both coverage reports
	open coverage/python/index.html coverage/js-coverage.html

clean:  ## Remove coverage output and caches (keeps .venv)
	rm -rf coverage .coverage .pytest_cache tests/__pycache__ __pycache__

# Cyber Kitchen — run `make` or `make help` to see the commands.

VENV    := .venv
PYTHON  := $(VENV)/bin/python
PORT    ?= 8000

.DEFAULT_GOAL := help
.PHONY: help setup build serve test test-py test-js screenshots coverage clean

help:  ## Show this list of commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

$(VENV)/.installed: requirements-dev.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --quiet --upgrade pip
	$(PYTHON) -m pip install --quiet -r requirements-dev.txt
	$(PYTHON) -m playwright install chromium
	@touch $@

setup: $(VENV)/.installed  ## Install the test tools (pytest, coverage, Playwright Chromium) into .venv

build:  ## Build site/index.html by inlining the modules in js/ into index.template.html, and check they went in unchanged
	python3 build.py --check

serve: build  ## Build, then start the live-reload web server (PORT=8000); needs only Python
	python3 server.py $(PORT)

test: build setup  ## Run every test, both coverage checks (100% each), check the page against tests/screenshots, print a summary
	@$(PYTHON) -m coverage run -m pytest tests -q; tests=$$?; \
	$(PYTHON) -m coverage json -o coverage/python.json --quiet; cover=$$?; \
	$(PYTHON) -m coverage html --directory coverage/python --quiet; \
	$(PYTHON) tests/summary.py; \
	[ $$tests -eq 0 ] && [ $$cover -eq 0 ]

test-py: setup  ## Run only the Python server tests, with coverage
	$(PYTHON) -m coverage run -m pytest tests/test_server.py
	$(PYTHON) -m coverage report

test-js: build setup  ## Run only the browser tests, with JavaScript coverage
	$(PYTHON) -m pytest tests/js tests/test_page.py tests/test_requirements.py tests/test_screenshots.py

screenshots: build setup  ## Accept how the page looks now: replace the checked-in screenshots that no longer match
	UPDATE_SCREENSHOTS=1 JS_COVERAGE_MIN=0 $(PYTHON) -m pytest tests/test_screenshots.py -q

coverage: test  ## Run all tests, then open both coverage reports
	open coverage/python/index.html coverage/js-coverage.html

clean:  ## Remove coverage output and caches (keeps .venv)
	rm -rf coverage .coverage .pytest_cache tests/__pycache__ __pycache__

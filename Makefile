# Variables
PYENV_ROOT := $(HOME)/.pyenv
PYTHON_VERSION := 3.12.11
PYTHON := $(PYENV_ROOT)/versions/$(PYTHON_VERSION)/bin/python
VENV := .venv
UV := uv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
ENV_FILE := .env
SHELL := /bin/bash
PYTHONPATH := $(CURDIR)/src

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make setup        - Set up the development environment"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run the main server"
	@echo "  make scrape       - Run the scraper"
	@echo "  make clean        - Clean up generated files"
	@echo "  make lint         - Run linting checks"
	@echo "  make check-env    - Check required environment variables"
	@echo "  make dev-install  - Install package in development mode"

# Create template .env file
.PHONY: init-env
init-env:
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Creating template .env file..."; \
		echo "LINKEDIN_EMAIL=your.email@example.com" > $(ENV_FILE); \
		echo "LINKEDIN_PASSWORD=your_password" >> $(ENV_FILE); \
		echo "CHROMEDRIVER=/path/to/chromedriver" >> $(ENV_FILE); \
		echo "Template .env file created. Please edit it with your credentials."; \
	else \
		echo ".env file already exists. Skipping creation."; \
	fi

# Check if .env file exists and export its variables
.PHONY: check-env
check-env:
	@echo "Checking environment setup..."
	@if [ -f $(ENV_FILE) ]; then \
		echo "Found .env file, checking required variables..."; \
		set -a; \
		. $(ENV_FILE); \
		set +a; \
		if [ -z "$$LINKEDIN_EMAIL" ] || [ -z "$$LINKEDIN_PASSWORD" ]; then \
			echo "Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env file"; \
			exit 1; \
		fi; \
		echo "Environment variables loaded successfully"; \
	else \
		echo "Error: .env file not found"; \
		exit 1; \
	fi

# Install package in development mode
.PHONY: dev-install
dev-install:
	@echo "Installing package in development mode..."
	PYTHONPATH=$(PYTHONPATH) $(UV) pip install -e .

# Setup virtual environment and install dependencies
.PHONY: setup
setup: check-env
	@echo "Setting up development environment..."
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "Error: Python $(PYTHON_VERSION) not found in pyenv. Please install it first:"; \
		echo "pyenv install $(PYTHON_VERSION)"; \
		exit 1; \
	fi
	$(PYTHON) -m venv $(VENV)
	PYTHONPATH=$(PYTHONPATH) $(UV) pip install -e .
	PYTHONPATH=$(PYTHONPATH) $(UV) pip install -e ".[dev]"
	$(UV) run pre-commit install
	@echo "Setup completed successfully"

# Run tests
.PHONY: test
test: check-env
	@echo "Running tests..."
	PYTHONPATH=$(PYTHONPATH) . $(ENV_FILE) && $(UV) run pytest

# Run the main server
.PHONY: run
run: check-env
	@echo "Running LinkedIn MCP server..."
	PYTHONPATH=$(PYTHONPATH) . $(ENV_FILE) && $(UV) run main.py

# Run the scraper
.PHONY: scrape
scrape: check-env
	@echo "Running LinkedIn scraper..."
	PYTHONPATH=$(PYTHONPATH) . $(ENV_FILE) && $(UV) run scraper.py

# Clean up generated files
.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run linting checks
.PHONY: lint
lint:
	@echo "Running linting checks..."
	PYTHONPATH=$(PYTHONPATH) $(UV) run ruff check .
	PYTHONPATH=$(PYTHONPATH) $(UV) run mypy src/
	PYTHONPATH=$(PYTHONPATH) $(UV) run pre-commit run --all-files

# Create sample profiles.csv if it doesn't exist
.PHONY: init-data
init-data:
	@echo "Creating sample profiles.csv..."
	@mkdir -p data
	@if [ ! -f data/profiles.csv ]; then \
		echo "name,url" > data/profiles.csv; \
		echo "Sample Profile,https://www.linkedin.com/in/sample-profile" >> data/profiles.csv; \
	fi

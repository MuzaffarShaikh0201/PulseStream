# PulseStream - Makefile
# Run `make` or `make help` for available commands

.PHONY: help install install-dev lock clean run api api-local test test-cov build

# Default target
.DEFAULT_GOAL := help

help:
	@echo "PulseStream - Available Commands"
	@echo "================================"
	@echo ""
	@echo "  Setup:"
	@echo "    install      - Install dependencies"
	@echo "    install-dev  - Install with dev dependencies (default)"
	@echo "    lock         - Update poetry.lock"
	@echo ""
	@echo "  Run:"
	@echo "    run          - Run API server (local dev, with reload)"
	@echo "    api          - Run API server (production)"
	@echo "    api-local    - Run API server (local dev, with reload)"
	@echo ""
	@echo "  Test:"
	@echo "    test         - Run tests"
	@echo "    test-cov     - Run tests with coverage report"
	@echo ""
	@echo "  Build & Clean:"
	@echo "    build        - Build distribution packages"
	@echo "    clean        - Remove cache, build artifacts, coverage"

# --- Setup ---
install:
	poetry install --no-dev

install-dev:
	poetry install

lock:
	poetry lock

# --- Run ---
run: api-local

api:
	poetry run api

api-local:
	poetry run api --local

# --- Test ---
test:
	poetry run pytest --no-cov -v --tb=short

test-cov:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html -v --tb=short

# --- Build & Clean ---
build:
	poetry build

clean:
	@echo "Cleaning project..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@rm -rf .coverage .coverage.* 2>/dev/null || true
	@rm -rf dist build 2>/dev/null || true
	@rm -rf .mypy_cache .ruff_cache 2>/dev/null || true
	@echo "Done."

.PHONY: help install run api

help:
	@echo "PulseStream - Available Commands"
	@echo "================================="
	@echo "  install        - Install dependencies"
	@echo "  clean          - Clean the project"
	@echo "  api            - Run API server (production)"
	@echo "  api-local      - Run API server (local development)"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"

install:
	poetry install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build

api:
	poetry run api

api-local:
	poetry run api --local

test:
	poetry run pytest --no-cov

test-cov:
	poetry run pytest --cov-report=term-missing --cov-report=html
.PHONY: help install install-dev test lint format type-check clean run setup

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install the package and dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  clean        - Clean up cache and temporary files"
	@echo "  run          - Run the MCP server"
	@echo "  setup        - Set up development environment"

# Install the package
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Set up development environment
setup: install-dev
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	@echo "Development environment ready!"
	@echo "Don't forget to:"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Install Chrome/Chromium for JavaScript scraping"

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src tests

# Format code
format:
	black src tests

# Check formatting
format-check:
	black --check src tests

# Run type checking
type-check:
	mypy src

# Run all checks
check: lint type-check format-check test

# Clean up cache and temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .web_scout_cache/
	rm -rf .test_cache/

# Run the MCP server
run:
	python -m src.server

# Run in development mode with debug logging
run-dev:
	WEB_SCOUT_LOG_LEVEL=DEBUG WEB_SCOUT_ENV=development python -m src.server

# Build distribution packages
build:
	python -m build

# Install pre-commit hooks
pre-commit:
	pre-commit install

# Run pre-commit on all files
pre-commit-all:
	pre-commit run --all-files

# Install package from PyPI (for users)
install-release:
	pip install web-scout-mcp-server

# Development workflow - run this before committing
dev-check: format lint type-check test
	@echo "All checks passed! Ready to commit."
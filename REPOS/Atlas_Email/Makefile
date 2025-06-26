# Atlas Email Makefile

.PHONY: help install dev-install test lint format clean build docs serve-docs

# Default target
help:
	@echo "Atlas Email - Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  test         Run test suite"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build package"
	@echo "  docs         Build documentation"
	@echo "  serve-docs   Serve documentation locally"
	@echo "  run-cli      Run CLI interface"
	@echo "  run-web      Run web interface"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	PYTHONPATH=src python3 -m pytest tests/ -v --cov=src/atlas_email --cov-report=html

test-unit:
	PYTHONPATH=src python3 -m pytest tests/unit/ -v

test-integration:
	PYTHONPATH=src python3 -m pytest tests/integration/ -v

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Documentation
docs:
	cd docs && mkdocs build

serve-docs:
	cd docs && mkdocs serve

# Build
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

# Run applications
run-cli:
	PYTHONPATH=src python3 -m atlas_email.cli.main

run-web:
	PYTHONPATH=src python3 -m atlas_email.api.app

# Database operations
db-init:
	python -c "from atlas_email.models.database import Database; Database().initialize()"

db-migrate:
	python scripts/migrate_database.py

# Development helpers
update-deps:
	pip freeze > requirements.txt

check-security:
	bandit -r src/

profile:
	python -m cProfile -o profile.stats -m atlas_email.cli.main
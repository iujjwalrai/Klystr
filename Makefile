.PHONY: help install services migrate run test lint fmt shell clean

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dev dependencies into the local venv
	./venv/bin/pip install -r requirements-dev.txt

services: ## Start Postgres and Redis
	docker compose -f infrastructure/docker/docker-compose.yml up -d

migrate: ## Apply database migrations
	./venv/bin/python manage.py migrate

run: ## Run the control plane API server
	./venv/bin/python manage.py runserver

test: ## Run the test suite
	./venv/bin/pytest

lint: ## Lint the codebase
	./venv/bin/ruff check .

fmt: ## Format the codebase
	./venv/bin/ruff format .

shell: ## Open a Django shell
	./venv/bin/python manage.py shell

clean: ## Remove caches
	find . -path ./venv -prune -o -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

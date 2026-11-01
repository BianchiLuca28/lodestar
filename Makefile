.DEFAULT_GOAL := help

BACKEND := backend
FRONTEND := frontend

.PHONY: help test lint gen-api

help: ## List every target
	@uv run --no-project python -c "import re; [print(f'  {m[1]:<10} {m[2]}') for m in re.finditer(r'^([a-z-]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

test: ## Run backend (pytest) and frontend (Vitest) tests
	cd $(BACKEND) && uv run pytest
	cd $(FRONTEND) && pnpm test

lint: ## Ruff, mypy (strict on domain/), ESLint and tsc
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . && uv run mypy
	cd $(FRONTEND) && pnpm lint && pnpm typecheck

gen-api: ## Regenerate frontend API types from the backend OpenAPI schema
	cd $(FRONTEND) && pnpm gen:api

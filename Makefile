.DEFAULT_GOAL := help

BACKEND := backend
FRONTEND := frontend

.PHONY: help test test-backend test-frontend lint lint-backend lint-frontend gen-api

help: ## List every target
	@uv run --no-project python -c "import re; [print(f'  {m[1]:<14} {m[2]}') for m in re.finditer(r'^([a-z-]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests (pytest)
	cd $(BACKEND) && uv run pytest

test-frontend: ## Run frontend tests (Vitest)
	cd $(FRONTEND) && pnpm test

lint: lint-backend lint-frontend ## Run every linter and type check

lint-backend: ## Ruff lint and format check, mypy (strict on domain/)
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . && uv run mypy

lint-frontend: ## ESLint and tsc
	cd $(FRONTEND) && pnpm lint && pnpm typecheck

gen-api: ## Regenerate frontend API types from the backend OpenAPI schema
	cd $(FRONTEND) && pnpm gen:api

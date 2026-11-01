.DEFAULT_GOAL := help

BACKEND := backend
FRONTEND := frontend
CONFIG ?= config
DATA ?= data

.PHONY: help dev test test-backend test-frontend lint lint-backend lint-frontend gen-api fake-ledger eval migrate import demo

help: ## List every target
	@uv run --no-project python -c "import re; [print(f'  {m[1]:<14} {m[2]}') for m in re.finditer(r'^([a-z-]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

dev: ## Build and start the stack in Docker (UI on http://127.0.0.1:8080)
	docker compose up --build

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

fake-ledger: ## Regenerate config.example/ledger.csv (seeded, deterministic)
	cd $(BACKEND) && uv run python scripts/gen_fake_ledger.py

eval: ## Run the parsing eval set (ARGS=--compare for before/after)
	cd $(BACKEND) && uv run python -m lodestar.ai.evals.runner $(ARGS)

migrate: ## Apply database migrations to data/lodestar.db (also runs at startup)
	cd $(BACKEND) && LODESTAR_DATA_DIR=../data uv run python -c "from pathlib import Path; from lodestar.adapters.db.engine import migrate; migrate(Path('../data/lodestar.db'))"

import: ## One-time import: make import FILE=path.csv [ARGS=--dry-run] [CONFIG=config DATA=data]
	cd $(BACKEND) && uv run python -m lodestar.jobs.initial_import "$(abspath $(FILE))" --config "$(abspath $(CONFIG))" --data "$(abspath $(DATA))" $(ARGS)

demo: ## Rebuild data-demo/ from the fake persona (config.example + ledger.csv)
	rm -rf data-demo
	$(MAKE) import FILE=config.example/ledger.csv CONFIG=config.example DATA=data-demo

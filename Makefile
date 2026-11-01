.DEFAULT_GOAL := help

BACKEND := backend

.PHONY: help test lint

help: ## List every target
	@uv run --no-project python -c "import re; [print(f'  {m[1]:<10} {m[2]}') for m in re.finditer(r'^([a-z-]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

test: ## Run backend tests
	cd $(BACKEND) && uv run pytest

lint: ## Ruff lint and format check, mypy (strict on domain/)
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . && uv run mypy

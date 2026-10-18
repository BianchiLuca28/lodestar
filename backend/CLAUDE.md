# Backend

Python 3.12, managed with `uv`. FastAPI, Pydantic v2, SQLModel on SQLAlchemy 2, Alembic, SQLite (WAL) with `sqlite-vec`, LangGraph + `langchain-ollama`, APScheduler. Tests with pytest; lint with Ruff; types with mypy (strict on `domain/`).

## Layers

```
src/lodestar/
  domain/     pure logic: ledger, direction, balances, buckets, rules, ranking. No I/O, no framework imports.
  ai/         LangGraph graphs, prompts, output schemas, few-shot retrieval
  adapters/   SQLite repositories, Telegram sender, relay client, price providers, backup targets, xlsx readers
  api/        FastAPI routers and request/response models
  jobs/       scheduled jobs: relay poll, prices, backups, digest
  config/     loading and validating the YAML files in config/
```

Dependencies point inward: `api`, `jobs`, `ai` and `adapters` may import `domain`; `domain` imports nothing from them. Pass repositories and clients in as parameters (protocols in `domain/ports.py`) so domain code is tested without a database or network.

## Conventions

- **Money:** `Decimal`, quantized to `0.01`, `ROUND_HALF_EVEN`. Stored as integer cents in SQLite. Parse Italian input (`1.234,56`) only at the edges.
- **Dates:** `datetime.date` for business dates; timezone `Europe/Rome` for "today" and relative dates ("ieri", "sabato"), resolved against the message's send time.
- **Direction** is derived, never stored: see `domain/direction.py` and `CONTEXT.md`.
- **Config** files are validated by Pydantic models on startup; an invalid file stops the app with a message naming the file and field.
- **Migrations:** every schema change ships an Alembic migration; never edit a released migration.
- **Errors:** domain raises typed exceptions; `api` maps them to HTTP errors with an Italian-safe message key for the UI.

## AI code

- One graph per file in `ai/graphs/` (`parse_message.py`, `plan_agent.py`, `chat.py`). State is a typed `TypedDict` or Pydantic model.
- Prompts live in `ai/prompts/<name>.md`, in English, with a version line at the top. Changing a prompt bumps its version so eval results stay comparable.
- Output schemas are Pydantic models in `ai/schemas.py`. Validate in code after every LLM call; on failure retry once with the validation errors, then return a draft flagged for review.
- The model for each task comes from `settings.yaml` (`models.parse`, `models.chat`, `models.vision`, `models.embed`). Never hard-code a model name.
- Tools given to agents are read-only and parameterised (`query_ledger(filters)`, never raw SQL).
- Unit tests use a fake chat model with scripted outputs. Real-model checks belong in `evals/`, run with `make eval`.

## Testing

- `tests/unit/` for `domain/` and pure helpers; fast, no I/O.
- `tests/integration/` for API and repositories against a fresh temporary SQLite file seeded from `config.example/`.
- No test touches the network; HTTP clients are faked with `respx` or protocol fakes.

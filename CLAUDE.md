# Lodestar

Local-first, AI-assisted personal finance tracker for one user per install. Expenses arrive in plain Italian via Telegram (through an AWS relay), local LLMs (Ollama, orchestrated with LangGraph) turn them into **drafts**, the user approves them, and a rules engine checks the ledger against the user's written financial plan. Open source, AGPL-3.0.

## Where knowledge lives

- `docs/design.md` is the spec. Before starting any issue, read the sections it touches (§5 data model, §6 AI design, §7 relay, §8 UX, §11 roadmap). If the design and the issue disagree, the design wins until a new ADR says otherwise.
- `CONTEXT.md` is the domain glossary. Use its terms in code, tests, commits and UI keys; add a term there when you introduce a new domain concept.
- `docs/adr/` records why things are the way they are. Read the matching ADR before changing anything it covers.
- Layer rules: `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `infra/CLAUDE.md`, loaded when you work there.

## Repo map

```
backend/        Python 3.12 · FastAPI · SQLite · LangGraph
frontend/       React · TypeScript · Vite
infra/          AWS SAM: Telegram relay + backup bucket
evals/          LLM eval datasets, runner, results history
config.example/ Fake persona: settings, accounts, categories, buckets, rules, instrument policy, plan
docs/           design.md, adr/
knowledge/      User's course material for RAG (git-ignored except README)
```

`config/`, `data/`, `knowledge/*` and `.env` hold the user's real data and secrets and are git-ignored.

## Commands

`make help` lists every target; it is the source of truth. Current targets: `make help`, `make dev`, `make test` (`test-backend`, `test-frontend`), `make lint` (`lint-backend`, `lint-frontend`), `make gen-api`, `make fake-ledger`, `make eval`, `make migrate`. Coming next: `make deploy-relay` (v0.2). Keep the Makefile and this line in sync.

## Invariants

These hold in every change. A PR that breaks one is wrong even if tests pass.

1. **Drafts first.** Every AI output, bank import or receipt becomes a draft; only an explicit user approval writes to `transactions`.
2. **Code computes, LLM explains.** Balances, totals, rule status and rankings come from deterministic code in `backend/domain/`. LLMs extract fields, pick categories from the configured list and write explanations of numbers they were given.
3. **Passive by design.** Suggestions act only on the plan's calendar, thresholds and the user's instrument policy. Price movements, trends and news never trigger a suggestion.
4. **Local AI.** All model calls go to the configured OpenAI-compatible endpoint (Ollama by default). Network calls are limited to Telegram, the relay, price providers and backup targets.
5. **Fake data in git.** Tests, fixtures and eval datasets in git use `config.example/` and synthetic rows. Real data stays under `config/`, `data/`, `evals/data/private/`.
6. **Money is exact.** Amounts are `Decimal` with 2 places, always positive, in EUR; direction comes from `from_account` / `to_account` (see `CONTEXT.md` → Direction).
7. **Six pages.** Inbox, Movimenti, Panoramica, Portafoglio, Piano, Chat. New features live inside one of them.
8. **English in code, Italian in UI.** Code, comments, prompts, commits and docs in English; user-facing strings through i18n with `it` as default.

## How to work

1. **One issue = one vertical slice = one PR.** Branch `feat/<issue-number>-<slug>` (or `fix/`, `chore/`).
2. **Plan, then build.** Start in plan mode; restate the acceptance criteria and list the files you will touch.
3. **Tests first.** Write the failing test, make it green, refactor. Domain logic gets unit tests; API gets integration tests against a temporary SQLite DB; LLM code gets tests with a fake chat model.
4. **AI behaviour changed?** (prompt, model, graph, retrieval) Run `make eval` and paste the before/after table into the PR.
5. **Decision changed?** Add a new ADR (`/new-adr`) and update `docs/design.md` in the same PR.
6. **Finish:** `make lint test` green, PR template filled, Conventional Commit messages (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`).

When the design is silent on something that changes behaviour for the user, stop and ask; list the question under "Open questions" in the PR instead of guessing.

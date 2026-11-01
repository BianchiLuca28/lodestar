# Lodestar

[![CI](https://github.com/BianchiLuca28/lodestar/actions/workflows/ci.yml/badge.svg)](https://github.com/BianchiLuca28/lodestar/actions/workflows/ci.yml)

**A local-first, AI-assisted personal finance tracker that keeps you on your own plan.**

A lodestar is the star you navigate by. Here the star is your written financial plan, and Lodestar tells you whether you are still on course: not by chasing markets, but by checking every euro you spend and save against the rules you set for yourself.

> Status: **pre-alpha, under construction.** See the [roadmap](#roadmap).

## What it does

- **Log expenses in plain language.** Message a Telegram bot ("cena da Zi Nenè 50€, Marco me ne ha ridati 25") and get ready-made ledger lines back.
- **You approve everything.** AI output is always a draft; one tap to accept, reject or correct.
- **Runs on your machine.** Data, LLMs and embeddings stay local (Ollama). The cloud only relays raw messages and stores encrypted backups.
- **Checks your plan.** Rules like "discretionary spending ≤ €700/month" or "liquidity between €1,500 and €3,500" are evaluated by code every day; a local agent explains the results and tells you when a planned purchase is due.
- **Tracks your buckets and portfolio.** Savings split into buckets (liquidity, emergency fund, house, long term) with targets, contributions and positions.
- **Answers questions with sources.** Chat over your ledger, your plan and your own reference material, with citations.
- **Never times the market.** Suggestions act only on your plan's calendar and thresholds, within an instrument policy you write yourself.

## How it works

```
Phone (Telegram) ──▶ AWS relay (API Gateway + Lambda + DynamoDB/S3)
                                │  polled by
                                ▼
Your PC (Docker Compose, localhost only)
  FastAPI · SQLite · LangGraph agents · rules engine · React UI
                                │
                                ▼
                        Ollama on your GPU
```

Full design: [`docs/design.md`](docs/design.md). Decisions: [`docs/adr/`](docs/adr/). Domain language: [`CONTEXT.md`](CONTEXT.md).

## Stack

Python 3.12 · FastAPI · SQLite + sqlite-vec · LangGraph · Ollama · React + TypeScript + Vite · Tailwind + shadcn/ui · AWS SAM (Lambda, API Gateway, DynamoDB, S3) · Docker Compose

## Roadmap

| Phase | Scope | Gate |
| --- | --- | --- |
| v0.0 | Repo, agent context, CI, config skeleton, eval harness | CI green on an empty app |
| v0.1 | Ledger, spreadsheet import, balance checks, export, backups | Spreadsheet retired |
| v0.2 | AWS relay, Telegram bot, LangGraph parser, Inbox, evals | Telegram replaces manual entry |
| v0.3 | Dashboards, portfolio, prices | Monthly review done in-app |
| v0.4 | Bank XLSX reconciliation, receipt photos | Bank statement reconciled |
| v0.5 | Rules engine, plan agent, digest and alerts | First monthly digest |
| v0.6 | Knowledge base (RAG) and chat | Answers cite their sources |

## Getting started

Setup instructions arrive with v0.1. The shape will be:

```bash
cp -r config.example config   # then edit the YAML files
docker compose up -d          # needs Ollama running on the host
open http://localhost:8080
```

## Run locally

Lodestar runs in Docker; Ollama runs natively on the host so it can use the GPU.

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) with the WSL2 backend, and [Ollama](https://ollama.com/) for Windows. Start both.
2. `make dev`, then open <http://127.0.0.1:8080>. The badge in the top right shows whether the backend and the LLM are reachable.

The backend needs a `config/` folder: start from the fake persona with `cp -r config.example config`, then edit the YAML files. An invalid file stops the backend with a message naming the file and the field (`docker compose logs backend`).

The UI is bound to `127.0.0.1` only. The LLM endpoint comes from `config/settings.yaml`; in Docker, `LODESTAR_LLM_BASE_URL` overrides it with `http://host.docker.internal:11434` to reach Ollama on the host.

**"LLM non raggiungibile" in Docker while Ollama is running?** Ollama listens only on `127.0.0.1` by default. Make it listen on all interfaces: set the user environment variable `OLLAMA_HOST=0.0.0.0`, quit Ollama from the tray and start it again.

## Development

Needs [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), Node 24 and GNU make.

```bash
cd backend && uv sync && cd ..
cd frontend && pnpm install && cd ..
make help          # every target
make lint test     # what CI runs
```

Pre-commit runs Ruff on `backend/` and ESLint on `frontend/` before each commit:

```bash
uv tool install pre-commit
pre-commit install
```

## Contributing

The project is built issue by issue with an AI coding agent; `CLAUDE.md` describes the workflow and the invariants every change must respect. Issues and PRs are welcome.

## Disclaimer

Lodestar is a personal tool for tracking and education. It is not financial advice, and nothing it says is a recommendation to buy or sell any security.

## License

[GNU Affero General Public License v3.0](LICENSE)

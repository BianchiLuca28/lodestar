# Infra

AWS resources for the Telegram relay and encrypted backups, defined with AWS SAM (`template.yaml`, `samconfig.toml`); SAM vs Terraform is confirmed by an ADR at the start of v0.2. Deployed with `make deploy-relay`. Target cost: within the AWS free tier for one user.

## Relay contract

| Route | Caller | Behaviour |
| --- | --- | --- |
| `POST /telegram` | Telegram webhook | Verify `X-Telegram-Bot-Api-Secret-Token` and sender user ID; store the update in DynamoDB `inbound` (key `update_id`, TTL 30 days); download photos and documents to S3 `inbound/`; reply "📥 Ricevuto…"; always answer 200 |
| `GET /inbound` | Local app | Return pending updates oldest first, max 100 |
| `POST /inbound/ack` | Local app | Delete the listed `update_id`s and their S3 objects |

The local app authenticates with an API key held in `.env`. Handlers are idempotent on `update_id`.

## Rules

- The relay stores raw input only. Parsing and every AI call happen on the user's PC.
- Backups arrive already encrypted with `age`; the bucket applies lifecycle rules (30 daily, 12 monthly) and blocks public access.
- Use on-demand and serverless resources only: Lambda, API Gateway HTTP API, DynamoDB on-demand, S3.
- Secrets (bot token, webhook secret, API key) live in SSM Parameter Store standard parameters, never in the template.

# Telegram input goes through an AWS relay

Telegram keeps undelivered bot updates for at most 24 hours, and the user's PC is often off longer. A serverless relay (API Gateway + Lambda + DynamoDB + S3) receives the webhook, stores raw updates, and the PC polls and acknowledges them when it runs. The relay never parses or reasons; AI stays local. Cost stays inside the free tier, and the relay doubles as the project's AWS learning surface.

## Considered Options

- Bot on the PC with long polling: loses messages after 24 h offline.
- Always-on PC or Raspberry Pi: hardware and power cost, still a single point of failure.

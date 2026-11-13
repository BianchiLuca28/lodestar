# v0.2 reads Telegram from the PC; the AWS relay comes later

Partly supersedes ADR 0003 (timing only) and drops the S3 target of ADR 0011 / ADR 0018.

ADR 0003 put an AWS relay in front of the bot because Telegram keeps undelivered updates for 24 hours at most, and the PC may be off for days. That reason still holds and the relay stays the target. But the user wants every feature proven locally before anything runs in the cloud, and no cloud resource may be created or deployed without their explicit OK, even inside the free tier.

So in v0.2 the backend long-polls Telegram `getUpdates` directly while it runs, stores updates in `inbound_messages` and sends replies itself. The known limit: messages sent while Lodestar is off for more than 24 hours are lost; the app warns when the gap since the last poll exceeds 24 hours. The AWS relay (built with AWS SAM, chosen over Terraform: fewer moving parts and no state file for a few Lambdas) moves to a later phase and is deployed only with the user's OK. The local poller is written behind an interface so the relay can replace it without touching the parser.

Encrypted S3 backups are dropped for now: plain local copies (ADR 0018) are enough for the user. Off-site backups stay an open point.

**Considered:** building the relay in v0.2 (rejected: cloud before the feature works locally, and the user wants to approve any spend); Terraform (rejected: state management for a tiny stack).

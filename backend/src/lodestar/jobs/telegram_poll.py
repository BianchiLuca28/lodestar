"""Read the Telegram bot from the PC while Lodestar runs (design §7, ADR 0019).

Telegram keeps undelivered updates for 24 hours, so after a longer gap some messages may be
gone; the user is told once, on the first poll after the gap.
"""

import logging
from datetime import datetime, timedelta

from lodestar.adapters.db.inbound_repo import InboundRepository
from lodestar.adapters.telegram import TelegramClient, parse_update

log = logging.getLogger(__name__)

RECEIVED = "📥 Ricevuto, lo elaboro a breve"
GAP_WARNING = (
    "⚠️ Lodestar è rimasto spento più di 24 ore: alcuni messaggi potrebbero essere andati persi."
)
TELEGRAM_RETENTION = timedelta(hours=24)
LONG_POLL_SECONDS = 25


def gap_exceeded(last_poll: datetime | None, now: datetime) -> bool:
    return last_poll is not None and now - last_poll > TELEGRAM_RETENTION


def poll_once(
    client: TelegramClient,
    repo: InboundRepository,
    user_id: int,
    now: datetime,
    timeout: int = 0,
) -> int:
    """Fetch new updates, keep the user's, reply to each; returns how many were stored."""
    warn = gap_exceeded(repo.last_poll_at(), now)
    stored = 0
    for raw in client.get_updates(repo.next_offset(), timeout):
        update = parse_update(raw)
        repo.mark_seen(int(raw["update_id"]))
        if update is None or update.user_id != user_id:
            continue
        if repo.add(update, raw, now):
            stored += 1
            if update.kind != "callback":
                client.send_message(update.chat_id, RECEIVED)
    if warn:
        client.send_message(user_id, GAP_WARNING)
    repo.set_last_poll_at(now)
    return stored


def safe_poll(client: TelegramClient, repo: InboundRepository, user_id: int, now: datetime) -> None:
    """The scheduled job: network errors are logged and retried on the next tick."""
    try:
        poll_once(client, repo, user_id, now, timeout=LONG_POLL_SECONDS)
    except Exception:
        log.exception("Telegram poll failed; retrying on the next tick")

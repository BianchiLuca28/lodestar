"""Inbound Telegram messages and the last-poll time in SQLite."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from lodestar.adapters.db.tables import AppState, InboundMessage
from lodestar.adapters.telegram import ParsedUpdate

LAST_POLL = "telegram.last_poll_at"
LAST_UPDATE = "telegram.last_update_id"


def _utc(value: datetime) -> datetime:
    # SQLite drops the timezone; every stored datetime is UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class InboundRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _get(self, key: str) -> str | None:
        with Session(self._engine) as session:
            row = session.get(AppState, key)
            return row.value if row else None

    def _set(self, key: str, value: str) -> None:
        with Session(self._engine) as session:
            row = session.get(AppState, key) or AppState(key=key, value=value)
            row.value = value
            session.add(row)
            session.commit()

    def next_offset(self) -> int | None:
        """The offset that confirms every update seen so far, stored or skipped."""
        seen = self._get(LAST_UPDATE)
        with Session(self._engine) as session:
            stored = session.exec(select(func.max(InboundMessage.telegram_update_id))).one()
        highest = max([int(v) for v in (seen, stored) if v is not None], default=None)
        return None if highest is None else highest + 1

    def mark_seen(self, update_id: int) -> None:
        current = self.next_offset()
        if current is None or update_id >= current:
            self._set(LAST_UPDATE, str(update_id))

    def add(self, update: ParsedUpdate, raw: dict[str, Any], now: datetime) -> bool:
        """Store one update; False when it was already stored."""
        row = InboundMessage(
            telegram_update_id=update.update_id,
            kind=update.kind,
            chat_id=update.chat_id,
            message_id=update.message_id,
            text=update.text,
            file_id=update.file_id,
            sent_at=update.sent_at,
            received_at=now,
            raw=json.dumps(raw, ensure_ascii=False),
        )
        with Session(self._engine) as session:
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                return False
        return True

    def pending(self) -> list[InboundMessage]:
        query = (
            select(InboundMessage)
            .where(col(InboundMessage.processed_at).is_(None))
            .order_by(col(InboundMessage.telegram_update_id))
        )
        with Session(self._engine) as session:
            return list(session.exec(query).all())

    def last_poll_at(self) -> datetime | None:
        value = self._get(LAST_POLL)
        return _utc(datetime.fromisoformat(value)) if value else None

    def set_last_poll_at(self, when: datetime) -> None:
        self._set(LAST_POLL, when.isoformat())

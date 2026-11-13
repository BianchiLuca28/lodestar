"""Drafts and their versions in SQLite. Approval writes the ledger in the same transaction."""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Engine, or_
from sqlmodel import Session, col, select

from lodestar.adapters.db.tables import Draft, DraftVersion, Transaction
from lodestar.adapters.db.transactions_repo import new_row
from lodestar.domain.drafts import DUPLICATE_WINDOW, Existing, ensure_pending
from lodestar.domain.errors import NotFound
from lodestar.domain.ledger import LineInput
from lodestar.domain.money import from_cents


def _dump(lines: Sequence[LineInput]) -> str:
    def row(line: LineInput) -> dict[str, Any]:
        return asdict(line) | {"date": line.date.isoformat(), "amount": str(line.amount)}

    return json.dumps([row(line) for line in lines], ensure_ascii=False)


def _load(text: str) -> list[LineInput]:
    return [
        LineInput(**(d | {"date": date.fromisoformat(d["date"]), "amount": Decimal(d["amount"])}))
        for d in json.loads(text)
    ]


@dataclass(frozen=True)
class StoredVersion:
    version: int
    lines: list[LineInput]
    author: str
    created_at: datetime


@dataclass(frozen=True)
class StoredDraft:
    draft: Draft
    lines: list[LineInput]  # the current version
    versions: list[StoredVersion]


class DraftRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @staticmethod
    def _versions(session: Session, draft_id: int) -> list[StoredVersion]:
        rows = session.exec(
            select(DraftVersion)
            .where(DraftVersion.draft_id == draft_id)
            .order_by(col(DraftVersion.version))
        ).all()
        return [StoredVersion(r.version, _load(r.lines), r.author, r.created_at) for r in rows]

    def _stored(self, session: Session, draft: Draft) -> StoredDraft:
        assert draft.id is not None
        versions = self._versions(session, draft.id)
        return StoredDraft(draft, versions[-1].lines, versions)

    @staticmethod
    def _pending(session: Session, draft_id: int) -> Draft:
        draft = session.get(Draft, draft_id)
        if draft is None:
            raise NotFound(f"draft {draft_id} not found")
        ensure_pending(draft.status)
        return draft

    def _save(self, session: Session, draft: Draft) -> StoredDraft:
        session.add(draft)
        session.commit()
        session.refresh(draft)
        return self._stored(session, draft)

    def create(
        self,
        lines: Sequence[LineInput],
        source: str,
        origin_text: str | None,
        author: str = "ai",
        confidence: float | None = None,
    ) -> StoredDraft:
        now = datetime.now(UTC)
        with Session(self._engine) as session:
            draft = Draft(
                source=source, origin_text=origin_text, confidence=confidence, created_at=now
            )
            session.add(draft)
            session.flush()
            assert draft.id is not None
            session.add(
                DraftVersion(
                    draft_id=draft.id, version=1, lines=_dump(lines), author=author, created_at=now
                )
            )
            return self._save(session, draft)

    def get(self, draft_id: int) -> StoredDraft:
        with Session(self._engine) as session:
            draft = session.get(Draft, draft_id)
            if draft is None:
                raise NotFound(f"draft {draft_id} not found")
            return self._stored(session, draft)

    def by_status(self, status: str | None) -> list[StoredDraft]:
        query = select(Draft).order_by(col(Draft.created_at).desc(), col(Draft.id).desc())
        if status:
            query = query.where(Draft.status == status)
        with Session(self._engine) as session:
            return [self._stored(session, d) for d in session.exec(query).all()]

    def add_version(self, draft_id: int, lines: Sequence[LineInput], author: str) -> StoredDraft:
        with Session(self._engine) as session:
            draft = self._pending(session, draft_id)
            draft.version += 1
            session.add(
                DraftVersion(
                    draft_id=draft_id,
                    version=draft.version,
                    lines=_dump(lines),
                    author=author,
                    created_at=datetime.now(UTC),
                )
            )
            return self._save(session, draft)

    def approve(self, draft_id: int) -> StoredDraft:
        """Write the current lines to the ledger and mark the draft approved: all or nothing."""
        with Session(self._engine) as session:
            draft = self._pending(session, draft_id)
            lines = self._versions(session, draft_id)[-1].lines
            session.add_all([new_row(line, draft.source) for line in lines])
            draft.status, draft.decided_at = "approved", datetime.now(UTC)
            return self._save(session, draft)

    def reject(self, draft_id: int) -> StoredDraft:
        with Session(self._engine) as session:
            draft = self._pending(session, draft_id)
            draft.status, draft.decided_at = "rejected", datetime.now(UTC)
            return self._save(session, draft)

    def near(self, line: LineInput) -> list[Existing]:
        """Ledger lines sharing an account with `line` within the duplicate window."""
        accounts = [a for a in (line.from_account, line.to_account) if a]
        query = select(Transaction).where(
            Transaction.date >= line.date - DUPLICATE_WINDOW,
            Transaction.date <= line.date + DUPLICATE_WINDOW,
            or_(
                col(Transaction.from_account).in_(accounts),
                col(Transaction.to_account).in_(accounts),
            ),
        )
        with Session(self._engine) as session:
            rows = session.exec(query).all()
        return [
            Existing(r.id, r.date, from_cents(r.amount_cents), r.from_account, r.to_account)
            for r in rows
            if r.id is not None
        ]

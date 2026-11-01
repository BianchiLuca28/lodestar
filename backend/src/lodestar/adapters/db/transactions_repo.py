"""Transactions in SQLite."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import Engine, func, or_
from sqlmodel import Session, col, select

from lodestar.adapters.db.tables import BalanceCheck, Transaction
from lodestar.domain.balances import AccountTotals
from lodestar.domain.errors import Conflict, NotFound
from lodestar.domain.ledger import LineInput
from lodestar.domain.money import from_cents, to_cents


@dataclass(frozen=True)
class Filters:
    date_from: date | None = None
    date_to: date | None = None
    account: str | None = None
    category: str | None = None
    tag: str | None = None
    q: str | None = None


def _apply(line: LineInput, row: Transaction) -> None:
    row.date = line.date
    row.amount_cents = to_cents(line.amount)
    row.from_account = line.from_account or None
    row.to_account = line.to_account or None
    row.category = line.category
    row.subcategory = line.subcategory or None
    row.note = line.note or None
    row.tag = line.tag or None
    row.exclude_from_stats = line.exclude_from_stats


def new_row(line: LineInput, source: str) -> Transaction:
    row = Transaction(
        date=line.date,
        amount_cents=0,
        category=line.category,
        source=source,
        created_at=datetime.now(UTC),
    )
    _apply(line, row)
    return row


class TransactionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list(self, filters: Filters, limit: int, offset: int) -> tuple[list[Transaction], int]:
        query = select(Transaction)
        if filters.date_from:
            query = query.where(Transaction.date >= filters.date_from)
        if filters.date_to:
            query = query.where(Transaction.date <= filters.date_to)
        if filters.account:
            query = query.where(
                or_(
                    col(Transaction.from_account) == filters.account,
                    col(Transaction.to_account) == filters.account,
                )
            )
        if filters.category:
            query = query.where(Transaction.category == filters.category)
        if filters.tag:
            query = query.where(Transaction.tag == filters.tag)
        if filters.q:
            pattern = f"%{filters.q.lower()}%"
            query = query.where(
                or_(
                    func.lower(col(Transaction.note)).like(pattern),
                    func.lower(col(Transaction.subcategory)).like(pattern),
                )
            )
        with Session(self._engine) as session:
            total = session.exec(select(func.count()).select_from(query.subquery())).one()
            rows = session.exec(
                query.order_by(col(Transaction.date).desc(), col(Transaction.id).desc())
                .limit(limit)
                .offset(offset)
            ).all()
        return list(rows), total

    def get(self, transaction_id: int) -> Transaction:
        with Session(self._engine) as session:
            row = session.get(Transaction, transaction_id)
        if row is None:
            raise NotFound(f"transaction {transaction_id} not found")
        return row

    def totals(self, account: str, until: date) -> AccountTotals:
        """Money in and out of an account up to and including a date (implements LedgerTotals)."""

        def total(side: str) -> int:
            column = col(getattr(Transaction, side))
            query = select(func.coalesce(func.sum(Transaction.amount_cents), 0)).where(
                column == account, Transaction.date <= until
            )
            with Session(self._engine) as session:
                return int(session.exec(query).one())

        return AccountTotals(from_cents(total("to_account")), from_cents(total("from_account")))

    def count(self) -> int:
        with Session(self._engine) as session:
            return session.exec(select(func.count()).select_from(Transaction)).one()

    def add(self, line: LineInput, source: str) -> Transaction:
        row = new_row(line, source)
        with Session(self._engine) as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        return row

    def add_many(self, lines: Sequence[LineInput], source: str) -> int:
        """Insert every line in one database transaction: all or nothing."""
        with Session(self._engine) as session:
            session.add_all([new_row(line, source) for line in lines])
            session.commit()
        return len(lines)

    def update(self, transaction_id: int, line: LineInput) -> Transaction:
        with Session(self._engine) as session:
            row = session.get(Transaction, transaction_id)
            if row is None:
                raise NotFound(f"transaction {transaction_id} not found")
            _apply(line, row)
            session.add(row)
            session.commit()
            session.refresh(row)
        return row

    def delete(self, transaction_id: int) -> None:
        with Session(self._engine) as session:
            row = session.get(Transaction, transaction_id)
            if row is None:
                raise NotFound(f"transaction {transaction_id} not found")
            linked = session.exec(
                select(BalanceCheck).where(BalanceCheck.adjustment_transaction_id == transaction_id)
            ).first()
            if linked is not None:
                raise Conflict(
                    "error.linkedToBalanceCheck",
                    "this line is the adjustment of a balance check",
                )
            session.delete(row)
            session.commit()

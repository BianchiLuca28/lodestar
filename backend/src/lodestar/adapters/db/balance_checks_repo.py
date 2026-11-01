"""Balance checks in SQLite, each with its optional adjustment line."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Engine
from sqlmodel import Session, col, select

from lodestar.adapters.db.tables import BalanceCheck, Transaction
from lodestar.adapters.db.transactions_repo import new_row
from lodestar.domain.ledger import LineInput
from lodestar.domain.money import to_cents


@dataclass(frozen=True)
class StoredCheck:
    check: BalanceCheck
    adjustment: Transaction | None


class BalanceCheckRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(
        self,
        account: str,
        on: date,
        real: Decimal,
        computed: Decimal,
        adjustment: LineInput | None,
    ) -> StoredCheck:
        """Write the check and its adjustment line in one database transaction."""
        with Session(self._engine) as session:
            line = new_row(adjustment, source="adjustment") if adjustment else None
            if line is not None:
                session.add(line)
                session.flush()
            check = BalanceCheck(
                account=account,
                date=on,
                real_balance_cents=to_cents(real),
                computed_balance_cents=to_cents(computed),
                adjustment_transaction_id=line.id if line else None,
                created_at=datetime.now(UTC),
            )
            session.add(check)
            session.commit()
            session.refresh(check)
            if line is not None:
                session.refresh(line)
            return StoredCheck(check, line)

    def history(self, account: str | None = None) -> list[StoredCheck]:
        query = select(BalanceCheck, Transaction).join(
            Transaction,
            col(BalanceCheck.adjustment_transaction_id) == col(Transaction.id),
            isouter=True,
        )
        if account:
            query = query.where(BalanceCheck.account == account)
        query = query.order_by(col(BalanceCheck.date).desc(), col(BalanceCheck.id).desc())
        with Session(self._engine) as session:
            return [StoredCheck(check, line) for check, line in session.exec(query).all()]

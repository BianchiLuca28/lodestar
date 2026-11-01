"""SQLModel tables (design §5). Money columns are integer cents; accounts and categories are
config names, not foreign keys."""

import datetime as dt
from typing import ClassVar

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel

SOURCES = ("manual", "telegram", "receipt", "bank_xlsx", "import", "adjustment")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Transaction(SQLModel, table=True):
    __tablename__: ClassVar[str] = "transactions"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("from_account IS NOT NULL OR to_account IS NOT NULL", name="has_account"),
        CheckConstraint(_in("source", SOURCES), name="known_source"),
    )

    id: int | None = Field(default=None, primary_key=True)
    date: dt.date = Field(index=True)
    amount_cents: int
    from_account: str | None = Field(default=None, index=True)
    to_account: str | None = Field(default=None, index=True)
    category: str = Field(index=True)
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = Field(default=None, index=True)
    exclude_from_stats: bool = False
    source: str = "manual"
    created_at: dt.datetime  # UTC


class BalanceCheck(SQLModel, table=True):
    __tablename__: ClassVar[str] = "balance_checks"

    id: int | None = Field(default=None, primary_key=True)
    account: str = Field(index=True)
    date: dt.date
    real_balance_cents: int
    computed_balance_cents: int
    adjustment_transaction_id: int | None = Field(default=None, foreign_key="transactions.id")
    created_at: dt.datetime


class PlannedExpense(SQLModel, table=True):
    __tablename__: ClassVar[str] = "planned_expenses"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint(_in("status", ("planned", "done", "cancelled")), name="known_status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    amount_cents: int
    expected_date: dt.date | None = None
    status: str = "planned"
    note: str | None = None


class Instrument(SQLModel, table=True):
    __tablename__: ClassVar[str] = "instruments"

    id: int | None = Field(default=None, primary_key=True)
    ticker: str | None = None
    isin: str = Field(unique=True)
    name: str
    asset_class: str  # equity_etf · money_market_etf · govt_bond
    tax_rate: str  # Decimal as text, e.g. "0.125"
    price_provider: str | None = None
    bucket: str
    maturity: dt.date | None = None
    coupon_rate: str | None = None  # Decimal as text, e.g. "0.0325"
    coupon_dates: str | None = None  # e.g. "05-15,11-15"


class Trade(SQLModel, table=True):
    __tablename__: ClassVar[str] = "trades"
    __table_args__ = (CheckConstraint(_in("side", ("buy", "sell")), name="known_side"),)

    id: int | None = Field(default=None, primary_key=True)
    date: dt.date
    instrument_id: int = Field(foreign_key="instruments.id", index=True)
    side: str
    # Decimals as text, exact. Bonds: nominal and price in % of nominal (4 decimals).
    # ETFs: units and € price.
    quantity: str
    price: str
    accrued_interest_cents: int = 0
    fees_cents: int = 0
    account: str
    transaction_id: int | None = Field(default=None, foreign_key="transactions.id")

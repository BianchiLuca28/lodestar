"""Initial schema: transactions, balance checks, planned expenses, instruments, trades.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SOURCES = "'manual', 'telegram', 'receipt', 'bank_xlsx', 'import', 'adjustment'"


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("from_account", sa.String, index=True),
        sa.Column("to_account", sa.String, index=True),
        sa.Column("category", sa.String, nullable=False, index=True),
        sa.Column("subcategory", sa.String),
        sa.Column("note", sa.String),
        sa.Column("tag", sa.String, index=True),
        sa.Column("exclude_from_stats", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("amount_cents > 0", name="amount_positive"),
        sa.CheckConstraint(
            "from_account IS NOT NULL OR to_account IS NOT NULL", name="has_account"
        ),
        sa.CheckConstraint(f"source IN ({SOURCES})", name="known_source"),
    )
    op.create_table(
        "balance_checks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account", sa.String, nullable=False, index=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("real_balance_cents", sa.Integer, nullable=False),
        sa.Column("computed_balance_cents", sa.Integer, nullable=False),
        sa.Column("adjustment_transaction_id", sa.Integer, sa.ForeignKey("transactions.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "planned_expenses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("expected_date", sa.Date),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("note", sa.String),
        sa.CheckConstraint("amount_cents > 0", name="amount_positive"),
        sa.CheckConstraint("status IN ('planned', 'done', 'cancelled')", name="known_status"),
    )
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ticker", sa.String),
        sa.Column("isin", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("asset_class", sa.String, nullable=False),
        sa.Column("tax_rate", sa.String, nullable=False),
        sa.Column("price_provider", sa.String),
        sa.Column("bucket", sa.String, nullable=False),
        sa.Column("maturity", sa.Date),
        sa.Column("coupon_rate", sa.String),
        sa.Column("coupon_dates", sa.String),
    )
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column(
            "instrument_id",
            sa.Integer,
            sa.ForeignKey("instruments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("side", sa.String, nullable=False),
        sa.Column("quantity", sa.String, nullable=False),
        sa.Column("price", sa.String, nullable=False),
        sa.Column("accrued_interest_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fees_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("account", sa.String, nullable=False),
        sa.Column("transaction_id", sa.Integer, sa.ForeignKey("transactions.id")),
        sa.CheckConstraint("side IN ('buy', 'sell')", name="known_side"),
    )


def downgrade() -> None:
    for table in ("trades", "instruments", "planned_expenses", "balance_checks", "transactions"):
        op.drop_table(table)

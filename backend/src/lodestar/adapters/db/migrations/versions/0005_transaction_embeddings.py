"""Embeddings of past transactions, the few-shot example index (design §6.1).

A cache: rows can be dropped and rebuilt from `transactions` at any time.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transaction_embeddings",
        sa.Column(
            "transaction_id",
            sa.Integer,
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("model", sa.String, nullable=False),
        sa.Column("text", sa.String, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=False),  # float32, sqlite-vec format
    )


def downgrade() -> None:
    op.drop_table("transaction_embeddings")

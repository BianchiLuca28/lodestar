"""Drafts and their versions.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("status", sa.String, nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("origin_text", sa.String),
        sa.Column("inbound_message_id", sa.Integer),
        sa.Column("confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("decided_at", sa.DateTime),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="known_status"),
        sa.CheckConstraint("source IN ('telegram', 'receipt', 'bank_xlsx')", name="known_source"),
    )
    op.create_table(
        "draft_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("draft_id", sa.Integer, sa.ForeignKey("drafts.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("lines", sa.String, nullable=False),
        sa.Column("author", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("author IN ('ai', 'user')", name="known_author"),
    )


def downgrade() -> None:
    op.drop_table("draft_versions")
    op.drop_table("drafts")

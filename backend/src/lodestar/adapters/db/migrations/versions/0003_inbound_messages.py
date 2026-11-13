"""Inbound Telegram messages, app state, and the draft → message link.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inbound_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_update_id", sa.Integer, nullable=False, unique=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("chat_id", sa.Integer, nullable=False),
        sa.Column("message_id", sa.Integer),
        sa.Column("text", sa.String),
        sa.Column("file_id", sa.String),
        sa.Column("sent_at", sa.DateTime, nullable=False),
        sa.Column("received_at", sa.DateTime, nullable=False),
        sa.Column("processed_at", sa.DateTime, index=True),
        sa.Column("raw", sa.String, nullable=False),
        sa.CheckConstraint("kind IN ('text', 'photo', 'document', 'callback')", name="known_kind"),
    )
    op.create_table(
        "app_state",
        sa.Column("key", sa.String, primary_key=True),
        sa.Column("value", sa.String, nullable=False),
    )
    # SQLite cannot add a foreign key in place; batch mode rebuilds the table.
    with op.batch_alter_table("drafts") as batch:
        batch.create_foreign_key(
            "fk_drafts_inbound_message", "inbound_messages", ["inbound_message_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("drafts") as batch:
        batch.drop_constraint("fk_drafts_inbound_message", type_="foreignkey")
    op.drop_table("app_state")
    op.drop_table("inbound_messages")

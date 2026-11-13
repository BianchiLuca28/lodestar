"""Drafts remember why the parser could not produce valid lines.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("drafts", sa.Column("review_note", sa.String))


def downgrade() -> None:
    with op.batch_alter_table("drafts") as batch:
        batch.drop_column("review_note")

"""Alembic environment. The URL comes from the Config built in engine.py, not from alembic.ini."""

from pathlib import Path

from alembic import context
from sqlmodel import SQLModel

import lodestar.adapters.db.tables  # noqa: F401  (registers the tables on SQLModel.metadata)
from lodestar.adapters.db.engine import make_engine

url = context.config.get_main_option("sqlalchemy.url")
if url is None:
    raise RuntimeError("sqlalchemy.url is not set; run migrations through engine.migrate()")
engine = make_engine(Path(url.removeprefix("sqlite:///")))

with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=SQLModel.metadata,
        render_as_batch=True,  # SQLite needs batch mode to alter tables
    )
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()

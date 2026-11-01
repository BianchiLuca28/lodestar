"""SQLite engine (WAL, foreign keys) and Alembic migrations, configured in code."""

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine, create_engine, event

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DB_FILE = "lodestar.db"


def db_path(data_dir: Path) -> Path:
    return data_dir / DB_FILE


def make_engine(db: Path) -> Engine:
    engine = create_engine(f"sqlite:///{db.as_posix()}")

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_conn: Any, _record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _alembic_config(db: Path) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def migrate(db: Path) -> None:
    """Bring the database at `db` to the latest revision, creating the file if needed."""
    db.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(_alembic_config(db), "head")


def downgrade_all(db: Path) -> None:
    command.downgrade(_alembic_config(db), "base")


def current_revision(db: Path) -> str | None:
    engine = make_engine(db)
    try:
        with engine.connect() as conn:
            return MigrationContext.configure(conn).get_current_revision()
    finally:
        engine.dispose()

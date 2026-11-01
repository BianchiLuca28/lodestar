import sqlite3
from pathlib import Path

import pytest

from lodestar.adapters.db.engine import current_revision, downgrade_all, migrate

TABLES = {"transactions", "balance_checks", "planned_expenses", "instruments", "trades"}


def tables(db: Path) -> set[str]:
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows} - {"alembic_version"}


def insert(db: Path, amount: int, from_account: str | None, to_account: str | None) -> None:
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO transactions (date, amount_cents, from_account, to_account, category,"
            " exclude_from_stats, source, created_at)"
            " VALUES ('2026-03-14', ?, ?, ?, 'X', 0, 'manual', '2026-03-14T10:00:00')",
            (amount, from_account, to_account),
        )


def test_upgrade_creates_tables_in_wal_mode(tmp_path: Path) -> None:
    db = tmp_path / "lodestar.db"
    migrate(db)
    assert tables(db) == TABLES
    assert current_revision(db) == "0001"
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_upgrade_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "lodestar.db"
    migrate(db)
    migrate(db)
    assert current_revision(db) == "0001"


def test_valid_transaction_accepted(tmp_path: Path) -> None:
    db = tmp_path / "lodestar.db"
    migrate(db)
    insert(db, 1250, "Banca Aurora", None)


@pytest.mark.parametrize(
    ("amount", "from_account", "to_account"),
    [(0, "Banca Aurora", None), (-5, "Banca Aurora", None), (100, None, None)],
)
def test_check_constraints(
    tmp_path: Path, amount: int, from_account: str | None, to_account: str | None
) -> None:
    db = tmp_path / "lodestar.db"
    migrate(db)
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, amount, from_account, to_account)


def test_downgrade_removes_everything(tmp_path: Path) -> None:
    db = tmp_path / "lodestar.db"
    migrate(db)
    downgrade_all(db)
    assert tables(db) == set()
    assert current_revision(db) is None


def test_models_match_migrations(tmp_path: Path) -> None:
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext
    from sqlmodel import SQLModel

    import lodestar.adapters.db.tables  # noqa: F401
    from lodestar.adapters.db.engine import make_engine

    db = tmp_path / "lodestar.db"
    migrate(db)
    engine = make_engine(db)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), SQLModel.metadata)
    engine.dispose()
    assert diff == [], "SQLModel tables and migrations disagree; add a migration"

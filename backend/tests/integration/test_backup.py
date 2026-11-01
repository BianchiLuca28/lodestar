import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lodestar.jobs.backup import (
    BackupNotValid,
    backup_if_due,
    backups_in,
    restore,
    run_backup,
)
from lodestar.jobs.initial_import import run_import

ROOT = Path(__file__).parents[3]
EXAMPLE = ROOT / "config.example"
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def ledger(db: Path) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute("SELECT * FROM transactions ORDER BY id").fetchall()
    finally:
        conn.close()  # Windows keeps an open file locked


@pytest.fixture
def data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    run_import(EXAMPLE / "ledger.csv", EXAMPLE, data, dry_run=False)
    return data


def test_backup_then_restore_into_a_new_path_gives_the_same_rows(
    data: Path, tmp_path: Path
) -> None:
    backup = run_backup(data / "lodestar.db", tmp_path / "backups", NOW)
    assert backup.name == "lodestar-20261101-120000.db"
    target = tmp_path / "elsewhere" / "lodestar.db"
    restore(backup, target)
    assert ledger(target) == ledger(data / "lodestar.db")


def test_restore_keeps_the_replaced_database_aside(data: Path, tmp_path: Path) -> None:
    db = data / "lodestar.db"
    backup = run_backup(db, tmp_path / "backups", NOW)
    conn = sqlite3.connect(db)
    with conn:
        conn.execute("DELETE FROM transactions")
    conn.close()
    aside = restore(backup, db, now=NOW)
    assert aside is not None and aside.exists()
    assert ledger(aside) == []
    assert len(ledger(db)) > 0


def test_restore_refuses_a_file_that_is_not_a_lodestar_backup(data: Path, tmp_path: Path) -> None:
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"not a database")
    before = ledger(data / "lodestar.db")
    with pytest.raises(BackupNotValid):
        restore(junk, data / "lodestar.db")
    assert ledger(data / "lodestar.db") == before


def test_backup_if_due_catches_up_and_prunes(data: Path, tmp_path: Path) -> None:
    folder = tmp_path / "backups"
    folder.mkdir()
    for days in range(40):
        stamp = NOW - timedelta(days=days + 2)
        (folder / f"lodestar-{stamp:%Y%m%d-%H%M%S}.db").write_bytes(b"")
    (folder / "notes.txt").write_text("mine")

    made = backup_if_due(data / "lodestar.db", folder, NOW)
    assert made is not None
    assert backup_if_due(data / "lodestar.db", folder, NOW + timedelta(hours=1)) is None
    remaining = backups_in(folder)
    assert len(remaining) < 41
    assert (folder / "notes.txt").exists()


def test_health_reports_the_last_backup(app: FastAPI) -> None:
    client = TestClient(app)
    status = client.get("/api/health").json()["backup"]
    assert status == {"enabled": True, "last_backup": None, "folder": "backups"}
    run_backup(app.state.db_path, app.state.db_path.parent / "backups", NOW)
    status = client.get("/api/health").json()["backup"]
    assert status["last_backup"].startswith("2026-11-01T12:00:00")


def test_app_startup_catches_up_with_a_backup(app: FastAPI) -> None:
    import time

    folder = app.state.db_path.parent / "backups"
    with TestClient(app):
        deadline = time.monotonic() + 5
        while not backups_in(folder) and time.monotonic() < deadline:
            time.sleep(0.05)
    assert len(backups_in(folder)) == 1

import sqlite3
from pathlib import Path

import pytest

from lodestar.jobs.initial_import import LedgerNotEmpty, main, run_import

ROOT = Path(__file__).parents[3]
EXAMPLE = ROOT / "config.example"
FAKE_LEDGER = EXAMPLE / "ledger.csv"


def count(data_dir: Path) -> int:
    with sqlite3.connect(data_dir / "lodestar.db") as conn:
        return int(conn.execute("SELECT count(*) FROM transactions").fetchone()[0])


def sources(data_dir: Path) -> set[str]:
    with sqlite3.connect(data_dir / "lodestar.db") as conn:
        return {r[0] for r in conn.execute("SELECT DISTINCT source FROM transactions")}


def test_fake_ledger_imports_fully(tmp_path: Path) -> None:
    outcome = run_import(FAKE_LEDGER, EXAMPLE, tmp_path, dry_run=False)
    expected = len(FAKE_LEDGER.read_text("utf-8").splitlines()) - 1
    assert outcome.written == expected == count(tmp_path)
    assert sources(tmp_path) == {"import"}


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    outcome = run_import(FAKE_LEDGER, EXAMPLE, tmp_path, dry_run=True)
    assert outcome.written == 0
    assert outcome.summary.count > 0
    assert count(tmp_path) == 0


def test_second_import_refused(tmp_path: Path) -> None:
    run_import(FAKE_LEDGER, EXAMPLE, tmp_path, dry_run=False)
    with pytest.raises(LedgerNotEmpty):
        run_import(FAKE_LEDGER, EXAMPLE, tmp_path, dry_run=False)


def test_one_bad_row_writes_nothing(tmp_path: Path) -> None:
    broken = tmp_path / "broken.csv"
    lines = FAKE_LEDGER.read_text("utf-8").splitlines()
    lines.append("2026-10-31,5.00,Banca Fantasma,,❓ Varie,,Riga rotta,,false")
    broken.write_text("\n".join(lines) + "\n", encoding="utf-8")
    outcome = run_import(broken, EXAMPLE, tmp_path / "data", dry_run=False)
    assert outcome.written == 0
    assert outcome.errors
    assert count(tmp_path / "data") == 0


def test_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    args = [str(FAKE_LEDGER), "--config", str(EXAMPLE), "--data", str(tmp_path)]
    assert main([*args, "--dry-run"]) == 0
    assert "dry run" in capsys.readouterr().out.lower()
    assert main(args) == 0
    assert main(args) == 2  # ledger not empty
    assert "una volta sola" in capsys.readouterr().err

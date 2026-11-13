import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest
import yaml

from lodestar.adapters.embeddings import HashingEmbedder
from lodestar.ai.evals.predictor import ScriptedPredictor
from lodestar.ai.evals.runner import DEFAULT_DATASET, run
from lodestar.ai.evals.schema import Case, Line, load_cases

CONFIG_DIR = Path(__file__).parents[3] / "config.example"


def test_dataset_parses_and_uses_the_fake_persona() -> None:
    cases = load_cases(DEFAULT_DATASET)
    assert 25 <= len(cases) <= 40
    assert len({c.id for c in cases}) == len(cases)
    accounts = {
        a["name"]
        for a in yaml.safe_load((CONFIG_DIR / "accounts.yaml").read_text("utf-8"))["accounts"]
    }
    cats = {
        c["name"]: set(c["subcategories"])
        for c in yaml.safe_load((CONFIG_DIR / "categories.yaml").read_text("utf-8"))["categories"]
    }
    for case in cases:
        for ln in case.expected:
            assert ln.from_account or ln.to_account, case.id
            for acc in (ln.from_account, ln.to_account):
                assert acc is None or acc in accounts, case.id
            assert ln.category in cats, case.id
            assert ln.subcategory is None or ln.subcategory in cats[ln.category], case.id
    assert any(len(c.expected) == 2 for c in cases)  # split bill
    assert any(ln.tag for c in cases for ln in c.expected)  # trip tag
    dated = [c for c in cases if c.expected[0].date != c.sent_at.date()]
    assert len(dated) >= 12  # dates written in the message (ieri, giovedì, il 2 novembre...)


def test_fake_run_writes_results_and_prints_table(tmp_path: Path) -> None:
    cases = load_cases(DEFAULT_DATASET)
    path, table = run(cases, ScriptedPredictor.from_cases(cases), tmp_path, today=date(2026, 11, 1))
    assert path.name == "2026-11-01_fake_v0.json"
    data = json.loads(path.read_text("utf-8"))
    assert data["model"] == "fake" and data["prompt_version"] == "v0"
    assert data["cases"] == len(cases)
    assert data["metrics"]["category_accuracy"] == 1.0
    assert "| category_accuracy | 1.000 |" in table


def test_compare_shows_before_and_after(tmp_path: Path) -> None:
    cases = load_cases(DEFAULT_DATASET)
    first = ScriptedPredictor({c.message: [] for c in cases})
    run(cases, first, tmp_path, today=date(2026, 10, 1))
    _, table = run(
        cases, ScriptedPredictor.from_cases(cases), tmp_path, today=date(2026, 11, 1), compare=True
    )
    assert "| Metric | Before | After |" in table
    assert "| line_count_accuracy | 0.000 | 1.000 |" in table


def test_results_include_seconds_per_case(tmp_path: Path) -> None:
    cases = load_cases(DEFAULT_DATASET)
    path, _ = run(cases, ScriptedPredictor.from_cases(cases), tmp_path, today=date(2026, 11, 1))
    seconds = json.loads(path.read_text("utf-8"))["metrics"]["seconds_per_case"]
    assert 0 <= seconds < 1


def test_the_predictor_sees_the_case_source_row_for_leave_one_out(tmp_path: Path) -> None:
    seen: list[int | None] = []

    class Spy(ScriptedPredictor):
        def predict(self, case: Case) -> list[Line]:
            seen.append(case.source_id)
            return super().predict(case)

    case = Case.model_validate(
        {
            "id": "x",
            "message": "m",
            "sent_at": "2026-11-05T10:00:00+01:00",
            "source_id": 7,
            "expected": [],
        }
    )
    run([case], Spy({}), tmp_path, today=date(2026, 11, 1))
    assert seen == [7]


def test_private_runs_read_and_write_only_git_ignored_folders() -> None:
    from lodestar.ai.evals.runner import REPO_ROOT, paths

    dataset, results, config = paths(private=True)
    assert dataset == REPO_ROOT / "evals" / "data" / "private" / "cases.jsonl"
    assert results == REPO_ROOT / "evals" / "results" / "private"
    assert config == REPO_ROOT / "config"
    ignored = (REPO_ROOT / ".gitignore").read_text("utf-8")
    assert "evals/data/private/" in ignored and "evals/results/private/" in ignored
    assert paths(private=False)[2] == REPO_ROOT / "config.example"


def test_a_private_run_migrates_the_database_before_indexing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lodestar.adapters.db.engine import migrate
    from lodestar.ai.evals import runner

    db = tmp_path / "lodestar.db"
    migrate(db)
    with sqlite3.connect(db) as conn:  # a database from before the example index existed
        conn.execute("DROP TABLE transaction_embeddings")
        conn.execute("UPDATE alembic_version SET version_num = '0004'")
    conn.close()
    monkeypatch.setattr(runner, "PRIVATE_DB", db)
    index = runner.private_index(HashingEmbedder(), "fake")
    assert index.sync() == 0  # the table exists again; nothing to embed


def test_a_run_can_write_the_misses_report(tmp_path: Path) -> None:
    cases = load_cases(DEFAULT_DATASET)
    report = tmp_path / "private" / "misses.md"
    run(cases, ScriptedPredictor({}), tmp_path, today=date(2026, 11, 1), misses=report)
    text = report.read_text("utf-8")
    assert f"{len(cases)} of {len(cases)} cases" in text


def test_private_runs_put_the_report_next_to_their_results() -> None:
    from lodestar.ai.evals.runner import PRIVATE_RESULTS, misses_path

    assert misses_path(private=True) == PRIVATE_RESULTS / "misses.md"
    assert misses_path(private=False) is None

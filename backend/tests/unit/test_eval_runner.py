import json
from datetime import date
from pathlib import Path

import yaml

from lodestar.ai.evals.predictor import ScriptedPredictor
from lodestar.ai.evals.runner import DEFAULT_DATASET, run
from lodestar.ai.evals.schema import load_cases

CONFIG_DIR = Path(__file__).parents[3] / "config.example"


def test_dataset_parses_and_uses_the_fake_persona() -> None:
    cases = load_cases(DEFAULT_DATASET)
    assert 10 <= len(cases) <= 20
    assert len({c.id for c in cases}) == len(cases)
    accounts = {a["name"] for a in yaml.safe_load((CONFIG_DIR / "accounts.yaml").read_text("utf-8"))["accounts"]}
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

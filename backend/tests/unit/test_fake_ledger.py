"""Checks the committed fake ledger in config.example/ledger.csv."""

import csv
import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).parents[3]
CONFIG_DIR = ROOT / "config.example"
LEDGER = CONFIG_DIR / "ledger.csv"
SCRIPT = ROOT / "backend" / "scripts" / "gen_fake_ledger.py"
HEADER = [
    "date",
    "amount",
    "from_account",
    "to_account",
    "category",
    "subcategory",
    "note",
    "tag",
    "exclude_from_stats",
]


def rows() -> list[dict[str, str]]:
    with LEDGER.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def config(name: str) -> Any:
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def load_generator() -> Callable[[int], str]:
    spec = importlib.util.spec_from_file_location("gen_fake_ledger", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Callable[[int], str], module.generate)


def test_header_is_the_csv_loader_layout() -> None:
    with LEDGER.open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == HEADER


def test_row_count_and_formats() -> None:
    data = rows()
    assert 270 <= len(data) <= 330
    for r in data:
        assert re.fullmatch(r"\d+\.\d{2}", r["amount"]) and float(r["amount"]) > 0, r
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]), r
        assert r["exclude_from_stats"] in {"true", "false"}, r
    months = {r["date"][:7] for r in data}
    assert 9 <= len(months) <= 11


def test_every_direction_present_and_every_row_has_an_account() -> None:
    data = rows()
    assert all(r["from_account"] or r["to_account"] for r in data)
    assert any(r["from_account"] and not r["to_account"] for r in data)  # expense
    assert any(r["to_account"] and not r["from_account"] for r in data)  # income
    assert any(r["from_account"] and r["to_account"] for r in data)  # transfer


def test_accounts_and_categories_are_known() -> None:
    accounts = {a["name"] for a in config("accounts.yaml")["accounts"]}
    categories = {
        c["name"]: set(c["subcategories"]) for c in config("categories.yaml")["categories"]
    }
    for r in rows():
        for acc in (r["from_account"], r["to_account"]):
            assert not acc or acc in accounts, r
        assert r["category"] in categories, r
        assert not r["subcategory"] or r["subcategory"] in categories[r["category"]], r


def test_refunds_trip_tag_and_excluded_rows() -> None:
    data = rows()
    refunds = [
        r
        for r in data
        if r["to_account"] and not r["from_account"] and r["category"] != "💰 Stipendio"
    ]
    assert len(refunds) >= 3
    assert any(r["tag"] for r in data)
    assert 2 <= sum(r["exclude_from_stats"] == "true" for r in data) <= 3


def test_same_seed_reproduces_the_committed_file() -> None:
    generate = load_generator()
    assert generate(2026).encode("utf-8") == LEDGER.read_bytes()

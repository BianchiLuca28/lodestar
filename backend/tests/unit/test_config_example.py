"""Checks the fake persona in config.example/ is complete and coherent.

The Pydantic config models arrive in v0.1 and will replace these structural checks.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

CONFIG_DIR = Path(__file__).parents[3] / "config.example"
YAML_FILES = [
    "settings.yaml",
    "accounts.yaml",
    "categories.yaml",
    "buckets.yaml",
    "rules.yaml",
    "instrument_policy.yaml",
]
RULE_KINDS = {
    "discretionary_cap",
    "p1_range",
    "safety_valve",
    "surplus",
    "contributions",
    "quarterly_order",
    "maturity_reinvestment",
    "p3_horizon",
    "trajectory",
    "emergency_fund",
    "never_touch",
    "p4_review_threshold",
}
ACCOUNT_TYPES = {"cash", "bank", "broker", "postal"}


def load(name: str) -> Any:
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def plan_sections() -> set[str]:
    text = (CONFIG_DIR / "plan.md").read_text(encoding="utf-8")
    return set(re.findall(r"^#+\s+§?(\d+(?:\.\d+)*)\b", text, re.M))


@pytest.mark.parametrize("name", YAML_FILES)
def test_yaml_files_parse(name: str) -> None:
    assert isinstance(load(name), dict)


def test_settings_cover_locale_models_backups_notifications() -> None:
    s = load("settings.yaml")
    assert s["locale"] == "it"
    assert s["currency"] == "EUR"
    assert s["llm"]["base_url"].startswith("http")
    assert set(s["models"]) == {"parse", "chat", "vision", "embed"}
    assert all(t["enabled"] is False for t in s["backup"]["targets"])
    assert "notifications" in s


def test_accounts_reference_buckets_and_have_one_default() -> None:
    accounts = load("accounts.yaml")["accounts"]
    buckets = {b["id"] for b in load("buckets.yaml")["buckets"]}
    assert 5 <= len(accounts) <= 6
    assert {a["type"] for a in accounts} == ACCOUNT_TYPES
    assert all(a["bucket"] in buckets for a in accounts)
    assert sum(1 for a in accounts if a.get("is_default")) == 1


def test_categories_have_subcategories_and_discretionary_flag() -> None:
    categories = load("categories.yaml")["categories"]
    assert all(isinstance(c["discretionary"], bool) for c in categories)
    assert all(isinstance(c["subcategories"], list) for c in categories)
    assert any(c["discretionary"] for c in categories)


def test_four_buckets_and_house_date_on_p3() -> None:
    buckets = {b["id"]: b for b in load("buckets.yaml")["buckets"]}
    assert set(buckets) == {"P1", "P2", "P3", "P4"}
    for b in buckets.values():
        for field in ("name", "purpose", "risk", "target", "monthly_contribution", "horizon"):
            assert field in b, f"{b['id']} missing {field}"
    assert "expected_house_date" in buckets["P3"]


def test_rules_cover_every_kind_and_cite_existing_plan_sections() -> None:
    rules = load("rules.yaml")["rules"]
    assert {r["kind"] for r in rules} == RULE_KINDS
    sections = plan_sections()
    for r in rules:
        assert r["plan_section"], r["kind"]
        for ref in r["plan_section"]:
            assert ref in sections, f"{r['kind']} cites missing plan §{ref}"


def test_discretionary_categories_exist() -> None:
    names = {c["name"] for c in load("categories.yaml")["categories"]}
    cap = next(r for r in load("rules.yaml")["rules"] if r["kind"] == "discretionary_cap")
    flagged = {c["name"] for c in load("categories.yaml")["categories"] if c["discretionary"]}
    assert flagged <= names
    assert cap["limit"] > 0


def test_instrument_policy_buckets_and_alternation_pair() -> None:
    policy = load("instrument_policy.yaml")
    buckets = {b["id"] for b in load("buckets.yaml")["buckets"]}
    assert set(policy["buckets"]) <= buckets
    pair = policy["buckets"]["P3"]["alternation_pair"]
    assert {p["country"] for p in pair} == {"IT", "DE"}
    assert policy["never_buy"]


def test_no_pension_fund_anywhere() -> None:
    for path in CONFIG_DIR.iterdir():
        text = path.read_text(encoding="utf-8").lower()
        for word in ("pension", "fondo pensione", "previdenz"):
            assert word not in text, f"{path.name} mentions {word!r} (ADR 0017)"

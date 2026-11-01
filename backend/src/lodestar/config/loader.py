"""Load and validate config/ (design §9). Any problem raises ConfigError naming file and field."""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from lodestar.config.models import (
    AccountsFile,
    AppConfig,
    BucketsFile,
    CategoriesFile,
    InstrumentPolicyFile,
    RulesFile,
    SettingsFile,
)

PLAN_FILE = "plan.md"
_HEADING = re.compile(r"^#+\s+§?(\d+(?:\.\d+)*)\b", re.M)


class ConfigError(Exception):
    """The config directory is missing or a file in it is invalid."""


def _loc(parts: tuple[int | str, ...]) -> str:
    out = ""
    for p in parts:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out


def _read_yaml(path: Path) -> Any:
    if not path.is_file():
        raise ConfigError(f"{path.name}: file missing in {path.parent}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path.name}: invalid YAML: {exc}") from exc


def _parse[M: BaseModel](directory: Path, name: str, model: type[M]) -> M:
    data = _read_yaml(directory / name)
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        lines = [
            f"{name} → {_loc(err['loc'])}: {err['msg']}" for err in exc.errors(include_url=False)
        ]
        raise ConfigError("\n".join(lines)) from exc


def plan_sections(plan: str) -> set[str]:
    return set(_HEADING.findall(plan))


def _cross_check(cfg: AppConfig) -> Iterator[str]:
    buckets = {b.id for b in cfg.buckets}
    accounts = {a.name for a in cfg.accounts}
    sections = plan_sections(cfg.plan)

    defaults = [a.name for a in cfg.accounts if a.is_default]
    if len(defaults) != 1:
        yield f"accounts.yaml → accounts: exactly one default account needed, found {defaults}"
    for i, a in enumerate(cfg.accounts):
        if a.bucket not in buckets:
            yield f"accounts.yaml → accounts[{i}].bucket: unknown bucket {a.bucket!r}"

    names = [c.name for c in cfg.categories]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        yield f"categories.yaml → categories: duplicate category {dup!r}"

    adjustment = cfg.settings.ledger.adjustment_category
    if adjustment not in names:
        yield f"settings.yaml → ledger.adjustment_category: unknown category {adjustment!r}"

    trade_account = cfg.settings.portfolio.trade_account
    if trade_account not in accounts:
        yield f"settings.yaml → portfolio.trade_account: unknown account {trade_account!r}"
    imp = cfg.settings.initial_import
    for label, mapping in [*imp.asset_classes.items(), *imp.instruments.items()]:
        if mapping.bucket not in buckets:
            yield (
                f"settings.yaml → initial_import.asset_classes.{label}.bucket: "
                f"unknown bucket {mapping.bucket!r}"
            )
    if imp.adjustment is not None:
        if imp.adjustment.account not in accounts:
            yield (
                "settings.yaml → initial_import.adjustment.account: "
                f"unknown account {imp.adjustment.account!r}"
            )
        if imp.adjustment.category not in names:
            yield (
                "settings.yaml → initial_import.adjustment.category: "
                f"unknown category {imp.adjustment.category!r}"
            )

    for i, rule in enumerate(cfg.rules):
        where = f"rules.yaml → rules[{i}]"
        for ref in rule.plan_section:
            if ref not in sections:
                yield f"{where}.plan_section: plan.md has no section {ref!r}"
        for field in ("account",):
            value = getattr(rule, field, None)
            if value is not None and value not in accounts:
                yield f"{where}.{field}: unknown account {value!r}"
        refs = [getattr(rule, "bucket", None), *getattr(rule, "buckets", [])]
        if hasattr(rule, "destination"):
            refs += [d.bucket for d in rule.destination]
        if hasattr(rule, "reduced_transfer"):
            refs += list(rule.reduced_transfer)
        for ref in refs:
            if ref is not None and ref not in buckets:
                yield f"{where}: unknown bucket {ref!r}"
        if hasattr(rule, "transfer"):
            for end in (rule.transfer.from_, rule.transfer.to):
                if end not in accounts:
                    yield f"{where}.transfer: unknown account {end!r}"

    for key in cfg.instrument_policy.buckets:
        if key not in buckets:
            yield f"instrument_policy.yaml → buckets.{key}: unknown bucket {key!r}"


def load_config(directory: Path) -> AppConfig:
    if not directory.is_dir():
        raise ConfigError(
            f"Config directory {directory} not found. Start from the example: "
            "cp -r config.example config"
        )
    plan_path = directory / PLAN_FILE
    if not plan_path.is_file():
        raise ConfigError(f"{PLAN_FILE}: file missing in {directory}")
    cfg = AppConfig(
        settings=_parse(directory, "settings.yaml", SettingsFile),
        accounts=_parse(directory, "accounts.yaml", AccountsFile).accounts,
        categories=_parse(directory, "categories.yaml", CategoriesFile).categories,
        buckets=_parse(directory, "buckets.yaml", BucketsFile).buckets,
        rules=_parse(directory, "rules.yaml", RulesFile).rules,
        instrument_policy=_parse(directory, "instrument_policy.yaml", InstrumentPolicyFile),
        plan=plan_path.read_text(encoding="utf-8"),
    )
    problems = list(_cross_check(cfg))
    if problems:
        raise ConfigError("\n".join(problems))
    return cfg

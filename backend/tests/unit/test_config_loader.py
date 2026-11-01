"""The config loader: config.example/ loads, and every broken file names the file and field."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from lodestar.config.loader import ConfigError, load_config
from lodestar.config.models import AppConfig

EXAMPLE = Path(__file__).parents[3] / "config.example"


@pytest.fixture
def cfg_dir(tmp_path: Path) -> Path:
    target = tmp_path / "config"
    shutil.copytree(EXAMPLE, target)
    return target


def edit(cfg_dir: Path, name: str, change: Callable[[dict], None]) -> None:  # type: ignore[type-arg]
    path = cfg_dir / name
    data = yaml.safe_load(path.read_text("utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), "utf-8")


def error_for(cfg_dir: Path) -> str:
    with pytest.raises(ConfigError) as exc:
        load_config(cfg_dir)
    return str(exc.value)


def test_example_config_loads() -> None:
    cfg = load_config(EXAMPLE)
    assert isinstance(cfg, AppConfig)
    assert cfg.settings.locale == "it"
    assert cfg.settings.currency == "EUR"
    assert set(cfg.settings.models.model_dump()) == {"parse", "chat", "vision", "embed"}
    assert all(not t.enabled for t in cfg.settings.backup.targets)
    assert cfg.default_account.name == "Banca Aurora"
    assert {b.id for b in cfg.buckets} == {"P1", "P2", "P3", "P4"}
    assert cfg.bucket("P3").expected_house_date is not None
    assert len({r.kind for r in cfg.rules}) == 12
    assert "## 5 Rules" in cfg.plan


def test_missing_directory_suggests_copying_the_example(tmp_path: Path) -> None:
    assert "cp -r config.example config" in error_for(tmp_path / "nope")


def test_missing_file_is_named(cfg_dir: Path) -> None:
    (cfg_dir / "buckets.yaml").unlink()
    assert "buckets.yaml" in error_for(cfg_dir)


def test_broken_yaml_is_named(cfg_dir: Path) -> None:
    (cfg_dir / "categories.yaml").write_text("categories: [unclosed", "utf-8")
    assert "categories.yaml" in error_for(cfg_dir)


def test_wrong_field_type_names_file_and_field(cfg_dir: Path) -> None:
    edit(cfg_dir, "accounts.yaml", lambda d: d["accounts"][1].update(type="piggy"))
    message = error_for(cfg_dir)
    assert "accounts.yaml" in message and "accounts[1].type" in message


def test_unknown_field_is_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "settings.yaml", lambda d: d.update(colour="blue"))
    message = error_for(cfg_dir)
    assert "settings.yaml" in message and "colour" in message


def test_two_default_accounts_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "accounts.yaml", lambda d: d["accounts"][1].update(is_default=True))
    message = error_for(cfg_dir)
    assert "accounts.yaml" in message and "default" in message


def test_unknown_bucket_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "accounts.yaml", lambda d: d["accounts"][2].update(bucket="P9"))
    message = error_for(cfg_dir)
    assert "accounts.yaml" in message and "accounts[2].bucket" in message and "P9" in message


def test_rule_citing_missing_plan_section_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "rules.yaml", lambda d: d["rules"][0].update(plan_section=["42.1"]))
    message = error_for(cfg_dir)
    assert "rules.yaml" in message and "rules[0].plan_section" in message and "42.1" in message


def test_rule_unknown_account_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "rules.yaml", lambda d: d["rules"][1].update(account="Banca Fantasma"))
    message = error_for(cfg_dir)
    assert "rules.yaml" in message and "Banca Fantasma" in message


def test_unknown_rule_kind_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "rules.yaml", lambda d: d["rules"][0].update(kind="moon_phase"))
    assert "rules.yaml" in error_for(cfg_dir)


def test_policy_unknown_bucket_rejected(cfg_dir: Path) -> None:
    edit(cfg_dir, "instrument_policy.yaml", lambda d: d["buckets"].update(P7={"allowed": []}))
    message = error_for(cfg_dir)
    assert "instrument_policy.yaml" in message and "P7" in message


def test_no_pension_fund_in_example() -> None:
    for path in EXAMPLE.iterdir():
        text = path.read_text(encoding="utf-8").lower()
        for word in ("pension", "fondo pensione", "previdenz"):
            assert word not in text, f"{path.name} mentions {word!r} (ADR 0017)"

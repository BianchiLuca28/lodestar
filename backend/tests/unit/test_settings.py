from pathlib import Path

import pytest

from lodestar.config.loader import load_config
from lodestar.config.settings import Settings

EXAMPLE = Path(__file__).parents[3] / "config.example"


def test_llm_url_comes_from_settings_yaml() -> None:
    settings = Settings.from_config(load_config(EXAMPLE), environ={})
    assert settings.llm_base_url == "http://127.0.0.1:11434"


def test_env_overrides_llm_url_and_strips_slash() -> None:
    environ = {"LODESTAR_LLM_BASE_URL": "http://host.docker.internal:11434/"}
    settings = Settings.from_config(load_config(EXAMPLE), environ=environ)
    assert settings.llm_base_url == "http://host.docker.internal:11434"


def test_config_dir_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LODESTAR_CONFIG_DIR", "/somewhere/else")
    assert Settings.config_dir() == Path("/somewhere/else")
    monkeypatch.delenv("LODESTAR_CONFIG_DIR")
    assert Settings.config_dir() == Path("config")


def test_telegram_is_off_without_a_token() -> None:
    settings = Settings.from_config(load_config(EXAMPLE), environ={})
    assert not settings.telegram_enabled


def test_telegram_token_and_user_come_from_env() -> None:
    environ = {"LODESTAR_TELEGRAM_BOT_TOKEN": "123:abc", "LODESTAR_TELEGRAM_USER_ID": "42"}
    settings = Settings.from_config(load_config(EXAMPLE), environ=environ)
    assert settings.telegram_enabled
    assert (settings.telegram_bot_token, settings.telegram_user_id) == ("123:abc", 42)

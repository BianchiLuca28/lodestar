import pytest

from lodestar.config.settings import DEFAULT_LLM_BASE_URL, Settings


def test_llm_base_url_defaults_to_local_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LODESTAR_LLM_BASE_URL", raising=False)

    assert Settings.from_env().llm_base_url == DEFAULT_LLM_BASE_URL == "http://127.0.0.1:11434"


def test_llm_base_url_comes_from_env_without_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LODESTAR_LLM_BASE_URL", "http://host.docker.internal:11434/")

    assert Settings.from_env().llm_base_url == "http://host.docker.internal:11434"

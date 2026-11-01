from pathlib import Path

import pytest
from fastapi import FastAPI

from lodestar.config.loader import load_config
from lodestar.config.models import AppConfig
from lodestar.config.settings import Settings
from lodestar.main import create_app

EXAMPLE = Path(__file__).parents[2] / "config.example"
TEST_LLM_URL = "http://llm.test:11434"


@pytest.fixture
def example_config() -> AppConfig:
    return load_config(EXAMPLE)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings pointing at a fresh temporary data dir, so each test gets its own SQLite file."""
    return Settings(llm_base_url=TEST_LLM_URL, data_dir=tmp_path / "data")


@pytest.fixture
def app(example_config: AppConfig, settings: Settings) -> FastAPI:
    return create_app(example_config, settings)

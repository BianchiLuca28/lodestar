"""Runtime settings: config/settings.yaml plus environment overrides."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from lodestar.config.models import AppConfig

CONFIG_DIR_ENV = "LODESTAR_CONFIG_DIR"
DATA_DIR_ENV = "LODESTAR_DATA_DIR"
LLM_URL_ENV = "LODESTAR_LLM_BASE_URL"


@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    data_dir: Path = field(default=Path("data"))

    @classmethod
    def from_config(cls, config: AppConfig, environ: Mapping[str, str] = os.environ) -> "Settings":
        # Docker overrides the URL to reach Ollama on the host (host.docker.internal).
        base_url = environ.get(LLM_URL_ENV) or config.settings.llm.base_url
        return cls(
            llm_base_url=base_url.rstrip("/"),
            data_dir=Path(environ.get(DATA_DIR_ENV, "data")),
        )

    @staticmethod
    def config_dir() -> Path:
        return Path(os.environ.get(CONFIG_DIR_ENV, "config"))

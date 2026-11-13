"""Runtime settings: config/settings.yaml plus environment overrides."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from lodestar.config.models import AppConfig

CONFIG_DIR_ENV = "LODESTAR_CONFIG_DIR"
DATA_DIR_ENV = "LODESTAR_DATA_DIR"
LLM_URL_ENV = "LODESTAR_LLM_BASE_URL"
BOT_TOKEN_ENV = "LODESTAR_TELEGRAM_BOT_TOKEN"
BOT_USER_ENV = "LODESTAR_TELEGRAM_USER_ID"


@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    data_dir: Path = field(default=Path("data"))
    # Secrets come from the environment (.env), never from config files.
    telegram_bot_token: str | None = None
    telegram_user_id: int | None = None

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token) and self.telegram_user_id is not None

    @classmethod
    def from_config(cls, config: AppConfig, environ: Mapping[str, str] = os.environ) -> "Settings":
        # Docker overrides the URL to reach Ollama on the host (host.docker.internal).
        base_url = environ.get(LLM_URL_ENV) or config.settings.llm.base_url
        return cls(
            llm_base_url=base_url.rstrip("/"),
            data_dir=Path(environ.get(DATA_DIR_ENV, "data")),
            telegram_bot_token=environ.get(BOT_TOKEN_ENV) or None,
            telegram_user_id=int(user) if (user := environ.get(BOT_USER_ENV)) else None,
        )

    @staticmethod
    def config_dir() -> Path:
        return Path(os.environ.get(CONFIG_DIR_ENV, "config"))

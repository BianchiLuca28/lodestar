"""App factory. Run with: uvicorn --factory lodestar.main:create_app"""

from fastapi import FastAPI

from lodestar.api import config, health
from lodestar.config.loader import load_config
from lodestar.config.models import AppConfig
from lodestar.config.settings import Settings


def create_app(app_config: AppConfig | None = None, settings: Settings | None = None) -> FastAPI:
    # An invalid config raises ConfigError here, so the app never starts half-configured.
    app_config = app_config or load_config(Settings.config_dir())
    app = FastAPI(title="Lodestar")
    app.state.config = app_config
    app.state.settings = settings or Settings.from_config(app_config)
    app.include_router(health.router)
    app.include_router(config.router)
    return app

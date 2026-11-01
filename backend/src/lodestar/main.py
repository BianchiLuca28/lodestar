"""App factory. Run with: uvicorn --factory lodestar.main:create_app"""

from fastapi import FastAPI

from lodestar.adapters.db.engine import db_path, make_engine, migrate
from lodestar.api import balances, config, errors, health, transactions
from lodestar.config.loader import load_config
from lodestar.config.models import AppConfig
from lodestar.config.settings import Settings


def create_app(app_config: AppConfig | None = None, settings: Settings | None = None) -> FastAPI:
    # An invalid config raises ConfigError here, so the app never starts half-configured.
    app_config = app_config or load_config(Settings.config_dir())
    settings = settings or Settings.from_config(app_config)
    db = db_path(settings.data_dir)
    migrate(db)

    app = FastAPI(title="Lodestar")
    app.state.config = app_config
    app.state.settings = settings
    app.state.db_path = db
    app.state.engine = make_engine(db)
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(transactions.router)
    app.include_router(balances.router)
    errors.install(app)
    return app

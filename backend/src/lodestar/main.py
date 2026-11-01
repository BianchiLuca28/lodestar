"""App factory. Run with: uvicorn --factory lodestar.main:create_app"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from lodestar.adapters.backup_folder import backup_folder, backup_if_due
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

    folder = backup_folder(app_config, settings.data_dir)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # Catch-up instead of a fixed time: the PC may be on once a week. Runs at startup,
        # then hourly; a backup is made only when the newest one is over a day old.
        scheduler = BackgroundScheduler(timezone=UTC)
        if folder is not None:
            scheduler.add_job(
                lambda: backup_if_due(db, folder, datetime.now(UTC)),
                "interval",
                hours=1,
                next_run_time=datetime.now(UTC),
                id="backup",
            )
        scheduler.start()
        try:
            yield
        finally:
            scheduler.shutdown(wait=False)

    app = FastAPI(title="Lodestar", lifespan=lifespan)
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

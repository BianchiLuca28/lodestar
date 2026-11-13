"""App factory. Run with: uvicorn --factory lodestar.main:create_app"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from lodestar.adapters.backup_folder import backup_folder, backup_if_due
from lodestar.adapters.db.drafts_repo import DraftRepository
from lodestar.adapters.db.engine import db_path, make_engine, migrate
from lodestar.adapters.db.examples_index import ExampleIndex
from lodestar.adapters.db.inbound_repo import InboundRepository
from lodestar.adapters.embeddings import Embedder, OpenAICompatEmbedder
from lodestar.adapters.llm import chat_model
from lodestar.adapters.telegram import HttpTelegramClient
from lodestar.ai.graphs.parse_message import ParseContext
from lodestar.api import balances, config, drafts, errors, health, transactions
from lodestar.config.loader import load_config
from lodestar.config.models import AppConfig
from lodestar.config.settings import Settings
from lodestar.jobs.parse_inbound import parse_pending, safe_sync
from lodestar.jobs.telegram_poll import safe_poll


def create_app(
    app_config: AppConfig | None = None,
    settings: Settings | None = None,
    embedder: Embedder | None = None,
) -> FastAPI:
    # An invalid config raises ConfigError here, so the app never starts half-configured.
    app_config = app_config or load_config(Settings.config_dir())
    settings = settings or Settings.from_config(app_config)
    db = db_path(settings.data_dir)
    migrate(db)

    folder = backup_folder(app_config, settings.data_dir)
    embed_model = app_config.settings.models.embed
    examples = ExampleIndex(
        db, embedder or OpenAICompatEmbedder(settings.llm_base_url, embed_model), embed_model
    )

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
        # Backfill the few-shot index from existing transactions; retried while Ollama is off.
        scheduler.add_job(
            lambda: safe_sync(app.state.examples),
            "interval",
            hours=1,
            next_run_time=datetime.now(UTC),
            max_instances=1,
            id="examples",
        )
        if settings.telegram_enabled:
            assert settings.telegram_bot_token and settings.telegram_user_id is not None
            client = HttpTelegramClient(settings.telegram_bot_token)
            inbound = InboundRepository(app.state.engine)
            user_id = settings.telegram_user_id
            parser = chat_model(settings.llm_base_url, app_config.settings.models.parse)
            ctx = ParseContext.from_config(app_config)
            drafts = DraftRepository(app.state.engine)

            def poll_and_parse(
                client: HttpTelegramClient, inbound: InboundRepository, user: int
            ) -> None:
                # One job, so parsing never races the poll; a down LLM leaves messages pending.
                safe_poll(client, inbound, user, datetime.now(UTC))
                safe_sync(app.state.examples)
                parse_pending(parser, ctx, inbound, drafts, app.state.examples.nearest)

            scheduler.add_job(
                lambda: poll_and_parse(client, inbound, user_id),
                "interval",
                seconds=30,
                next_run_time=datetime.now(UTC),
                max_instances=1,
                id="telegram",
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
    app.state.examples = examples
    app.state.engine = make_engine(db)
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(transactions.router)
    app.include_router(balances.router)
    app.include_router(drafts.router)
    errors.install(app)
    return app

from fastapi import FastAPI

from lodestar.api import health
from lodestar.config.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Lodestar")
    app.state.settings = settings or Settings.from_env()
    app.include_router(health.router)
    return app


app = create_app()

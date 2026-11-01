from fastapi import FastAPI

from lodestar.api import health


def create_app() -> FastAPI:
    app = FastAPI(title="Lodestar")
    app.include_router(health.router)
    return app


app = create_app()

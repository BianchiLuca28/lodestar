from importlib.metadata import version
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from lodestar.adapters.llm_probe import llm_reachable
from lodestar.config.settings import Settings

router = APIRouter(prefix="/api", tags=["health"])


class LlmStatus(BaseModel):
    reachable: bool
    base_url: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    llm: LlmStatus


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=version("lodestar"),
        llm=LlmStatus(
            reachable=await llm_reachable(settings.llm_base_url),
            base_url=settings.llm_base_url,
        ),
    )

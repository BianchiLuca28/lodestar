from importlib.metadata import version
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=version("lodestar"))

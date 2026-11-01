from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from lodestar.config.models import AppConfig

router = APIRouter(prefix="/api", tags=["config"])


class AccountOut(BaseModel):
    name: str
    type: Literal["cash", "bank", "broker", "postal"]
    bucket: str
    is_default: bool


class CategoryOut(BaseModel):
    name: str
    discretionary: bool
    subcategories: list[str]


class ConfigResponse(BaseModel):
    accounts: list[AccountOut]
    categories: list[CategoryOut]


def get_config(request: Request) -> AppConfig:
    config: AppConfig = request.app.state.config
    return config


@router.get("/config")
def read_config(config: Annotated[AppConfig, Depends(get_config)]) -> ConfigResponse:
    return ConfigResponse(
        accounts=[AccountOut.model_validate(a.model_dump()) for a in config.accounts],
        categories=[CategoryOut.model_validate(c.model_dump()) for c in config.categories],
    )

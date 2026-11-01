from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from lodestar.adapters.backup_folder import backup_folder, last_backup
from lodestar.adapters.db.engine import current_revision
from lodestar.adapters.llm_probe import llm_reachable
from lodestar.config.settings import Settings

router = APIRouter(prefix="/api", tags=["health"])


class LlmStatus(BaseModel):
    reachable: bool
    base_url: str


class DatabaseStatus(BaseModel):
    reachable: bool
    revision: str | None


class BackupStatus(BaseModel):
    enabled: bool
    last_backup: datetime | None
    folder: str | None  # as configured; relative paths live under the data dir


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    llm: LlmStatus
    database: DatabaseStatus
    backup: BackupStatus


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db_path(request: Request) -> Path:
    db: Path = request.app.state.db_path
    return db


def _database_status(db: Path) -> DatabaseStatus:
    try:
        return DatabaseStatus(reachable=True, revision=current_revision(db))
    except SQLAlchemyError:
        return DatabaseStatus(reachable=False, revision=None)


def _backup_status(request: Request, db: Path) -> BackupStatus:
    folder = backup_folder(request.app.state.config, db.parent)
    if folder is None:
        return BackupStatus(enabled=False, last_backup=None, folder=None)
    configured = next(
        t.path for t in request.app.state.config.settings.backup.targets if t.kind == "folder"
    )
    return BackupStatus(enabled=True, last_backup=last_backup(folder), folder=configured)


@router.get("/health")
async def health(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Path, Depends(get_db_path)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=version("lodestar"),
        llm=LlmStatus(
            reachable=await llm_reachable(settings.llm_base_url),
            base_url=settings.llm_base_url,
        ),
        database=_database_status(db),
        backup=_backup_status(request, db),
    )

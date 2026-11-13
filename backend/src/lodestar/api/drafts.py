"""Drafts API: list, create, edit (new version), approve, reject (design §6.1, §8 Inbox)."""

import datetime as dt
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from lodestar.adapters.db.drafts_repo import DraftRepository, StoredDraft
from lodestar.api.transactions import ERRORS, Cat, TransactionIn
from lodestar.domain.drafts import possible_duplicates
from lodestar.domain.ledger import Catalog, LineInput, validate_line

router = APIRouter(prefix="/api/drafts", tags=["drafts"], responses=ERRORS)

DraftStatus = Literal["pending", "approved", "rejected"]
DraftSource = Literal["telegram", "receipt", "bank_xlsx"]
Author = Literal["ai", "user"]


class DraftLine(TransactionIn):
    """A proposed line in responses; its own schema keeps `TransactionIn` input-only."""


class DraftLineOut(DraftLine):
    possible_duplicates: list[int]


class DraftVersionOut(BaseModel):
    version: int
    lines: list[DraftLine]
    author: Author
    created_at: dt.datetime


class DraftOut(BaseModel):
    id: int
    status: DraftStatus
    version: int
    source: DraftSource
    origin_text: str | None
    confidence: float | None
    created_at: dt.datetime
    decided_at: dt.datetime | None
    lines: list[DraftLineOut]


class DraftDetail(DraftOut):
    versions: list[DraftVersionOut]


class DraftIn(BaseModel):
    source: DraftSource
    origin_text: str | None = None
    lines: list[TransactionIn]


class DraftLinesIn(BaseModel):
    lines: list[TransactionIn]


def get_repo(request: Request) -> DraftRepository:
    return DraftRepository(request.app.state.engine)


Repo = Annotated[DraftRepository, Depends(get_repo)]


def _line_in(line: LineInput) -> DraftLine:
    return DraftLine.model_validate(line, from_attributes=True)


def _out(stored: StoredDraft, repo: DraftRepository) -> DraftOut:
    d = stored.draft
    assert d.id is not None
    pending = d.status == "pending"
    return DraftOut(
        id=d.id,
        status=cast(DraftStatus, d.status),
        version=d.version,
        source=cast(DraftSource, d.source),
        origin_text=d.origin_text,
        confidence=d.confidence,
        created_at=d.created_at,
        decided_at=d.decided_at,
        lines=[
            DraftLineOut(
                **_line_in(line).model_dump(),
                possible_duplicates=possible_duplicates(line, repo.near(line)) if pending else [],
            )
            for line in stored.lines
        ],
    )


def _detail(stored: StoredDraft, repo: DraftRepository) -> DraftDetail:
    return DraftDetail(
        **_out(stored, repo).model_dump(),
        versions=[
            DraftVersionOut(
                version=v.version,
                lines=[_line_in(line) for line in v.lines],
                author=cast(Author, v.author),
                created_at=v.created_at,
            )
            for v in stored.versions
        ],
    )


def _validated(lines: list[TransactionIn], catalog: Catalog) -> list[LineInput]:
    result = [LineInput(**line.model_dump()) for line in lines]
    for line in result:
        validate_line(line, catalog)
    return result


@router.get("")
def list_drafts(repo: Repo, status: DraftStatus | None = None) -> list[DraftOut]:
    return [_out(d, repo) for d in repo.by_status(status)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_draft(data: DraftIn, repo: Repo, catalog: Cat) -> DraftDetail:
    lines = _validated(data.lines, catalog)
    return _detail(repo.create(lines, data.source, data.origin_text), repo)


@router.get("/{draft_id}")
def get_draft(draft_id: int, repo: Repo) -> DraftDetail:
    return _detail(repo.get(draft_id), repo)


@router.put("/{draft_id}/lines")
def edit_draft(draft_id: int, data: DraftLinesIn, repo: Repo, catalog: Cat) -> DraftDetail:
    lines = _validated(data.lines, catalog)
    return _detail(repo.add_version(draft_id, lines, author="user"), repo)


@router.post("/{draft_id}/approve")
def approve_draft(draft_id: int, repo: Repo) -> DraftDetail:
    return _detail(repo.approve(draft_id), repo)


@router.post("/{draft_id}/reject")
def reject_draft(draft_id: int, repo: Repo) -> DraftDetail:
    return _detail(repo.reject(draft_id), repo)

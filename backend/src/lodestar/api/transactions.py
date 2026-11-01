"""Ledger API: list, create, update, delete transactions (design §5, §8 Movimenti)."""

import datetime as dt
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel

from lodestar.adapters.db.tables import Transaction
from lodestar.adapters.db.transactions_repo import Filters, TransactionRepository
from lodestar.api.errors import ErrorResponse
from lodestar.config.catalog import catalog_of
from lodestar.config.models import AppConfig
from lodestar.domain.direction import Direction, direction_of
from lodestar.domain.ledger import Catalog, LineInput, validate_line
from lodestar.domain.money import from_cents

ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}
router = APIRouter(prefix="/api/transactions", tags=["transactions"], responses=ERRORS)


class TransactionIn(BaseModel):
    date: dt.date
    amount: Decimal
    from_account: str | None = None
    to_account: str | None = None
    category: str
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = None
    exclude_from_stats: bool = False


class TransactionPatch(BaseModel):
    date: dt.date | None = None
    amount: Decimal | None = None
    from_account: str | None = None
    to_account: str | None = None
    category: str | None = None
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = None
    exclude_from_stats: bool | None = None


class TransactionOut(TransactionIn):
    id: int
    direction: Direction
    source: str
    created_at: dt.datetime


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int


def get_repo(request: Request) -> TransactionRepository:
    return TransactionRepository(request.app.state.engine)


def get_catalog(request: Request) -> Catalog:
    config: AppConfig = request.app.state.config
    return catalog_of(config)


Repo = Annotated[TransactionRepository, Depends(get_repo)]
Cat = Annotated[Catalog, Depends(get_catalog)]


def to_out(row: Transaction) -> TransactionOut:
    assert row.id is not None
    return TransactionOut(
        id=row.id,
        date=row.date,
        amount=from_cents(row.amount_cents),
        from_account=row.from_account,
        to_account=row.to_account,
        category=row.category,
        subcategory=row.subcategory,
        note=row.note,
        tag=row.tag,
        exclude_from_stats=row.exclude_from_stats,
        direction=direction_of(row.from_account, row.to_account),
        source=row.source,
        created_at=row.created_at,
    )


def _line(data: TransactionIn) -> LineInput:
    return LineInput(**data.model_dump())


@router.get("")
def list_transactions(
    repo: Repo,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    account: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TransactionPage:
    filters = Filters(date_from, date_to, account, category, tag, q)
    rows, total = repo.list(filters, limit, offset)
    return TransactionPage(items=[to_out(r) for r in rows], total=total)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionIn, repo: Repo, catalog: Cat) -> TransactionOut:
    line = _line(data)
    validate_line(line, catalog)
    return to_out(repo.add(line, source="manual"))


@router.patch("/{transaction_id}")
def update_transaction(
    transaction_id: int, patch: TransactionPatch, repo: Repo, catalog: Cat
) -> TransactionOut:
    current = to_out(repo.get(transaction_id))
    merged = TransactionIn.model_validate(
        current.model_dump() | patch.model_dump(exclude_unset=True)
    )
    line = _line(merged)
    validate_line(line, catalog)
    return to_out(repo.update(transaction_id, line))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, repo: Repo) -> Response:
    repo.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

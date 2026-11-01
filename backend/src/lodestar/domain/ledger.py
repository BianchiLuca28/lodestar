"""Ledger lines: the shape of a transaction and its validation against the configured catalog."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from lodestar.domain.errors import FieldError, InvalidAmount
from lodestar.domain.money import to_cents


@dataclass(frozen=True)
class Catalog:
    """The accounts and categories a line may use, taken from config."""

    accounts: frozenset[str]
    categories: Mapping[str, frozenset[str]]  # category → allowed subcategories (empty: any)


@dataclass(frozen=True)
class LineInput:
    date: date
    amount: Decimal
    from_account: str | None
    to_account: str | None
    category: str
    subcategory: str | None
    note: str | None
    tag: str | None
    exclude_from_stats: bool


def validate_line(line: LineInput, catalog: Catalog) -> None:
    """Raise FieldError for the first invalid field, in form order."""
    try:
        if line.amount <= 0:
            raise InvalidAmount("amount must be positive")
        to_cents(line.amount)
    except InvalidAmount as exc:
        raise FieldError("error.invalidAmount", "amount", str(exc)) from exc

    if not line.from_account and not line.to_account:
        raise FieldError(
            "error.missingAccount", "from_account", "a source or destination is needed"
        )
    for field in ("from_account", "to_account"):
        account = getattr(line, field)
        if account and account not in catalog.accounts:
            raise FieldError("error.unknownAccount", field, f"unknown account {account!r}")
    if line.from_account and line.from_account == line.to_account:
        raise FieldError("error.sameAccount", "to_account", "source and destination are the same")

    if line.category not in catalog.categories:
        raise FieldError("error.unknownCategory", "category", f"unknown category {line.category!r}")
    allowed = catalog.categories[line.category]
    if line.subcategory and allowed and line.subcategory not in allowed:
        raise FieldError(
            "error.unknownSubcategory",
            "subcategory",
            f"{line.subcategory!r} is not a subcategory of {line.category!r}",
        )

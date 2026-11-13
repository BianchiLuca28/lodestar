"""Drafts: proposed lines waiting for the user's decision (design §5, §8; ADR 0007)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from lodestar.domain.errors import Conflict
from lodestar.domain.ledger import LineInput

STATUSES = ("pending", "approved", "rejected")
DUPLICATE_WINDOW = timedelta(days=2)


@dataclass(frozen=True)
class Existing:
    """A ledger line a draft line may duplicate."""

    id: int
    date: date
    amount: Decimal
    from_account: str | None
    to_account: str | None


def possible_duplicates(line: LineInput, candidates: Iterable[Existing]) -> list[int]:
    """Ids of ledger lines with the same amount, a shared account and a date within ±2 days."""
    accounts = {line.from_account, line.to_account} - {None}
    return [
        c.id
        for c in candidates
        if c.amount == line.amount
        and abs(c.date - line.date) <= DUPLICATE_WINDOW
        and accounts & ({c.from_account, c.to_account} - {None})
    ]


def ensure_pending(status: str) -> None:
    if status != "pending":
        raise Conflict("error.draftNotPending", f"the draft is already {status}")

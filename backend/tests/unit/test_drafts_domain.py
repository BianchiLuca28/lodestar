from datetime import date
from decimal import Decimal

import pytest

from lodestar.domain.drafts import Existing, ensure_pending, possible_duplicates
from lodestar.domain.errors import Conflict
from lodestar.domain.ledger import LineInput


def line(
    d: date, amount: str, src: str | None = "Banca Aurora", dst: str | None = None
) -> LineInput:
    return LineInput(d, Decimal(amount), src, dst, "🥦 Spesa", None, None, None, False)


DAY = date(2026, 3, 14)


def existing(
    id_: int, d: date, amount: str, src: str | None = "Banca Aurora", dst: str | None = None
) -> Existing:
    return Existing(id_, d, Decimal(amount), src, dst)


def test_same_account_amount_within_two_days_is_a_possible_duplicate() -> None:
    candidates = [existing(1, date(2026, 3, 12), "12.50"), existing(2, date(2026, 3, 16), "12.50")]
    assert possible_duplicates(line(DAY, "12.50"), candidates) == [1, 2]


def test_three_days_apart_is_not_a_duplicate() -> None:
    assert possible_duplicates(line(DAY, "12.50"), [existing(1, date(2026, 3, 11), "12.50")]) == []


def test_different_amount_or_account_is_not_a_duplicate() -> None:
    candidates = [existing(1, DAY, "12.51"), existing(2, DAY, "12.50", src="Contanti")]
    assert possible_duplicates(line(DAY, "12.50"), candidates) == []


def test_shared_destination_account_matches() -> None:
    candidates = [existing(3, DAY, "100.00", src="Contanti", dst="Broker Orsa")]
    assert possible_duplicates(line(DAY, "100.00", "Banca Aurora", "Broker Orsa"), candidates) == [
        3
    ]


def test_only_pending_drafts_can_change() -> None:
    ensure_pending("pending")
    for status in ("approved", "rejected"):
        with pytest.raises(Conflict):
            ensure_pending(status)

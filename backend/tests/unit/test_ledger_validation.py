from datetime import date
from decimal import Decimal

import pytest

from lodestar.domain.errors import FieldError
from lodestar.domain.ledger import Catalog, LineInput, validate_line

CATALOG = Catalog(
    accounts=frozenset({"Banca Aurora", "Contanti", "Broker Orsa"}),
    categories={
        "🍝 Ristoranti": frozenset({"Pizzeria", "Trattoria"}),
        "❓ Varie": frozenset(),
    },
)


def line(**kw: object) -> LineInput:
    base: dict[str, object] = {
        "date": date(2026, 3, 14),
        "amount": Decimal("12.50"),
        "from_account": "Banca Aurora",
        "to_account": None,
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": None,
        "tag": None,
        "exclude_from_stats": False,
    }
    return LineInput(**(base | kw))  # type: ignore[arg-type]


def error(candidate: LineInput) -> FieldError:
    with pytest.raises(FieldError) as exc:
        validate_line(candidate, CATALOG)
    return exc.value


def test_valid_line_passes() -> None:
    validate_line(line(), CATALOG)


def test_unknown_account() -> None:
    err = error(line(from_account="Banca Fantasma"))
    assert (err.key, err.field) == ("error.unknownAccount", "from_account")


def test_unknown_destination_account() -> None:
    err = error(line(from_account=None, to_account="Nowhere"))
    assert (err.key, err.field) == ("error.unknownAccount", "to_account")


def test_unknown_category() -> None:
    err = error(line(category="🛸 Ufo"))
    assert (err.key, err.field) == ("error.unknownCategory", "category")


def test_subcategory_must_belong_to_category() -> None:
    err = error(line(subcategory="Cinema"))
    assert (err.key, err.field) == ("error.unknownSubcategory", "subcategory")


def test_any_subcategory_when_category_lists_none() -> None:
    validate_line(line(category="❓ Varie", subcategory="Qualsiasi"), CATALOG)


@pytest.mark.parametrize("amount", ["0", "-3.00", "1.005"])
def test_invalid_amount(amount: str) -> None:
    err = error(line(amount=Decimal(amount)))
    assert (err.key, err.field) == ("error.invalidAmount", "amount")


def test_no_account() -> None:
    err = error(line(from_account=None, to_account=None))
    assert (err.key, err.field) == ("error.missingAccount", "from_account")


def test_same_account_both_sides() -> None:
    err = error(line(to_account="Banca Aurora"))
    assert (err.key, err.field) == ("error.sameAccount", "to_account")

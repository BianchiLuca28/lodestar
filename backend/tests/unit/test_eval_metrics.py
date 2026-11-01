from datetime import date
from decimal import Decimal

import pytest

from lodestar.ai.evals.metrics import FIELDS, score
from lodestar.ai.evals.schema import Line


def line(**kw: object) -> Line:
    base: dict[str, object] = {
        "date": date(2026, 3, 14),
        "amount": Decimal("12.50"),
        "from_account": "Banca Aurora",
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": "Pizza",
    }
    return Line.model_validate(base | kw)


def test_perfect_match_scores_one_everywhere() -> None:
    result = score([([line()], [line()])])
    assert result["line_count_accuracy"] == 1.0
    assert all(result[f"field.{f}"] == 1.0 for f in FIELDS)


def test_amount_compared_as_decimal() -> None:
    result = score([([line(amount=Decimal("12.5"))], [line(amount="12.50")])])
    assert result["amount_accuracy"] == 1.0


def test_wrong_category_is_a_partial_match() -> None:
    result = score([([line()], [line(category="🎬 Svago")]), ([line()], [line()])])
    assert result["category_accuracy"] == 0.5
    assert result["amount_accuracy"] == 1.0
    assert result["line_count_accuracy"] == 1.0


def test_missing_line_counts_as_misses() -> None:
    expected = [line(), line(amount=Decimal("7.00"))]
    result = score([(expected, [line()])])
    assert result["line_count_accuracy"] == 0.0
    assert result["amount_accuracy"] == 0.5


def test_extra_line_counts_as_misses() -> None:
    result = score([([line()], [line(), line()])])
    assert result["line_count_accuracy"] == 0.0
    assert result["category_accuracy"] == 0.5


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        score([])

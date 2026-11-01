from decimal import Decimal

import pytest

from lodestar.domain.errors import InvalidAmount
from lodestar.domain.money import from_cents, to_cents


@pytest.mark.parametrize(
    ("amount", "cents"),
    [("12.50", 1250), ("12.5", 1250), ("0.01", 1), ("1234.56", 123456), ("7", 700)],
)
def test_to_cents(amount: str, cents: int) -> None:
    assert to_cents(Decimal(amount)) == cents


def test_from_cents_has_two_places() -> None:
    value = from_cents(1250)
    assert value == Decimal("12.50")
    assert value.as_tuple().exponent == -2


def test_round_trip() -> None:
    for cents in (1, 99, 100, 123456789):
        assert to_cents(from_cents(cents)) == cents


def test_more_than_two_places_rejected() -> None:
    with pytest.raises(InvalidAmount):
        to_cents(Decimal("1.005"))

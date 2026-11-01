"""Money is exact: Decimal with 2 places in EUR, stored as integer cents (invariant 6)."""

from decimal import ROUND_HALF_EVEN, Decimal

from lodestar.domain.errors import InvalidAmount

CENT = Decimal("0.01")


def quantize(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_EVEN)


def to_cents(amount: Decimal) -> int:
    """Convert an amount with at most 2 decimal places to integer cents."""
    if quantize(amount) != amount:
        raise InvalidAmount(f"{amount} has more than 2 decimal places")
    return int(amount * 100)


def from_cents(cents: int) -> Decimal:
    return quantize(Decimal(cents) / 100)

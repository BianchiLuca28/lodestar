"""Account balances and the adjustment that closes a balance-check gap (CONTEXT.md)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from lodestar.domain.ledger import LineInput
from lodestar.domain.money import quantize

ADJUSTMENT_NOTE = "Riallineamento saldo"


@dataclass(frozen=True)
class AccountTotals:
    """Money that entered and left one account up to a date, excluded lines included."""

    money_in: Decimal
    money_out: Decimal


def balance_of(totals: AccountTotals) -> Decimal:
    return quantize(totals.money_in - totals.money_out)


def gap_between(real: Decimal, computed: Decimal) -> Decimal:
    """Positive when the account holds more than the ledger says."""
    return quantize(real - computed)


def adjustment_for(account: str, on: date, gap: Decimal, category: str) -> LineInput | None:
    """The line that makes the ledger match the real balance; None when they already match."""
    if gap == 0:
        return None
    return LineInput(
        date=on,
        amount=abs(gap),
        from_account=account if gap < 0 else None,
        to_account=account if gap > 0 else None,
        category=category,
        subcategory=None,
        note=ADJUSTMENT_NOTE,
        tag=None,
        exclude_from_stats=True,
    )

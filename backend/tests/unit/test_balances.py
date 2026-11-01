from datetime import date
from decimal import Decimal

from lodestar.domain.balances import AccountTotals, adjustment_for, balance_of, gap_between
from lodestar.domain.direction import Direction, direction_of


def test_balance_is_money_in_minus_money_out() -> None:
    assert balance_of(AccountTotals(Decimal("2150.00"), Decimal("92.50"))) == Decimal("2057.50")


def test_balance_can_be_negative() -> None:
    assert balance_of(AccountTotals(Decimal("0.00"), Decimal("5.00"))) == Decimal("-5.00")


def test_gap_is_real_minus_computed() -> None:
    assert gap_between(real=Decimal("1000.00"), computed=Decimal("980.50")) == Decimal("19.50")
    assert gap_between(real=Decimal("900.00"), computed=Decimal("980.50")) == Decimal("-80.50")


def test_positive_gap_becomes_an_income_into_the_account() -> None:
    line = adjustment_for("Banca Aurora", date(2026, 3, 1), Decimal("19.50"), "❓ Varie")
    assert line is not None
    assert direction_of(line.from_account, line.to_account) is Direction.INCOME
    assert line.to_account == "Banca Aurora"
    assert line.amount == Decimal("19.50")
    assert line.exclude_from_stats is True
    assert line.category == "❓ Varie"
    assert line.date == date(2026, 3, 1)


def test_negative_gap_becomes_an_expense_from_the_account() -> None:
    line = adjustment_for("Contanti", date(2026, 3, 1), Decimal("-80.50"), "❓ Varie")
    assert line is not None
    assert line.from_account == "Contanti" and line.to_account is None
    assert line.amount == Decimal("80.50")


def test_zero_gap_needs_no_adjustment() -> None:
    assert adjustment_for("Contanti", date(2026, 3, 1), Decimal("0.00"), "❓ Varie") is None

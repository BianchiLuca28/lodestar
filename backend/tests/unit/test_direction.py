import pytest

from lodestar.domain.direction import Direction, direction_of
from lodestar.domain.errors import InvalidTransaction


def test_only_source_is_expense() -> None:
    assert direction_of("Banca Aurora", None) is Direction.EXPENSE


def test_only_destination_is_income() -> None:
    assert direction_of(None, "Banca Aurora") is Direction.INCOME


def test_both_is_transfer() -> None:
    assert direction_of("Banca Aurora", "Broker Orsa") is Direction.TRANSFER


def test_empty_strings_count_as_missing() -> None:
    assert direction_of("", "Banca Aurora") is Direction.INCOME


def test_no_account_rejected() -> None:
    with pytest.raises(InvalidTransaction):
        direction_of(None, None)


def test_same_account_both_sides_rejected() -> None:
    with pytest.raises(InvalidTransaction):
        direction_of("Contanti", "Contanti")

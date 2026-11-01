"""Direction is derived from the accounts, never stored (CONTEXT.md → Direction, ADR 0002)."""

from enum import StrEnum

from lodestar.domain.errors import InvalidTransaction


class Direction(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


def direction_of(from_account: str | None, to_account: str | None) -> Direction:
    if from_account and to_account:
        if from_account == to_account:
            raise InvalidTransaction("a transfer needs two different accounts")
        return Direction.TRANSFER
    if from_account:
        return Direction.EXPENSE
    if to_account:
        return Direction.INCOME
    raise InvalidTransaction("a transaction needs a source or a destination account")

"""Protocols the domain needs from the outside; adapters implement them."""

from datetime import date
from typing import Protocol

from lodestar.domain.balances import AccountTotals


class LedgerTotals(Protocol):
    def totals(self, account: str, until: date) -> AccountTotals:
        """Money in and out of `account` on every date up to and including `until`."""
        ...

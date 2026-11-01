"""Instruments and trades as the initial import produces them, and how trades meet the ledger."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from lodestar.domain.ledger import LineInput

BOND_UNIT = Decimal(100)  # the spreadsheet counts bonds in units of 100 nominal


@dataclass(frozen=True)
class InstrumentInput:
    ticker: str
    isin: str
    name: str
    asset_class: str  # equity_etf · money_market_etf · govt_bond
    tax_rate: Decimal
    bucket: str


@dataclass(frozen=True)
class TradeInput:
    date: date
    ticker: str
    side: str  # buy · sell
    quantity: Decimal  # bonds: nominal; ETFs: units
    price: Decimal  # bonds: % of nominal; ETFs: € per unit
    fees: Decimal
    account: str


def link_trades(trades: Sequence[TradeInput], lines: Sequence[LineInput]) -> list[int | None]:
    """For each trade, the index of the ledger line that already holds its cash, or None.

    The spreadsheet records a purchase as one line leaving the broker account on the trade's day,
    often one line for several trades. So a buy links to the largest line out of the trade's
    account that day, a sell to the largest line into it. Imported trades never create new
    cash lines: the money is already in the ledger.
    """
    links: list[int | None] = []
    for trade in trades:
        side = "from_account" if trade.side == "buy" else "to_account"
        candidates = [
            i
            for i, line in enumerate(lines)
            if line.date == trade.date and getattr(line, side) == trade.account
        ]
        links.append(max(candidates, key=lambda i: lines[i].amount, default=None))
    return links

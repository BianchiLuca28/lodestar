"""Writes an initial import in one database transaction: all of it, or nothing."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Engine
from sqlmodel import Session

from lodestar.adapters.db.tables import Instrument, Trade
from lodestar.adapters.db.transactions_repo import new_row
from lodestar.domain.ledger import LineInput
from lodestar.domain.money import to_cents
from lodestar.domain.portfolio import InstrumentInput, TradeInput


@dataclass(frozen=True)
class Written:
    lines: int
    instruments: int
    trades: int


def write_import(
    engine: Engine,
    lines: Sequence[LineInput],
    created_at: Sequence[datetime | None],
    adjustments: Sequence[LineInput],
    instruments: Sequence[InstrumentInput],
    trades: Sequence[TradeInput],
    links: Sequence[int | None],
) -> Written:
    """`links[i]` is the index in `lines` of the cash line trade i belongs to, if any."""
    with Session(engine) as session:
        rows = [new_row(line, "import") for line in lines]
        for row, stamp in zip(rows, created_at, strict=False):
            if stamp is not None:
                row.created_at = stamp
        session.add_all(rows)
        session.add_all([new_row(line, "adjustment") for line in adjustments])
        by_ticker = {
            i.ticker: Instrument(
                ticker=i.ticker,
                isin=i.isin,
                name=i.name,
                asset_class=i.asset_class,
                tax_rate=str(i.tax_rate),
                bucket=i.bucket,
            )
            for i in instruments
        }
        session.add_all(by_ticker.values())
        session.flush()  # assigns ids for the trade foreign keys
        ids = {ticker: row.id for ticker, row in by_ticker.items() if row.id is not None}
        session.add_all(
            [
                Trade(
                    date=t.date,
                    instrument_id=ids[t.ticker],
                    side=t.side,
                    quantity=str(t.quantity),
                    price=str(t.price),
                    fees_cents=to_cents(t.fees),
                    account=t.account,
                    transaction_id=None if link is None else rows[link].id,
                )
                for t, link in zip(trades, links, strict=True)
            ]
        )
        session.commit()
    return Written(len(lines) + len(adjustments), len(instruments), len(trades))

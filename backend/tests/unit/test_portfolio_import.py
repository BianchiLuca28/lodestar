from datetime import date
from decimal import Decimal

from lodestar.domain.ledger import LineInput
from lodestar.domain.portfolio import TradeInput, link_trades


def line(d: date, amount: str, src: str | None, dst: str | None) -> LineInput:
    return LineInput(d, Decimal(amount), src, dst, "📊 Investimenti", None, None, None, True)


def trade(d: date, side: str = "buy") -> TradeInput:
    return TradeInput(d, "XEON", side, Decimal("10"), Decimal("140"), Decimal("0"), "Broker Orsa")


DAY = date(2026, 7, 29)


def test_trade_links_to_the_broker_line_of_its_day() -> None:
    lines = [
        line(DAY, "20.00", "Banca Aurora", None),
        line(DAY, "1400.00", "Broker Orsa", None),
        line(date(2026, 7, 30), "900.00", "Broker Orsa", None),
    ]
    assert link_trades([trade(DAY)], lines) == [1]


def test_several_trades_share_one_aggregated_line() -> None:
    lines = [line(DAY, "5.00", "Broker Orsa", None), line(DAY, "3000.00", "Broker Orsa", None)]
    assert link_trades([trade(DAY), trade(DAY)], lines) == [1, 1]


def test_a_sell_links_to_money_coming_into_the_broker() -> None:
    lines = [line(DAY, "1400.00", "Broker Orsa", None), line(DAY, "1500.00", None, "Broker Orsa")]
    assert link_trades([trade(DAY, "sell")], lines) == [1]


def test_no_matching_line_leaves_the_trade_unlinked() -> None:
    assert link_trades([trade(DAY)], [line(DAY, "10.00", "Banca Aurora", None)]) == [None]

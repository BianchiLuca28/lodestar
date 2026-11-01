from datetime import date
from decimal import Decimal

from lodestar.domain.import_report import format_report, summarize
from lodestar.domain.ledger import LineInput


def line(d: int, amount: str, src: str | None, dst: str | None, cat: str) -> LineInput:
    return LineInput(
        date=date(2026, 1, d),
        amount=Decimal(amount),
        from_account=src,
        to_account=dst,
        category=cat,
        subcategory=None,
        note=None,
        tag=None,
        exclude_from_stats=False,
    )


ROWS = [
    line(5, "2150.00", None, "Banca Aurora", "💰 Stipendio"),
    line(2, "12.50", "Banca Aurora", None, "🍝 Ristoranti"),
    line(9, "80.00", "Banca Aurora", "Contanti", "❓ Varie"),
    line(7, "7.50", "Contanti", None, "🍝 Ristoranti"),
]


def test_summary_counts_dates_and_totals() -> None:
    s = summarize(ROWS)
    assert s.count == 4
    assert (s.first_date, s.last_date) == (date(2026, 1, 2), date(2026, 1, 9))
    assert s.by_account["Banca Aurora"] == (Decimal("2150.00"), Decimal("92.50"))
    assert s.by_account["Contanti"] == (Decimal("80.00"), Decimal("7.50"))
    assert s.by_category["🍝 Ristoranti"] == Decimal("20.00")


def test_report_mentions_totals_and_errors() -> None:
    text = format_report(summarize(ROWS), ["riga 7 · amount: not a number"])
    assert "4" in text and "2026-01-02" in text and "2026-01-09" in text
    assert "Banca Aurora" in text and "2150.00" in text
    assert "riga 7 · amount: not a number" in text


def test_empty_summary() -> None:
    s = summarize([])
    assert s.count == 0 and s.first_date is None
    assert "0" in format_report(s, [])

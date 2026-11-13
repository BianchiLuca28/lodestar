from datetime import date
from decimal import Decimal

from lodestar.adapters.db.examples_index import Example
from lodestar.ai.evals.misses import misses_report
from lodestar.ai.evals.schema import Case, Line


def line(category: str, sub: str | None, note: str = "Conad") -> Line:
    return Line(
        date=date(2026, 11, 5),
        amount=Decimal("12.50"),
        from_account="Banca Aurora",
        category=category,
        subcategory=sub,
        note=note,
    )


def case(id_: str, message: str, expected: Line) -> Case:
    return Case(id=id_, message=message, sent_at="2026-11-05T19:00:00+01:00", expected=[expected])


def test_report_lists_only_wrong_cases_with_what_the_model_saw() -> None:
    right = case("ok", "coop 12,50", line("🥦 Spesa", "Supermercato"))
    wrong = case("ko", "gelato 3", line("🍝 Ristoranti", "Gelateria"))
    examples = {"ko": [Example("Gelato Grom", "🍝 Ristoranti", "Gelateria", "Banca Aurora", None)]}
    report = misses_report(
        [right, wrong],
        [[line("🥦 Spesa", "Supermercato")], [line("🥦 Spesa", None)]],
        examples,
    )
    assert "coop 12,50" not in report
    assert "gelato 3" in report
    assert "Gelato Grom" in report  # the few-shot example the model was given
    assert "1 of 2 cases" in report


def test_summary_counts_category_confusions_by_name_only() -> None:
    cases = [
        case("a", "gelato 3", line("🍝 Ristoranti", "Gelateria", note="SECRET-A")),
        case("b", "gelato 4", line("🍝 Ristoranti", "Gelateria", note="SECRET-B")),
        case("c", "regalo 30", line("🎁 Regali", None, note="SECRET-C")),
    ]
    predicted = [
        [line("🥦 Spesa", None)],
        [line("🥦 Spesa", None)],
        [line("🎁 Regali", "Natale")],
    ]
    report = misses_report(cases, predicted, {})
    summary = report.split("## Cases")[0]
    assert "| 🍝 Ristoranti | 🥦 Spesa | 2 |" in summary
    assert "| 🎁 Regali / – | 🎁 Regali / Natale | 1 |" in summary
    assert "SECRET" not in summary and "gelato" not in summary  # safe to share


def test_missing_and_extra_lines_are_reported() -> None:
    split = Case(
        id="s",
        message="cena 40, Marta mi ha ridato 20",
        sent_at="2026-11-05T19:00:00+01:00",
        expected=[line("🍝 Ristoranti", None), line("🍝 Ristoranti", None)],
    )
    report = misses_report([split], [[line("🍝 Ristoranti", None)]], {})
    assert "(missing)" in report

"""The dry-run report of an initial import: counts, date range and totals, computed in code."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from lodestar.domain.ledger import LineInput

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ImportSummary:
    count: int
    first_date: date | None
    last_date: date | None
    by_account: dict[str, tuple[Decimal, Decimal]] = field(default_factory=dict)  # (in, out)
    by_category: dict[str, Decimal] = field(default_factory=dict)


def summarize(rows: Sequence[LineInput]) -> ImportSummary:
    money_in: dict[str, Decimal] = defaultdict(lambda: ZERO)
    money_out: dict[str, Decimal] = defaultdict(lambda: ZERO)
    by_category: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for r in rows:
        if r.to_account:
            money_in[r.to_account] += r.amount
        if r.from_account:
            money_out[r.from_account] += r.amount
        by_category[r.category] += r.amount
    accounts = sorted(set(money_in) | set(money_out))
    dates = [r.date for r in rows]
    return ImportSummary(
        count=len(rows),
        first_date=min(dates, default=None),
        last_date=max(dates, default=None),
        by_account={a: (money_in[a], money_out[a]) for a in accounts},
        by_category=dict(sorted(by_category.items())),
    )


def format_report(summary: ImportSummary, errors: Sequence[str]) -> str:
    lines = [
        f"Righe valide: {summary.count}",
        f"Periodo: {summary.first_date or '-'} → {summary.last_date or '-'}",
        "",
        "Conto | Entrate | Uscite",
    ]
    lines += [f"{a} | {i:.2f} | {o:.2f}" for a, (i, o) in summary.by_account.items()]
    lines += ["", "Categoria | Totale"]
    lines += [f"{c} | {t:.2f}" for c, t in summary.by_category.items()]
    if errors:
        lines += ["", f"Righe non valide: {len(errors)}", *errors]
    return "\n".join(lines)

"""A readable report of the cases the parser got wrong (design §6.5).

Private runs write it to the git-ignored `evals/results/private/` (invariant 5). The summary at the
top holds only category and subcategory names, so it can be shared; the cases below it hold
messages, amounts and notes, and stay on the user's PC.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from itertools import zip_longest

from lodestar.adapters.db.examples_index import Example
from lodestar.ai.evals.metrics import note_matches
from lodestar.ai.evals.schema import Case, Line

COMPARED = ("date", "amount", "from_account", "to_account", "category", "subcategory", "tag")


def _wrong(expected: Line | None, predicted: Line | None) -> bool:
    if expected is None or predicted is None:
        return True
    if any(getattr(expected, f) != getattr(predicted, f) for f in COMPARED):
        return True
    return not note_matches(expected.note, predicted.note)


def _cat(line: Line, with_sub: bool = False) -> str:
    return f"{line.category} / {line.subcategory or '–'}" if with_sub else line.category


def _show(line: Line | None) -> str:
    if line is None:
        return "(missing)"
    accounts = f"{line.from_account or '–'} → {line.to_account or '–'}"
    tag = f" · #{line.tag}" if line.tag else ""
    return (
        f"{line.date} · {line.amount} · {accounts} · {_cat(line, with_sub=True)}"
        f" · {line.note or '–'}{tag}"
    )


def _table(title: str, counts: Counter[tuple[str, str]]) -> list[str]:
    rows = [f"### {title}", ""]
    if not counts:
        return [*rows, "None.", ""]
    rows += ["| Expected | Predicted | Cases |", "| --- | --- | --- |"]
    rows += [f"| {exp} | {pred} | {n} |" for (exp, pred), n in counts.most_common()]
    return [*rows, ""]


def misses_report(
    cases: Sequence[Case],
    predictions: Sequence[Sequence[Line]],
    examples: Mapping[str, Sequence[Example]],
) -> str:
    categories: Counter[tuple[str, str]] = Counter()
    subcategories: Counter[tuple[str, str]] = Counter()
    body: list[str] = []
    wrong_cases = 0
    for case, predicted in zip(cases, predictions, strict=True):
        pairs = list(zip_longest(case.expected, predicted))
        if not any(_wrong(e, p) for e, p in pairs):
            continue
        wrong_cases += 1
        for exp, pred in pairs:
            if exp is None or pred is None:
                continue
            if exp.category != pred.category:
                categories[(_cat(exp), _cat(pred))] += 1
            elif exp.subcategory != pred.subcategory:
                subcategories[(_cat(exp, True), _cat(pred, True))] += 1
        body += [f"### {case.id}", "", f"> {case.message}", ""]
        for number, (exp, pred) in enumerate(pairs, start=1):
            marker = "✗" if _wrong(exp, pred) else "✓"
            body += [
                f"- line {number} {marker}",
                f"  - expected:  {_show(exp)}",
                f"  - predicted: {_show(pred)}",
            ]
        seen = examples.get(case.id, [])
        if seen:
            body.append("- examples given to the model:")
            body += [
                f"  - “{e.note}” → {e.category} / {e.subcategory or '–'}"
                f" ({e.from_account or '–'} → {e.to_account or '–'})"
                for e in seen
            ]
        body.append("")
    head = [
        "# Parsing misses",
        "",
        f"{wrong_cases} of {len(cases)} cases have at least one wrong field.",
        "",
        "## Summary (category names only, safe to share)",
        "",
        *_table("Wrong category", categories),
        *_table("Right category, wrong subcategory", subcategories),
        "## Cases (private: messages, amounts and notes)",
        "",
    ]
    return "\n".join(head + body)

"""Parsing eval metrics, computed in code (design §6.5).

Lines are compared position by position. A case with too few or too many lines
scores the missing or extra positions as misses on every field.
"""

from collections.abc import Sequence

from lodestar.ai.evals.schema import Line

FIELDS = (
    "date",
    "amount",
    "from_account",
    "to_account",
    "category",
    "subcategory",
    "note",
    "tag",
)

Pair = tuple[Sequence[Line], Sequence[Line]]  # (expected, predicted)


def score(pairs: Sequence[Pair]) -> dict[str, float]:
    if not pairs:
        raise ValueError("no cases to score")
    hits = dict.fromkeys(FIELDS, 0)
    slots = 0
    count_ok = 0
    for expected, predicted in pairs:
        count_ok += len(expected) == len(predicted)
        slots += max(len(expected), len(predicted))
        for exp, pred in zip(expected, predicted, strict=False):
            for field in FIELDS:
                # Decimal equality ignores trailing zeros: 12.5 == 12.50.
                hits[field] += getattr(exp, field) == getattr(pred, field)
    result = {"line_count_accuracy": count_ok / len(pairs)}
    result |= {f"field.{f}": (hits[f] / slots if slots else 1.0) for f in FIELDS}
    result["category_accuracy"] = result["field.category"]
    result["amount_accuracy"] = result["field.amount"]
    return result

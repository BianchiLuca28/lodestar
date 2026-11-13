"""Parsing eval metrics, computed in code (design §6.5).

Lines are compared position by position. A case with too few or too many lines
scores the missing or extra positions as misses on every field.
"""

import re
import unicodedata
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


def _words(text: str | None) -> set[str]:
    plain = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return set(re.findall(r"[a-z0-9]+", plain.lower()))


def note_matches(expected: str | None, predicted: str | None) -> bool:
    """Loose note match: same words ignoring case and accents, or one inside the other."""
    exp, pred = _words(expected), _words(predicted)
    if not exp or not pred:
        return exp == pred
    return exp <= pred or pred <= exp


def score(pairs: Sequence[Pair]) -> dict[str, float]:
    if not pairs:
        raise ValueError("no cases to score")
    hits = dict.fromkeys(FIELDS, 0)
    loose = 0
    slots = 0
    count_ok = 0
    for expected, predicted in pairs:
        count_ok += len(expected) == len(predicted)
        slots += max(len(expected), len(predicted))
        for exp, pred in zip(expected, predicted, strict=False):
            for field in FIELDS:
                # Decimal equality ignores trailing zeros: 12.5 == 12.50.
                hits[field] += getattr(exp, field) == getattr(pred, field)
            loose += note_matches(exp.note, pred.note)
    result = {"line_count_accuracy": count_ok / len(pairs)}
    result |= {f"field.{f}": (hits[f] / slots if slots else 1.0) for f in FIELDS}
    result["category_accuracy"] = result["field.category"]
    result["amount_accuracy"] = result["field.amount"]
    # Addition to §6.5: free-text notes almost never match exactly.
    result["note_loose"] = loose / slots if slots else 1.0
    return result

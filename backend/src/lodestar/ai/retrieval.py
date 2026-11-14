"""What the few-shot search looks for: the words of a message, not its amount or date (§6.1).

Embedding "benzina 20,13" whole matches notes that are numbers ("32.99") or full of dates
("Stipendio … ricevuto il 30 aprile"). Searching with "benzina" finds past fuel rows.
"""

import re

_WEEKDAY = r"(?:luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)"
_MONTH = (
    r"(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre"
    r"|novembre|dicembre)"
)
_DATE_WORDS = [
    r"\b(?:\d+|un|uno|due|tre|quattro|cinque|sei) giorn[oi] fa\b",
    r"\bl['’]\s?altro\s?ieri\b|\baltroieri\b",
    r"\b(?:ieri|oggi|stamattina|stasera)(?: sera| mattina| pomeriggio)?\b",
    rf"\b{_WEEKDAY}(?: scors[oa])?\b",
    rf"\b(?:il |l['’]|del |dell['’])?\d{{1,2}}°? {_MONTH}(?: \d{{4}})?\b",
    r"\b(?:il |l['’]|del |dell['’])?\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?\b",
    r"\b(?:il |l['’]|del |dell['’])\d{1,2}°?(?=\s|$)",
    rf"\b{_MONTH}\b",
]
_CURRENCY = r"€|\beuro\b|\beur\b"
_DECIMAL = r"\b\d{1,3}(?:\.\d{3})*,\d{1,2}\b|\b\d+[.,]\d{1,2}\b|\b\d{1,3}(?:\.\d{3})+\b"
_AMOUNT_BEFORE_EURO = r"\b\d+\s*(?=€|\beuro\b)"


def search_text(message: str) -> str:
    """The message without amounts, currency and date words; unchanged if nothing is left."""
    text = message
    for pattern in _DATE_WORDS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    text = re.sub(_DECIMAL, " ", text)  # before the next rule, or "1.234,50" loses only "50"
    text = re.sub(_AMOUNT_BEFORE_EURO, " ", text, flags=re.IGNORECASE)
    text = re.sub(_CURRENCY, " ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:\s\d+)+\s*$", " ", f" {text}")  # a trailing bare number is the amount
    text = re.sub(r"\s+", " ", text).strip()
    return text if re.search(r"[^\W\d_]", text) else message.strip()

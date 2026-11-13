"""Italian date words → an exact date, relative to the day the message was sent (design §6.1).

The parser LLM copies the date words verbatim; this module does the arithmetic (invariant 2).
Anything it cannot read with certainty returns None, so the draft is flagged, never guessed.
Without a year, a date is the most recent one not after the send day.
"""

import re
import unicodedata
from datetime import date, timedelta

WEEKDAYS = ("lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica")
MONTHS = (
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
)
TODAY = {"oggi", "stamattina", "stamani", "stasera", "stanotte", "oggi pomeriggio"}
YESTERDAY = {"ieri", "ieri sera", "ieri mattina", "ieri pomeriggio", "ieri notte"}
DAY_BEFORE = {"l'altro ieri", "laltro ieri", "l'altroieri", "laltroieri", "altroieri", "avantieri"}
NUMBERS = {"un": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6}

_DAYS_AGO = re.compile(r"^(\d+|un|uno|due|tre|quattro|cinque|sei) giorn[oi] fa$")
_WEEKDAY = re.compile(rf"^({'|'.join(WEEKDAYS)})( scors[oa])?$")
_DAY = re.compile(r"^(?:il |l')?(\d{1,2})°?$")
_DAY_MONTH = re.compile(r"^(?:il |l')?(\d{1,2})°? ([a-z]+)(?: (\d{4}))?$")
_NUMERIC = re.compile(r"^(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2}|\d{4}))?$")
_PREPOSITION = re.compile(r"^(?:il |lo |la |di |del |dello |della |al |a |per |dell'|l')")
_WEEKDAY_AND_DATE = re.compile(rf"^({'|'.join(WEEKDAYS)}) (\d.*)$")


def _normalise(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    plain = plain.lower().replace("’", "'").strip()
    return re.sub(r"\s+", " ", plain)


def _month(word: str) -> int | None:
    """Full Italian month name or an unambiguous 3+ letter prefix ("nov", "sett")."""
    if len(word) < 3:
        return None
    matches = [i for i, name in enumerate(MONTHS, start=1) if name.startswith(word)]
    return matches[0] if len(matches) == 1 else None


def _make(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _latest_day(day: int, today: date) -> date | None:
    """The most recent `day`-th of a month, not after today (skips months too short for it)."""
    if not 1 <= day <= 31:
        return None
    year, month = today.year, today.month
    for _ in range(12):
        candidate = _make(year, month, day)
        if candidate is not None and candidate <= today:
            return candidate
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    return None


def _latest_day_month(day: int, month: int, today: date) -> date | None:
    """The most recent day/month, not after today (29 February looks back to a leap year)."""
    for year in range(today.year, today.year - 8, -1):
        candidate = _make(year, month, day)
        if candidate is not None and candidate <= today:
            return candidate
    return None


def _full_year(text: str) -> int:
    return int(text) + 2000 if len(text) == 2 else int(text)


def resolve_date(text: str | None, today: date) -> date | None:
    """The date `text` names, seen from `today` (the send day in Europe/Rome); None if unclear."""
    if text is None or not text.strip():
        return today
    return _resolve(_normalise(text), today)


def _resolve(words: str, today: date) -> date | None:
    if words not in DAY_BEFORE and (m := _PREPOSITION.match(words)):
        return _resolve(words[m.end() :], today)  # "del 30 ottobre", "di ieri", "il giovedì"
    if m := _WEEKDAY_AND_DATE.match(words):  # "giovedì 12": the weekday must agree
        resolved = _resolve(m.group(2), today)
        if resolved is None or WEEKDAYS[resolved.weekday()] != m.group(1):
            return None
        return resolved
    if words in TODAY:
        return today
    if words in YESTERDAY:
        return today - timedelta(days=1)
    if words in DAY_BEFORE:
        return today - timedelta(days=2)
    if m := _DAYS_AGO.match(words):
        count = m.group(1)
        return today - timedelta(days=int(count) if count.isdigit() else NUMBERS[count])
    if m := _WEEKDAY.match(words):
        back = (today.weekday() - WEEKDAYS.index(m.group(1))) % 7
        if m.group(2) and back == 0:  # "venerdì scorso" said on a Friday: last week's
            back = 7
        return today - timedelta(days=back)
    if m := _DAY.match(words):
        return _latest_day(int(m.group(1)), today)
    if m := _DAY_MONTH.match(words):
        month = _month(m.group(2))
        if month is None:
            return None
        day = int(m.group(1))
        if m.group(3):
            return _make(int(m.group(3)), month, day)
        return _latest_day_month(day, month, today)
    if m := _NUMERIC.match(words):
        day, month = int(m.group(1)), int(m.group(2))
        if m.group(3):
            return _make(_full_year(m.group(3)), month, day)
        if _make(2024, month, day) is None:  # impossible in any year (31/02)
            return None
        return _latest_day_month(day, month, today)
    return None

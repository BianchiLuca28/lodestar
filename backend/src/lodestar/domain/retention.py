"""Backup schedule and retention (design §7, ADR 0018).

The PC may stay off for days, so nothing is tied to the calendar: a backup is due whenever the
newest one is older than a day, and retention counts days that have a backup, not calendar days.
"""

from collections.abc import Callable, Hashable, Iterable
from datetime import datetime, timedelta

EVERY = timedelta(days=1)


def is_due(last: datetime | None, now: datetime, every: timedelta = EVERY) -> bool:
    return last is None or now - last >= every


def _newest_per(
    stamps: Iterable[datetime], key: Callable[[datetime], Hashable], count: int
) -> set[datetime]:
    newest: dict[Hashable, datetime] = {}
    for stamp in sorted(stamps):
        newest[key(stamp)] = stamp  # later stamps of the same period win
    return set(sorted(newest.values(), reverse=True)[:count])


def to_keep(stamps: Iterable[datetime], daily: int = 30, monthly: int = 12) -> set[datetime]:
    """The newest backup of each of the last `daily` days and `monthly` months that have one."""
    stamps = list(stamps)
    return _newest_per(stamps, lambda s: s.date(), daily) | _newest_per(
        stamps, lambda s: (s.year, s.month), monthly
    )

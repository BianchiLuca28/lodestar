from datetime import UTC, datetime, timedelta

from lodestar.domain.retention import is_due, to_keep

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def at(days_ago: float, hour: int = 10) -> datetime:
    return (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=0)


def test_due_when_never_backed_up_or_older_than_a_day() -> None:
    assert is_due(None, NOW)
    assert is_due(NOW - timedelta(hours=25), NOW)
    assert not is_due(NOW - timedelta(hours=23), NOW)


def test_keeps_newest_backup_of_each_of_the_last_30_days() -> None:
    stamps = [at(d, h) for d in range(40) for h in (9, 18)]
    kept = to_keep(stamps)
    daily = {s for s in kept if s >= at(29, 0)}
    assert len(daily) == 30
    assert all(s.hour == 18 for s in daily)


def test_counts_days_that_have_a_backup_not_calendar_days() -> None:
    # Used once a week: 40 weekly backups, all on distinct days, the newest 30 are kept.
    stamps = [at(7 * w) for w in range(40)]
    kept = to_keep(stamps)
    assert set(stamps[:30]) <= kept


def test_keeps_newest_backup_of_each_of_the_last_12_months() -> None:
    stamps = [datetime(2025 + (m - 1) // 12, (m - 1) % 12 + 1, d, tzinfo=UTC)
              for m in range(1, 23) for d in (3, 20)]  # fmt: skip
    kept = to_keep(stamps, daily=0)
    assert len(kept) == 12
    assert all(s.day == 20 for s in kept)
    assert max(kept) == max(stamps)


def test_empty() -> None:
    assert to_keep([]) == set()

from datetime import date

import pytest

from lodestar.domain.dates import resolve_date

FRI = date(2026, 11, 13)  # Friday 13 November 2026


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (None, FRI),
        ("", FRI),
        ("oggi", FRI),
        ("stasera", FRI),
        ("ieri", date(2026, 11, 12)),
        ("Ieri sera", date(2026, 11, 12)),
        ("l'altro ieri", date(2026, 11, 11)),
        ("altroieri", date(2026, 11, 11)),
        ("l’altroieri", date(2026, 11, 11)),  # typographic apostrophe
        ("3 giorni fa", date(2026, 11, 10)),
        ("un giorno fa", date(2026, 11, 12)),
        ("giovedì", date(2026, 11, 12)),
        ("giovedi", date(2026, 11, 12)),
        ("venerdì", FRI),  # today is Friday: the most recent Friday not after today
        ("venerdì scorso", date(2026, 11, 6)),
        ("sabato", date(2026, 11, 7)),
        ("domenica scorsa", date(2026, 11, 8)),
        ("lunedì", date(2026, 11, 9)),
        ("il 2", date(2026, 11, 2)),
        ("2", date(2026, 11, 2)),
        ("il 1°", date(2026, 11, 1)),
        ("il 20", date(2026, 10, 20)),  # the 20th of this month is still to come
        ("il 31", date(2026, 10, 31)),
        ("il 2 novembre", date(2026, 11, 2)),
        ("2 nov", date(2026, 11, 2)),
        ("il 25 dicembre", date(2025, 12, 25)),  # this year's is in the future
        ("25 dicembre 2024", date(2024, 12, 25)),
        ("2/11", date(2026, 11, 2)),
        ("02/11/2026", date(2026, 11, 2)),
        ("2-11-26", date(2026, 11, 2)),
        ("2.11", date(2026, 11, 2)),
        ("30/11", date(2025, 11, 30)),
    ],
)
def test_resolves_italian_date_words_against_the_send_day(text: str | None, expected: date) -> None:
    assert resolve_date(text, FRI) == expected


def test_day_31_in_a_short_month_goes_back_to_a_month_that_has_it() -> None:
    assert resolve_date("il 31", date(2026, 3, 5)) == date(2026, 1, 31)  # skips February


def test_twenty_ninth_of_february_outside_a_leap_year() -> None:
    assert resolve_date("29 febbraio", date(2026, 3, 1)) == date(2024, 2, 29)


@pytest.mark.parametrize(
    "text",
    ["la settimana scorsa", "a fine mese", "boh", "31/02", "32", "0", "il 2 smarzo", "domani"],
)
def test_unclear_or_impossible_expressions_are_not_guessed(text: str) -> None:
    assert resolve_date(text, FRI) is None


def test_an_explicit_future_date_with_a_year_is_returned_for_validation_to_reject() -> None:
    assert resolve_date("2/12/2026", FRI) == date(2026, 12, 2)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("del 30 ottobre", date(2026, 10, 30)),
        ("di ieri", date(2026, 11, 12)),
        ("dell'11", date(2026, 11, 11)),
        ("giovedì 12", date(2026, 11, 12)),
        ("giovedì 12 novembre", date(2026, 11, 12)),
        ("il giovedì", date(2026, 11, 12)),
    ],
)
def test_leading_prepositions_and_a_redundant_weekday_are_ignored(
    text: str, expected: date
) -> None:
    assert resolve_date(text, FRI) == expected


def test_a_weekday_that_contradicts_the_date_is_not_guessed() -> None:
    assert resolve_date("mercoledì 12", FRI) is None  # the 12th was a Thursday

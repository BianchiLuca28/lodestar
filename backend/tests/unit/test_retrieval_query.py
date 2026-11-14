import pytest

from lodestar.ai.retrieval import search_text


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("benzina 20,13", "benzina"),
        ("zi nenè 5 giorni fa 30,50", "zi nenè"),
        ("€6,50 aperitivo", "aperitivo"),
        ("affitto novembre 1.234,50 euro", "affitto"),
        ("il 25 settembre 51,90 parati vernice", "parati vernice"),
        ("pane e salsa barbecue 4,69 il 11", "pane e salsa barbecue"),
        ("ieri cinema 8 euro", "cinema"),
        ("domenica scorsa concerto 25", "concerto"),
        ("cinema il 28/10 9 euro", "cinema"),
        ("acquisto 6 titoli di stato 16932,37", "acquisto 6 titoli di stato"),
        ("l'altro ieri treno per bologna 9,80", "treno per bologna"),
    ],
)
def test_amounts_and_date_words_are_left_out_of_the_search(message: str, expected: str) -> None:
    assert search_text(message) == expected


def test_a_message_of_only_numbers_keeps_its_text() -> None:
    assert search_text("35,01") == "35,01"

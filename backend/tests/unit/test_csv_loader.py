from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from lodestar.adapters.loaders.base import UnsupportedFile, loader_for
from lodestar.adapters.loaders.csv_loader import HEADER, CsvLoader
from lodestar.config.models import AppConfig
from lodestar.domain.ledger import Catalog

CATALOG = Catalog(
    accounts=frozenset({"Banca Aurora", "Contanti"}),
    categories={"🍝 Ristoranti": frozenset({"Pizzeria"}), "❓ Varie": frozenset()},
)
GOOD = "2026-03-14,12.50,Banca Aurora,,🍝 Ristoranti,Pizzeria,Pizza,,false"


def write(tmp_path: Path, *rows: str, header: str = ",".join(HEADER)) -> Path:
    path = tmp_path / "ledger.csv"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def test_good_row_is_parsed(tmp_path: Path) -> None:
    result = CsvLoader().load(write(tmp_path, GOOD), CATALOG)
    assert result.errors == []
    [row] = result.rows
    assert row.date == date(2026, 3, 14)
    assert row.amount == Decimal("12.50")
    assert row.from_account == "Banca Aurora" and row.to_account is None
    assert row.subcategory == "Pizzeria" and row.tag is None
    assert row.exclude_from_stats is False


def test_wrong_header_is_a_file_error(tmp_path: Path) -> None:
    result = CsvLoader().load(write(tmp_path, GOOD, header="data,importo"), CATALOG)
    assert result.rows == []
    assert result.errors[0].line == 1
    assert "header" in result.errors[0].message


@pytest.mark.parametrize(
    ("row", "field"),
    [
        ("2026-03-14,12,5,Banca Aurora,,🍝 Ristoranti,Pizzeria,Pizza,,false", None),
        ("2026-03-14,abc,Banca Aurora,,🍝 Ristoranti,Pizzeria,Pizza,,false", "amount"),
        ("14/03/2026,12.50,Banca Aurora,,🍝 Ristoranti,Pizzeria,Pizza,,false", "date"),
        (
            "2026-03-14,12.50,Banca Aurora,,🍝 Ristoranti,Pizzeria,Pizza,,forse",
            "exclude_from_stats",
        ),
        ("2026-03-14,12.50,Banca Fantasma,,🍝 Ristoranti,Pizzeria,Pizza,,false", "from_account"),
        ("2026-03-14,12.50,,,🍝 Ristoranti,Pizzeria,Pizza,,false", "from_account"),
    ],
)
def test_bad_rows_report_line_and_field(tmp_path: Path, row: str, field: str | None) -> None:
    result = CsvLoader().load(write(tmp_path, GOOD, row), CATALOG)
    assert len(result.rows) == 1
    [err] = result.errors
    assert err.line == 3
    assert err.field == field


def test_loader_chosen_by_extension(tmp_path: Path, example_config: AppConfig) -> None:
    assert isinstance(loader_for(tmp_path / "x.CSV", example_config.settings), CsvLoader)
    with pytest.raises(UnsupportedFile):
        loader_for(tmp_path / "x.pdf", example_config.settings)

"""CSV loader for the flat ledger layout of design §5 (also the Movimenti CSV export)."""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from lodestar.adapters.loaders.base import LoadResult, RowError
from lodestar.domain.errors import FieldError
from lodestar.domain.ledger import Catalog, LineInput, validate_line

HEADER = [
    "date",
    "amount",
    "from_account",
    "to_account",
    "category",
    "subcategory",
    "note",
    "tag",
    "exclude_from_stats",
]
BOOLS = {"true": True, "false": False}


class _BadField(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise _BadField("date", f"{value!r} is not an ISO date (YYYY-MM-DD)") from None


def _amount(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        raise _BadField("amount", f"{value!r} is not a number like 12.50") from None


def _bool(value: str) -> bool:
    try:
        return BOOLS[value.strip().lower()]
    except KeyError:
        raise _BadField("exclude_from_stats", f"{value!r} must be true or false") from None


def _parse(cells: dict[str, str]) -> LineInput:
    def opt(name: str) -> str | None:
        return cells[name].strip() or None

    return LineInput(
        date=_date(cells["date"].strip()),
        amount=_amount(cells["amount"].strip()),
        from_account=opt("from_account"),
        to_account=opt("to_account"),
        category=cells["category"].strip(),
        subcategory=opt("subcategory"),
        note=opt("note"),
        tag=opt("tag"),
        exclude_from_stats=_bool(cells["exclude_from_stats"]),
    )


class CsvLoader:
    def load(self, path: Path, catalog: Catalog) -> LoadResult:
        result = LoadResult()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            if [h.strip() for h in header] != HEADER:
                result.errors.append(
                    RowError(1, None, f"header must be exactly: {','.join(HEADER)}")
                )
                return result
            for number, cells in enumerate(reader, start=2):
                if not any(c.strip() for c in cells):
                    continue
                if len(cells) != len(HEADER):
                    message = f"expected {len(HEADER)} columns, found {len(cells)}"
                    result.errors.append(RowError(number, None, message))
                    continue
                try:
                    line = _parse(dict(zip(HEADER, cells, strict=True)))
                    validate_line(line, catalog)
                except _BadField as exc:
                    result.errors.append(RowError(number, exc.field, str(exc)))
                except FieldError as exc:
                    result.errors.append(RowError(number, exc.field, str(exc)))
                else:
                    result.rows.append(line)
        return result

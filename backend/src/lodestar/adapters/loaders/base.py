"""Initial-import loaders: one per file format, all producing the same validated lines."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

from lodestar.config.models import SettingsFile
from lodestar.domain.ledger import Catalog, LineInput
from lodestar.domain.portfolio import InstrumentInput, TradeInput


@dataclass(frozen=True)
class RowError:
    line: int  # 1-based line in the file (the header is line 1)
    field: str | None
    message: str

    def __str__(self) -> str:
        where = f"riga {self.line}" + (f" · {self.field}" if self.field else "")
        return f"{where}: {self.message}"


@dataclass
class LoadResult:
    rows: list[LineInput] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    created_at: list[datetime | None] = field(default_factory=list)  # UTC, aligned with rows
    adjustments: list[LineInput] = field(default_factory=list)  # written with source=adjustment
    instruments: list[InstrumentInput] = field(default_factory=list)
    trades: list[TradeInput] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # left out on purpose, shown in the report


class Loader(Protocol):
    def load(self, path: Path, catalog: Catalog) -> LoadResult: ...


class UnsupportedFile(Exception):
    pass


def loader_for(path: Path, settings: SettingsFile) -> Loader:
    from lodestar.adapters.loaders.csv_loader import CsvLoader
    from lodestar.adapters.loaders.xlsx_loader import XlsxLoader

    loaders: dict[str, Loader] = {".csv": CsvLoader(), ".xlsx": XlsxLoader(settings)}
    try:
        return loaders[path.suffix.lower()]
    except KeyError:
        raise UnsupportedFile(
            f"{path.name}: unsupported file type; use one of {', '.join(loaders)}"
        ) from None

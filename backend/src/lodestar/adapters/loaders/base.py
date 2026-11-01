"""Initial-import loaders: one per file format, all producing the same validated lines."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from lodestar.domain.ledger import Catalog, LineInput


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


class Loader(Protocol):
    def load(self, path: Path, catalog: Catalog) -> LoadResult: ...


class UnsupportedFile(Exception):
    pass


def loader_for(path: Path) -> Loader:
    from lodestar.adapters.loaders.csv_loader import CsvLoader

    loaders: dict[str, Loader] = {".csv": CsvLoader()}
    try:
        return loaders[path.suffix.lower()]
    except KeyError:
        raise UnsupportedFile(
            f"{path.name}: unsupported file type; use one of {', '.join(loaders)}"
        ) from None

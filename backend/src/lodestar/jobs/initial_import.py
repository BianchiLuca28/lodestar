"""One-time initial import into an empty ledger (design §5, ADR 0015).

Usage: python -m lodestar.jobs.initial_import FILE [--dry-run] [--config DIR] [--data DIR]
"""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from lodestar.adapters.db.engine import db_path, make_engine, migrate
from lodestar.adapters.db.initial_import_repo import write_import
from lodestar.adapters.db.transactions_repo import TransactionRepository
from lodestar.adapters.loaders.base import UnsupportedFile, loader_for
from lodestar.config.catalog import catalog_of
from lodestar.config.loader import ConfigError, load_config
from lodestar.domain.import_report import ImportSummary, format_report, summarize
from lodestar.domain.portfolio import InstrumentInput, TradeInput, link_trades

EXIT_OK, EXIT_INVALID, EXIT_NOT_EMPTY = 0, 1, 2


class LedgerNotEmpty(Exception):
    pass


@dataclass
class ImportOutcome:
    summary: ImportSummary
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # instruments, trades, skipped items
    written: int = 0


def run_import(path: Path, config_dir: Path, data_dir: Path, dry_run: bool) -> ImportOutcome:
    config = load_config(config_dir)
    catalog = catalog_of(config)
    db = db_path(data_dir)
    migrate(db)
    engine = make_engine(db)
    try:
        repo = TransactionRepository(engine)
        if repo.count() > 0:
            raise LedgerNotEmpty(
                "Il registro non è vuoto: l'import iniziale si fa una volta sola (ADR 0015)."
            )
        result = loader_for(path, config.settings).load(path, catalog)
        links = link_trades(result.trades, result.rows)
        outcome = ImportOutcome(
            summarize([*result.rows, *result.adjustments]),
            [str(e) for e in result.errors],
            _portfolio_notes(result.instruments, result.trades, links, result.skipped),
        )
        if not dry_run and not outcome.errors:
            created = result.created_at or [None] * len(result.rows)
            written = write_import(
                engine,
                result.rows,
                created,
                result.adjustments,
                result.instruments,
                result.trades,
                links,
            )
            outcome.written = written.lines
        return outcome
    finally:
        engine.dispose()


def _portfolio_notes(
    instruments: Sequence[InstrumentInput],
    trades: Sequence[TradeInput],
    links: Sequence[int | None],
    skipped: Sequence[str],
) -> list[str]:
    if not instruments and not trades and not skipped:
        return []
    traded = {t.ticker for t in trades}
    watchlist = sum(1 for i in instruments if i.ticker not in traded)
    linked = sum(1 for link in links if link is not None)
    notes = [
        f"Strumenti: {len(instruments)} (in watchlist: {watchlist})",
        f"Operazioni: {len(trades)} (collegate a un movimento: {linked})",
    ]
    if skipped:
        notes += ["Non importati:", *(f"- {s}" for s in skipped)]
    return notes


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    parser.add_argument("--config", type=Path, default=Path("config"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)
    # Category names carry emoji; the Windows console defaults to cp1252.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    try:
        outcome = run_import(args.file, args.config, args.data, args.dry_run)
    except LedgerNotEmpty as exc:
        print(exc, file=sys.stderr)
        return EXIT_NOT_EMPTY
    except (ConfigError, UnsupportedFile, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
        return EXIT_INVALID

    print(format_report(outcome.summary, outcome.errors, outcome.notes))
    print()
    if args.dry_run:
        print("Dry run: nothing written.")
    elif outcome.errors:
        print("Import aborted: fix the invalid rows; nothing was written.")
    else:
        print(f"Imported {outcome.written} rows.")
    return EXIT_INVALID if outcome.errors else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

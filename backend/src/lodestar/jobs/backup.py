"""Database backups to a local folder, and restore (design §7, ADR 0018).

Usage:
  python -m lodestar.jobs.backup now [--config DIR] [--data DIR]
  python -m lodestar.jobs.backup restore FILE [--data DIR] [--yes]

Backups are plain SQLite copies taken with the online backup API, so they are consistent while
the app runs. Inside the app, `backup_if_due` runs at startup and every hour.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from lodestar.adapters.backup_folder import (
    BackupNotValid,
    backup_folder,
    backup_if_due,
    backups_in,
    prune,
    restore,
    run_backup,
)

__all__ = ["BackupNotValid", "backup_if_due", "backups_in", "main", "restore", "run_backup"]


def main(argv: Sequence[str] | None = None) -> int:
    from lodestar.adapters.db.engine import db_path
    from lodestar.config.loader import ConfigError, load_config

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    now_cmd = sub.add_parser("now", help="make a backup now")
    now_cmd.add_argument("--config", type=Path, default=Path("config"))
    now_cmd.add_argument("--data", type=Path, default=Path("data"))
    restore_cmd = sub.add_parser("restore", help="replace the database with a backup")
    restore_cmd.add_argument("file", type=Path)
    restore_cmd.add_argument("--data", type=Path, default=Path("data"))
    restore_cmd.add_argument("--yes", action="store_true", help="skip the confirmation")
    args = parser.parse_args(argv)

    db = db_path(args.data)
    if args.command == "now":
        try:
            folder = backup_folder(load_config(args.config), args.data)
        except ConfigError as exc:
            print(exc, file=sys.stderr)
            return 1
        if folder is None:
            print("Backups are disabled: enable a folder target in settings.yaml.")
            return 1
        made = run_backup(db, folder, datetime.now(UTC))
        removed = prune(folder)
        print(f"Backup written: {made}" + (f" ({len(removed)} old removed)" if removed else ""))
        return 0

    print(f"This replaces {db} with {args.file}. Stop the app first (docker compose down).")
    if not args.yes and input("Type 'si' to continue: ").strip().lower() != "si":
        print("Restore cancelled.")
        return 1
    try:
        aside = restore(args.file, db)
    except (BackupNotValid, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Restored. The previous database is kept at {aside}." if aside else "Restored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

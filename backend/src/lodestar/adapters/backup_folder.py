"""Backups as plain SQLite copies in a local folder (design §7, ADR 0018)."""

import re
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from lodestar.config.models import AppConfig
from lodestar.domain.retention import is_due, to_keep

NAME = re.compile(r"^lodestar-(\d{8}-\d{6})\.db$")
STAMP = "%Y%m%d-%H%M%S"


class BackupNotValid(Exception):
    pass


def backup_folder(config: AppConfig, data_dir: Path) -> Path | None:
    """The enabled folder target; a relative path lives under the data dir. None: disabled."""
    for target in config.settings.backup.targets:
        if target.kind == "folder" and target.enabled and target.path:
            path = Path(target.path)
            return path if path.is_absolute() else data_dir / path
    return None


def backups_in(folder: Path) -> dict[datetime, Path]:
    """Backup files by their UTC timestamp; other files in the folder are ignored."""
    found: dict[datetime, Path] = {}
    if folder.is_dir():
        for file in folder.iterdir():
            match = NAME.match(file.name)
            if match:
                found[datetime.strptime(match[1], STAMP).replace(tzinfo=UTC)] = file
    return found


def last_backup(folder: Path) -> datetime | None:
    return max(backups_in(folder), default=None)


def _copy(source: Path, target: Path) -> None:
    src = sqlite3.connect(source)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def run_backup(db: Path, folder: Path, now: datetime) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"lodestar-{now.astimezone(UTC):{STAMP}}.db"
    partial = target.with_suffix(".db.partial")
    _copy(db, partial)
    partial.replace(target)  # a half-written file never looks like a backup
    return target


def prune(folder: Path) -> list[Path]:
    backups = backups_in(folder)
    keep = to_keep(backups)
    removed = [path for stamp, path in backups.items() if stamp not in keep]
    for path in removed:
        path.unlink()
    return removed


def backup_if_due(db: Path, folder: Path, now: datetime) -> Path | None:
    if not is_due(last_backup(folder), now):
        return None
    made = run_backup(db, folder, now)
    prune(folder)
    return made


def _check(file: Path) -> None:
    if not file.is_file():
        raise FileNotFoundError(f"{file} not found: pick a file listed in the backups folder")
    try:
        with sqlite3.connect(f"file:{file.as_posix()}?mode=ro", uri=True) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    except sqlite3.DatabaseError:
        raise BackupNotValid(f"{file.name} is not a SQLite database") from None
    if not {"transactions", "alembic_version"} <= tables:
        raise BackupNotValid(f"{file.name} is not a Lodestar database")


def restore(file: Path, db: Path, now: datetime | None = None) -> Path | None:
    """Replace `db` with the backup; the replaced file is kept aside and returned."""
    _check(file)
    db.parent.mkdir(parents=True, exist_ok=True)
    aside = None
    if db.exists():
        stamp = (now or datetime.now(UTC)).astimezone(UTC)
        aside = db.with_name(f"{db.name}.before-restore-{stamp:{STAMP}}")
        _copy(db, aside)
        for extra in (db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm")):
            extra.unlink(missing_ok=True)
        db.unlink()
    shutil.copyfile(file, db)
    return aside

# Cutover: from the Google Sheet to Lodestar

A one-time checklist (design §0, §5 Initial import; ADRs 0001, 0015). At the end, Lodestar is the only copy of your history and the Sheet is gone. Allow about an hour.

Commands run from the repository root in Git Bash; in PowerShell use the `uv run` lines shown where `make` is not available.

## 1. Last Sheet update

- [ ] Log every movement up to today in the Sheet.
- [ ] Fix the dates you know are wrong (for example bond trades that settled the day after).
- [ ] From "Patrimonio", write down the real balance of every account and the date it refers to. You will compare against these in step 7.

| Account | Balance | Date |
|---------|---------|------|
|         |         |      |

## 2. Download the XLSX

- [ ] Google Sheets → File → Download → Microsoft Excel (.xlsx).
- [ ] Save it in `data/` (git-ignored), for example `data/SituazionePatrimoniale.xlsx`.

## 3. Config

New install: `cp -r config.example config`, then edit every file. If `config/` already exists, check:

- [ ] `accounts.yaml`: every account the Sheet uses, exactly one `is_default`.
- [ ] `categories.yaml`: every category with the same spelling and emoji as the Sheet, and the subcategories you use (an empty list accepts any).
- [ ] `settings.yaml → portfolio.trade_account`: your broker account.
- [ ] `settings.yaml → initial_import`:
  - `asset_classes`: the Sheet's "Asset" labels → asset class and bucket
  - `instruments`: per-ticker overrides (ISIN, ticker, class, bucket)
  - `skip_tickers` and `watchlist`: what to leave out, and which untraded instruments to keep
  - `adjustment`: the plan's realignment line (date, amount, account, direction)
- [ ] `settings.yaml → backup`: the folder target is enabled (`path: backups`).

## 4. Stop the app

- [ ] `docker compose down`. The import writes `data/lodestar.db` directly; nothing else may hold it.

## 5. Dry run

```bash
make import FILE=data/SituazionePatrimoniale.xlsx ARGS=--dry-run
# PowerShell: cd backend; uv run python -m lodestar.jobs.initial_import ..\data\SituazionePatrimoniale.xlsx --dry-run --config ..\config --data ..\data
```

Read the report:

- [ ] **No "Righe non valide".** Each line names the sheet row and the field; fix the Sheet or `config/` and download again.
- [ ] **Counts and period** match the Sheet ("Righe valide" = your rows + the adjustment).
- [ ] **Per-account in/out totals** look right.
- [ ] **"Operazioni"**: every trade "collegata a un movimento"; an unlinked trade means its cash line has a different date or account.
- [ ] **"Non importati"**: only what you meant to leave out (zero-amount rows, crypto, positions outside the watchlist).

The dry run writes nothing.

## 6. Import

```bash
make import FILE=data/SituazionePatrimoniale.xlsx
```

- [ ] It ends with "Imported N rows." If it says the ledger is not empty, see "Start over" below.

## 7. Compare balances

- [ ] `make dev`, open <http://127.0.0.1:8080/movimenti>.
- [ ] In **Saldi**, for each account press **Verifica saldo**, enter the date and balance noted in step 1.
  - Gap 0: done.
  - A gap: look for the missing or wrong movement first and fix it on Movimenti. If the gap is real history you cannot rebuild, confirm the check to record a "Riallineamento saldo" adjustment (excluded from stats).
- [ ] Every account checked.

## 8. First backup and a restore test

```bash
make backup
```

- [ ] It prints `Backup written: …/data/backups/lodestar-YYYYMMDD-HHMMSS.db`.
- [ ] Test the restore **into a throwaway folder**, so the real database is not touched. Replace `YYYYMMDD-HHMMSS` with the name `make backup` just printed:

```bash
make restore FILE=data/backups/lodestar-YYYYMMDD-HHMMSS.db DATA=data-restore-test
# type "si" to confirm
cd backend && uv run python -c "import sqlite3; print(sqlite3.connect('../data-restore-test/lodestar.db').execute('select count(*) from transactions').fetchone())"
```

- [ ] The count matches the rows on Movimenti. Then delete `data-restore-test/`.

## 9. Retire the Sheet

- [ ] Export the ledger once from Movimenti (**Esporta → Excel**) and keep it with the downloaded XLSX in `data/` for a month, as a safety net.
- [ ] Delete the Google Sheet and its Form.
- [ ] After a month without surprises, delete the XLSX files too. From now on the database and its backups are the only copy (ADR 0001).
- [ ] Close the cutover issue: the v0.1 gate "Spreadsheet retired" is reached.

## Start over

The import runs into an empty ledger only. To redo it before you start using Lodestar:

1. `docker compose down`
2. Move `data/lodestar.db` (and any `lodestar.db-wal` / `-shm`) out of `data/`.
3. Repeat from step 5. The app recreates an empty database on the next start.

Once you have added movements in the app, do not start over: fix single movements on Movimenti instead.

## Found a bug?

Open a `fix/` issue with the step, the command and the message (no real amounts), and finish the cutover after it is merged.

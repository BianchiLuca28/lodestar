# One-time initial import from XLSX or CSV

The ledger is seeded once, into an empty database, from either the 7-sheet XLSX or a flat CSV with the `transactions` columns, each read by its own loader into the same rows. After the import the database is the only copy (ADR 0001): Lodestar never reads the file again, the user may delete it, and a second import is refused. The CSV loader serves the fake ledger in `config.example/` and users who never had the Sheet.

## Considered Options

- XLSX only: ties the importer to one person's spreadsheet layout and leaves the fake persona without a realistic seed path.
- Keep the file as a recurring input: would make it a second source of truth, which ADR 0001 rules out.

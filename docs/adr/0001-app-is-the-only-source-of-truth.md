# The app is the only source of truth

The ledger used to live in a Google Sheet fed by a Google Form. Lodestar imports it once (all sheets, plus a balancing adjustment for unreliable early data) and then the Sheet is retired. Every number comes from Lodestar's database; XLSX/CSV export exists for portability, never as a second place to edit.

## Considered Options

- Two-way sync with the Sheet: fragile, conflict-prone, and keeps the wide spreadsheet format alive.
- AI layer on top of the Sheet: leaves prices on GOOGLEFINANCE and the data model limited by spreadsheet columns.

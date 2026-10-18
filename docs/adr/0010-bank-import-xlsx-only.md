# Bank statements are imported from XLSX only

Bank reconciliation reads the XLSX exports of the user's banks with deterministic parsers, then de-duplicates against the ledger (same account and amount, date within a few days) and turns new or uncertain lines into drafts. PDF statements are out of scope for now: XLSX is reliable and needs no LLM.

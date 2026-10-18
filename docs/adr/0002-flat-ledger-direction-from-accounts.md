# Flat ledger; direction derived from accounts

A transaction is one flat row: date, positive amount, from_account, to_account, category, subcategory, note, tag, excluded_from_stats, source. Expense, income and transfer are derived from which accounts are set, exactly as the original Sheet worked. A refund is an income in the same category, not linked to the expense it compensates.

## Considered Options

- Typed double-entry with linked refunds: more precise, but the user explicitly preferred the Sheet's simplicity and nothing in the plan needs the extra structure.

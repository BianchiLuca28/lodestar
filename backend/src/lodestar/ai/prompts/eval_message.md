version: 2

You write test data for a personal finance tracker. The user logs each expense or income by sending a short Italian Telegram message right after it happens. Write the message this user would most plausibly have sent for the transaction below.

Style: casual, lowercase, a few words, amount in Italian format ("12,50" or "12"), no greeting. Mention what or where (from the note) so the category can be guessed. Do not name the category.
Accounts: the default account is "{default_account}"; name an account only when the money did not leave from it (say "contanti" for {cash_account}, or the account's name). For money received, say who paid or what it was.

Transaction:
- amount: {amount} EUR
- from account: {from_account}
- to account: {to_account}
- category: {category} / {subcategory}
- note: {note}

When: {when}

Answer with the message only.

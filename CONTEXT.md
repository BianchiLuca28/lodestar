# Lodestar

A personal ledger and plan checker for one person: money movements between their accounts, the buckets their savings are split into, and the rules of their written financial plan. UI labels are Italian; the Italian label follows each term.

## Ledger

**Transaction** (_Movimento_):
One movement of money on a given date: a positive amount, a category, and at least one of a source account and a destination account.
_Avoid_: entry, record, line, expense (an expense is one direction of a transaction)

**Account** (_Conto_):
A place where the user's money sits: a bank account, a broker, cash, a postal account. Each belongs to one bucket.
_Avoid_: wallet, balance

**Direction**:
What a transaction does, derived from its accounts: only a source account = **expense** (_uscita_); only a destination account = **income** (_entrata_); both = **transfer** (_trasferimento_). Never stored.
_Avoid_: type, sign

**Refund**:
An income in the same category as the expense it compensates (a friend paying back their share, a returned item). Not linked to the original transaction.
_Avoid_: reimbursement record, storno line

**Category** (_Categoria_) / **Subcategory** (_Sottocategoria_):
The user-configured classification of a transaction, e.g. "🍸 Cibo fuori / Bevute" / "Pizzeria". Subcategories belong to exactly one category.

**Discretionary category**:
A category flagged in config as optional spending; their expenses count towards the monthly discretionary cap.

**Tag**:
A free label grouping transactions across categories, typically a trip ("Vacanza Zante - 2026").

**Trip** (_Viaggio_):
A period in which every new draft gets the trip's tag by default, opened with `/viaggio` and closed with `/fine` or by expiry.

**Excluded from stats**:
A flag that keeps an extraordinary transaction (inheritance, internal movements tied to an investment) out of income, expense and savings-rate figures while still moving balances.

**Source**:
How a transaction entered the ledger: manual, telegram, receipt, bank_xlsx, import, adjustment.

**Initial import** (_Importazione iniziale_):
The one-time seeding of an empty ledger from a file (the 7-sheet XLSX or a flat CSV), through one loader per format. Its rows get source `import`; afterwards the file is no longer needed.
_Avoid_: sync, re-import

**Balance check** (_Verifica saldo_):
The user's real balance of one account on one date, compared with the balance computed from the ledger.

**Adjustment** (_Rettifica_):
A transaction created on purpose to close the gap found by a balance check or a data migration.

## Input

**Inbound message**:
A raw Telegram update (text, photo, document or button press) as received by the relay, before any interpretation.

**Relay**:
The cloud queue that holds inbound messages until the user's PC collects them.

**Draft** (_Bozza_):
One or more proposed transactions produced from an inbound message, a bank import or a receipt, waiting for the user to approve, edit or reject. Only approval turns a draft into transactions.
_Avoid_: suggestion, pending transaction

**Possible duplicate** (_Possibile duplicato_):
A draft whose line resembles an existing transaction (same account and amount, close date) and needs an explicit decision.

## Plan

**Plan** (_Piano_):
The user's written financial plan, a markdown document the agent reads for context.

**Bucket** (_Pilastro_):
A container of money with one purpose, horizon and risk level (e.g. liquidity, emergency fund, house, long term). Has a target amount and a monthly contribution.
_Avoid_: pillar (in code), pot, envelope

**Rule** (_Regola_):
A measurable check derived from the plan or set by the user, with thresholds in config (e.g. discretionary spending ≤ €700/month).

**Rule status**:
The result of evaluating a rule now: ok, warning or breach, with the numbers behind it.

**Safety valve** (_Valvola_):
The rule that halves next month's contributions when the liquidity account falls below its threshold.

**Contribution** (_Versamento_):
The planned monthly transfer from the liquidity account into a bucket.

**Planned expense** (_Spesa pianificata_):
A known future expense with an amount and an optional expected date (e.g. replacing the car).

**Digest** (_Riepilogo mensile_):
The monthly Telegram summary of rule status and the plan's key numbers.

**Alert** (_Avviso_):
A Telegram message sent when a specific rule changes status or something becomes due.

## Investments

**Instrument** (_Strumento_):
A security the user can hold: ETF, government bond, money-market ETF. Has an asset class, a tax rate and a price source.

**Trade** (_Operazione_):
A buy or sell of an instrument on a date, with quantity, price and fees. Each trade has a matching cash transaction.

**Position** (_Posizione_):
The quantity of an instrument currently held in an account, derived from trades.

**Coupon** (_Cedola_):
Periodic interest paid by a bond, received net of tax as an income to the broker account, excluded from stats. Coupons in P3 are never spent; they go into the next quarterly order.

**Accrued interest** (_Rateo_):
Interest built up since a bond's last coupon, paid to the seller on purchase and recovered with the next coupon. Stored on the trade.

**Quarterly order** (_Ordine trimestrale_):
The single P3 bond purchase placed at the end of January, April, July and October, alternating Italian and German bonds (ADR 0016).

**Expected house date**:
The date P3 must be fully liquid by; every P3 bond matures on or before it. Set in config, reviewed every January.

**Instrument policy** (_Policy strumenti_):
The user's written list of instruments and constraints allowed per bucket, plus a blacklist; the only universe the agent may suggest from.

## Knowledge

**Knowledge base**:
The user's own reference documents (e.g. course notes) indexed locally and cited in chat answers.

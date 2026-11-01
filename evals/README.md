# Evals

The eval set is the backbone of every AI change (design §6.5).

```
datasets/parsing/cases.jsonl   synthetic cases for the fake persona (config.example/)
results/                       one JSON per run: <date>_<model>_<prompt-version>.json
data/private/                  git-ignored: cases built from your real ledger
results/private/               git-ignored: results on private cases
```

## Case format

One JSON object per line:

```json
{"id": "cash", "message": "caffè 1,30 in contanti", "sent_at": "2026-11-05T08:40:00+01:00",
 "expected": [{"date": "2026-11-05", "amount": "1.30", "from_account": "Contanti",
               "category": "🍝 Ristoranti", "subcategory": "Caffè", "note": "Caffè"}]}
```

`expected` lists the ledger lines in order (`date, amount, from_account, to_account, category, subcategory, note, tag`). Amounts are strings compared as `Decimal`. Relative dates ("ieri", "sabato") resolve against `sent_at`.

## Running

- `make eval` runs the full set and prints a metrics table; `make eval ARGS=--compare` adds a before/after against the last saved result.
- Metrics: line count accuracy, exact match per field, category accuracy, amount accuracy.
- Until the v0.2 parser lands, the only predictor is the scripted fake, so scores are 1.000. Results from the fake (`*_fake_*.json`) are git-ignored; commit results from real models to keep the history.
- CI runs the runner with the fake predictor through `pytest` (`backend/tests/unit/test_eval_runner.py`).

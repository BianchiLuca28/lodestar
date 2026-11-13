# Parsing model: gpt-oss:20b, without a head-to-head against qwen3:8b

Settles the open point "gpt-oss:20b vs qwen3:8b" (design §6, §12).

The design planned to pick the parsing model by eval score between `gpt-oss:20b` and `qwen3:8b`. The user chose not to download `qwen3:8b` for now: `gpt-oss:20b` is already installed, and bigger models are already available locally if a comparison is ever needed. Any download stays the user's call.

`gpt-oss:20b` is therefore the default for `models.parse` and `models.chat`. Its score on the public fake set (30 cases, prompt v2 with few-shot retrieval, 13/11/2026): category 1.000, amount 1.000, line count 1.000, from_account 0.909, date 0.909, tag 0.939, loose note 0.879, about 3.1 s per case. The private set (about 100 cases from the real ledger, checked by the user) is run with `make eval ARGS="--live --private"`, and its results stay git-ignored.

Changing the model later needs no code change: set `models.parse` in `config/settings.yaml`, then run `make eval ARGS="--live --model <name>"` on both sets. The winning rule agreed for any comparison is: highest category accuracy wins, and within 3 points the faster model (`seconds_per_case`) wins.

**Considered:** pulling `qwen3:8b` (about 5 GB) to compare now (rejected by the user: not needed while gpt-oss scores well); comparing the larger local models `qwen3.8:27b` and `gemma4:12b` (deferred: the same commands do it whenever wanted).

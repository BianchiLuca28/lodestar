---
description: Run the LLM eval suite and compare against the last recorded results
argument-hint: [suite, e.g. parse | rag | policy] [model override]
---

Run the evals for: **$ARGUMENTS** (all suites if empty).

1. Check Ollama is reachable at the endpoint in settings and the configured models are pulled; if not, stop and tell me which `ollama pull` to run.
2. `make eval` with the requested suite and model.
3. Compare with the latest file in `evals/results/` for the same suite: per-metric before/after table, plus the 5 worst failing cases with expected vs actual output.
4. Save the new results file (suite, model, prompt versions, date in the name).
5. Summarise in three lines: did it get better or worse, where, and the most likely cause.

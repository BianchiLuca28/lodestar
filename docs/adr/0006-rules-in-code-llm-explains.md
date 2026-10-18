# Plan rules are checked by code; the LLM only explains

The plan's measurable rules (discretionary cap, liquidity range, safety valve, contributions, bucket trajectory, emergency fund size) live in rules.yaml, edited by hand or through the Regole form, and are evaluated by deterministic Python. The LLM receives rule results and writes explanations; it never computes a figure shown to the user. Small local models are unreliable at arithmetic and at extracting thresholds from long prose.

## Considered Options

- LLM reasons over the markdown plan alone: flexible, but unverifiable and inconsistent between runs.

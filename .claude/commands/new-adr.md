---
description: Record an architectural decision as a new ADR and sync the design doc
argument-hint: <short decision title>
---

Record the decision: **$ARGUMENTS**.

1. Check it qualifies: hard to reverse, surprising without context, and the result of a real trade-off. If any is missing, tell me and stop.
2. Find the highest number in `docs/adr/` and create `docs/adr/NNNN-<slug>.md`: a title, then 1–3 sentences of context, decision and why. Add "Considered Options" only if the rejected alternatives are worth remembering. If it replaces an older ADR, add `Status: superseded by ADR-NNNN` to the old one.
3. Update the matching parts of `docs/design.md` (including §13 Decision log) so the two never disagree.
4. Show me the diff.

---
description: Turn one roadmap phase from docs/design.md into a GitHub milestone with slice issues
argument-hint: <phase, e.g. v0.1>
---

Create the GitHub milestone and issues for phase **$ARGUMENTS**.

1. Read `docs/design.md` §11 (Roadmap) for the phase's checklist and gate, plus every section those items reference. Read `CONTEXT.md` and the relevant ADRs.
2. Split the phase into **vertical slices**: each one delivers something the user can see or run end to end, is mergeable alone, and takes at most a day or two. A checklist item may become several slices; foundational slices come first.
3. For each slice, draft an issue from `.github/ISSUE_TEMPLATE/slice.md`: goal, design reference (§ and ADRs), checkable acceptance criteria, test notes, out of scope.
4. Show me the full list (title + one-line goal, in order, with dependencies) and wait for my approval.
5. After approval: `gh api repos/{owner}/{repo}/milestones -f title="$ARGUMENTS — <phase name>" -f description="<gate>"`, then `gh issue create` for each slice with `--milestone` and label `slice`, in dependency order. Reply with the issue numbers.

Done when every checklist item of the phase is covered by at least one issue and the phase gate is reachable by closing them all.

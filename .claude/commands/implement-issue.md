---
description: Implement one GitHub issue end to end, test-first, and open a PR
argument-hint: <issue number>
---

Implement issue **#$ARGUMENTS**.

1. `gh issue view $ARGUMENTS`. Read the `docs/design.md` sections and ADRs it references, and `CONTEXT.md`.
2. Plan: restate the acceptance criteria, list the files you will create or change, the tests that will prove each criterion, and any question the design leaves open. Wait for my OK.
3. Branch `feat/$ARGUMENTS-<slug>` (or `fix/`, `chore/`) from an up-to-date `main`.
4. For each acceptance criterion: write the failing test, make it pass, refactor. Commit in small Conventional Commits.
5. If prompts, models, graphs or retrieval changed: run `make eval` on `main` and on the branch and keep both tables.
6. If a decision changed or a new domain term appeared: add the ADR and update `docs/design.md` / `CONTEXT.md` in this branch.
7. `make lint test` green, then `gh pr create` using `.github/pull_request_template.md`, with `Closes #$ARGUMENTS`.

Done when every acceptance criterion maps to a passing test and the PR template is fully filled.

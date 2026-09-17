# 2026-08-31 Hermes patch-stack rebase

## Scope

- Canonical fork branch: `peter/hermes-patches`
- Preserved pre-rebase fork tip: `231d56bf8cec3878a3ebf072205c88d313fb4de1`
- Recovery ref: `recovery/hermes-update-remote-pre-rebase-20260831T101137Z`
- Previous upstream tracking tip: `1f99a4b2f2982fbef06df00ad673ade4e1895668`
- Previous patch-stack base: `a9611f3c6f7ff287a4f10f71a77d7c5a808ea1c8`
- Initially captured canonical upstream base: `2f261f99fff98036da5b383498470fe5b0f68136`
- Final refreshed canonical upstream base: `38b7d0f4cf8a11137d8da5e3d95d7b5b7e41fb46`
- Candidate branch: `update/hermes-patches-20260831T101137Z`
- Initial source candidate before the upstream refresh: `7187df29fd9cd17ff80af5b623aec40ff655cd16`
- Final source candidate before this report: `a168d67c796a0d21bc6848d4a652197be6263e5d`

The rebase ran in an isolated worktree. The live checkout at `/opt/hermes-agent`, its venv, and the checked-out fork branch remained untouched.

## Patch decisions

The source-stack range-diff against the previous 77-commit stack initially classifies:

- 75 commits as patch-identical (`=`).
- 2 commits as adapted (`!`) to current upstream structure.
- No source patches as dropped (`<`).
- No new source patches as added (`>`).

Material adaptations:

- `3711154f87` → `7e88edde68`: retained the configured approval/sudo prompt bell while composing it with upstream's new literal-submission reference in `useMainApp`; 148 focused TUI tests and the TUI typecheck passed immediately after conflict resolution.
- `c07127db4e` → `8b672eebe0`: context-only composition with upstream `393af4a310` todo-state response wrapping; the session-scoped tool-preview budget remains threaded through the existing response owner without bypassing `_attach_todo_state`.

Canonical upstream advanced once during verification from `2f261f99ff` to `446563262e`. The candidate was refreshed again; all 77 patches replayed without conflict and the refresh-to-refresh range-diff classified all 77 commits as patch-identical.

It advanced a second time to `38b7d0f4cf` with credential and environment-state reliability fixes plus contributor metadata. The candidate was refreshed again; all 77 patches replayed without conflict and all 77 remained patch-identical to the prior refreshed candidate.

The final semantic supersession audit covered all 29 active patch families against `38b7d0f4cf`: 27 retain unchanged, 2 retain with the adaptations above, and 0 drop. It found no blocker, no newly superseded behavior, and no unexplained range-diff entry.

## Catalogue

- Reconciled all 29 retained active rows and report headers to the rebased commit identities while preserving earlier refs as lineage.
- No active patch family was dropped or retired in this rebase.
- Mechanical validation of active refs and linked reports is part of the final verification gate below.

## Verification

- Conflict-focused TUI event/config tests: 148 passed; TUI typecheck passed.
- Changed-area Python suite (`scripts/run_tests.sh`): 39 files; 1,573 passed, 10 skipped, 0 failed across 8 workers in 91.1 seconds.
- Full root JavaScript check after the final upstream refresh: Desktop UI 6,758 passed; Desktop Electron 1,962 passed and 6 skipped; TUI 1,735 passed; Web 281 passed; JS integration 53 passed; all typechecks, lint gates, builds, and the Desktop packaging smoke passed. Existing lint warnings and build-environment warnings remained non-fatal.
- Python lint: Ruff passed across all 75 changed Python files; one pre-existing invalid `# noqa` warning in `run_agent.py:108` was non-fatal.
- Final-refresh credential/environment regressions: 18 passed across `test_env_export_line_lifecycle.py`, `test_credential_lifecycle.py`, and `test_model_assignment_env_key_mirror.py`.
- Structural checks: `git diff --check` passed.
- Catalogue lineage validation: 29 active patch families; every active ref resolves, is outside upstream, is an ancestor of the candidate, and appears in its linked report.
- Semantic supersession audit: 29 families audited; 27 retain unchanged, 2 adapted-and-retained, 0 dropped; no blocker.
- Independent review of source candidate and catalogue reconciliation at `eddb5c7b79c08b6b54fc6271fa8944092502dedb`: no blockers; both adaptations, the 75/2 range-diff classification, and all 29 active-family lineages were clean.
- Final upstream-stability check: refreshed to `38b7d0f4cf`; repeat immediately before the immutable review and publication gate.

## Publication gate

Freeze the final candidate, verify canonical upstream has not advanced from the final reviewed base, compare the fork ref with the frozen lease baseline, and publish only with explicit expected-object `--force-with-lease`. Any mismatch aborts publication.

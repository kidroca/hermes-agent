# 2026-08-23 Hermes patch-stack rebase

## Scope

- Canonical fork branch: `peter/hermes-patches`
- Preserved pre-rebase fork tip: `d48fdf07a852925b28b1f4ac247a697aad45a998`
- Recovery ref: `recovery/hermes-update-remote-pre-rebase-20260823T102428Z`
- Previous upstream base: `a90d5369f76c87c98547d2e283aa26d5cfabf322`
- Initial fetched upstream base: `933c209e96630a6026b0a18ecf6a86e65110f5b8`
- Final refreshed upstream base: `b766607b5b92879c21ffd767465487e6de725868`
- Candidate branch: `update/hermes-patches-20260823T102428Z`
- Source candidate before this report: `6687e867f7` (the final-base rewrite of `1e8467df26`)

The rebase ran in an isolated worktree. The live checkout at `/opt/hermes-agent`, its venv, and the checked-out fork branch remained untouched.

## Patch decisions

The final source-stack range-diff against the previous 73-commit stack classifies:

- 58 commits as patch-identical (`=`).
- 14 commits as adapted (`!`) to current upstream structure.
- 1 source patch as dropped (`<`).
- 1 new documentation commit (`>`) for the 2026-08-23 lineage reconciliation.

After verification, upstream advanced by 20 commits. The complete 74-commit candidate rebased over that final delta patch-identically (`74 =`, no conflicts), then the active catalogue lineage was refreshed once more.

Dropped patch:

- `c9519c86e3` / rebased trial `0339000898` — provider retry output-cap metadata. Current upstream initially resolves output caps in priority order `ephemeral > user > profile default`, but later profile top-level extras can still overwrite that value. No bundled provider profile consumes the forwarded metadata, and the local regression returned its competing value in the `extra_body` half of the hook tuple, so it did not prove the claimed top-level override edge case. The patch was retired as unused/speculative metadata—not as upstream-equivalent ordering—and the final transport suite passes without it.

Materially adapted patch families:

- Browser/CDP preservation, TUI approval bell, and TUI npm-launch optimization were reconciled with upstream desktop surface and TUI launcher changes.
- TUI SessionDB recovery and warning were ported onto upstream's explicit DB ownership transfer contract; recovered profile handles are agent-owned and close on teardown.
- TUI memory-context visibility and Slack authored-query recall were routed through upstream's durable turn-lease/finalization flow.
- Kanban profile invocation isolation was composed with upstream profile discovery and memory-pressure dispatch policy.
- TUI tool-preview budgets were preserved across upstream timestamped transcript hydration.
- Doctor's bounded shallow checks were composed with upstream repair durability barriers and live-writer/snapshot handling.
- The TUI approval-bell integration commit was reconciled with upstream batch clarification behavior.
- External-memory prefetch deadlines retained configuration ownership while using upstream's generic memory manager.
- Curator guarded-read serialization was retained across current timestamped message dispatch.
- Fork-aware update status retained only the still-missing canonical-remote selector and cache migration while composing upstream's exact GitHub compare counts, local-ahead handling, and SSH-safe checks.

## Catalogue

- Reconciled all retained active rows and report headers to the rebased commit identities while preserving earlier refs as lineage.
- Marked provider retry output caps historical and documented why it was dropped.
- Final active catalogue: 29 rows and 36 active source refs.
- Mechanical validation confirmed every active ref is in the candidate history, every linked report exists, and every active ref appears in its report.

## Verification

- Canonical changed-area Python suite after the drop: 39 files, 1,427 passed, 4 skipped, 0 failed.
- Dropped-patch transport regression set: 51 passed, 0 failed.
- TUI `check`: Ink build and TypeScript passed; 160 files / 1,715 tests passed with 1 skipped; lint had 0 errors and 2 upstream warnings.
- Desktop typecheck and lint passed; lint had 0 errors and 117 upstream warnings. Desktop Vitest passed 686 files with 1 skipped and 7,100 tests with 3 skipped.
- Ruff passed across the candidate-changed Python set; one pre-existing malformed-`noqa` warning remains in `run_agent.py`.
- `git diff --check`: passed.
- The candidate-only venv required the lock-defined `agent-client-protocol==0.9.0` and `hindsight-client==0.6.1` extras before the canonical Python run; after installation, the full changed-area suite passed.
- `npm ci --include=dev` used the repository lockfile with `NODE_ENV=test`; npm audit reported six high-severity dependency findings without changing dependencies or the lockfile.

## Publication gate

Freeze the final candidate, verify upstream has not advanced, obtain an independent read-only review of the immutable range-diff/conflict resolutions/drop/catalogue, then compare the fork ref with the frozen lease baseline and publish only with explicit expected-object `--force-with-lease`. Any mismatch aborts publication.

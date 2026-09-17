# 2026-08-14 Hermes patch-stack rebase

## Scope

- Canonical fork branch: `peter/hermes-patches`
- Preserved pre-rebase fork tip: `baff1e8f845447f50be1c3cd9d5b6c28479ec928`
- Recovery ref: `recovery/hermes-update-remote-pre-rebase-20260814T134439Z`
- Pre-rebase upstream base: `2446c8bb6755ff5e6feff4d26e425661edd4019b`
- Final upstream base: `c896c09c42910c584c4c7d2325b58c14713ea42c`
- Candidate branch: `update/hermes-patches-20260814T134439Z`
- Source-stack tip before this report: `cd1dedba11297eee08c9ad3ab7faa23a52c902bc`

The rebase ran in `/home/kidroca/.hermes/worktrees/hermes-update-20260814T134439Z`; the live checkout at `/opt/hermes-agent`, its venv, and the fork branch were not modified.

## Patch decisions

The source-stack range-diff maps 69 of 71 old commits onto the candidate:

- 54 commits are patch-identical (`=`).
- 15 commits are adapted (`!`) to current upstream structure.
- 2 source commits disappeared (`<`) because upstream now provides their behavior.
- No unexplained source or documentation commit was added (`>`).

Dropped patches:

- `1369da7563` — the provider-local current-turn Hindsight recall strategy is superseded by upstream `34c727c5c2`, which provides current-turn recall through the current `recall_sync` architecture and tests.
- `2f4203b7b8` — the local query-timing names only configured the dropped strategy and no longer fit the upstream `recall_sync` architecture. The retained generic latency policy remains `memory.external_prefetch_timeout_seconds`.

Materially adapted patches:

- `0c77b22982` → `b7edc3f88e` — preserve browser/CDP contracts across upstream browser refactoring.
- `a0006f51a2` → `b7243c4db6` and `01d82afd79` → `75377f5cfd` — retain Hindsight source labels and empty-prefetch bootstrap behavior in upstream's synchronous recall path.
- `6bfadc1e6c` → `dd5d9162c6` — preserve Slack memory notices alongside upstream task-card progress queues.
- `1c8431de0a` → `8f6f1307cc` and `3c7407e0d9` → `4bb58c22fc` — preserve Kanban profile isolation and worker memory defaults across upstream review-dispatch and turn-context changes.
- `2e4fce9b45` → `66215c0229`, `ac4e5f5aa8` → `ca0179ec67`, and `f120632b37` → `dc959bb70f` — retain failed-retain notices, short-input gating, and prior-prefetch consumption in the new recall architecture.
- `3cf6f6d9c1` → `d7aa5bf32f` — retain explicit Hindsight retain previews across display changes.
- `4506407813` → `c32a7f34ad` — preserve the configured preview budget while retaining upstream's full tool-argument payload.
- `59a62b3ba4` → `6e39c6976b` — preserve authored-only Slack recall queries alongside upstream internal-notification persistence fields.
- `02e84d55ad` → `87d27ae8a0` — move the external-memory deadline to the generic manager while leaving Hindsight's internal join unbounded inside that bounded worker.
- `d6271418fd` → `d352c1028b` — retain Git-project bank routing across upstream provider constructor changes.
- `ef0ebcddbc` → `0cd6064d68` — reconcile the earlier patch-stack integration commit with the new base.

## Catalogue reconciliation

- Updated all 29 retained active rows and their linked report headers to the 2026-08-14 refs.
- Preserved pre-rebase and reviewed SHAs as lineage.
- Marked the two superseded Hindsight reports historical and named upstream `34c727c5c2` as the replacement.
- Recorded 36 final active source refs; mechanical ancestry and report-link validation are publication gates.

## Verification

Final source-tree evidence before this documentation-only report commit:

- Conflict-focused Hindsight, Slack, Kanban, TUI gateway, and memory-manager runs: all passed; the focused batches covered 809 tests with 3 skips.
- All 38 candidate-changed Python test files through the canonical isolated runner: 1,385 passed, 4 skipped, 0 failed. The first attempt was discarded after exposing a missing lock-defined ACP extra; `agent-client-protocol==0.9.0` was installed in the candidate-only venv and the entire changed-area set was rerun.
- TUI Ink build: passed.
- TUI TypeScript check: passed.
- TUI Vitest: 141 files passed; 1,555 tests passed and 1 skipped.
- TUI ESLint: 0 errors and 1 warning in unchanged `src/app/useSessionLifecycle.ts`.
- Ruff across all 75 candidate-changed Python files: passed, with one existing malformed-`noqa` warning in `run_agent.py`.
- `git diff --check`: passed.

`npm ci --include=dev` used the repository lockfile with `NODE_ENV=test`. Its audit summary reported six high-severity dependency findings; this preparation did not alter dependency versions or the lockfile.

## Review and publication gates

The candidate must remain immutable while an independent reviewer audits all `!` mappings, both dropped patches, conflict resolutions, and this catalogue reconciliation. Any blocker requires a fix, affected-gate rerun, and review of the revised final diff.

Publication, if separately approved, must use an explicit lease against `baff1e8f845447f50be1c3cd9d5b6c28479ec928`; an unguarded force push is forbidden.

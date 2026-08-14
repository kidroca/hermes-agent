# 2026-08-14 Hermes patch-stack publication refresh

## Scope

- Fork lease baseline: `baff1e8f845447f50be1c3cd9d5b6c28479ec928`
- Recovery ref: `recovery/hermes-update-remote-pre-publish-20260814T192746Z`
- Previously verified candidate: `618ae7895882022dbcc691a05e13e825430a90ce`
- Previous upstream base: `c896c09c42910c584c4c7d2325b58c14713ea42c`
- Refreshed upstream base: `a90d5369f76c87c98547d2e283aa26d5cfabf322`
- Publication candidate: `update/hermes-patches-publish-20260814T192746Z`

The refresh ran in an isolated worktree. The live checkout, its venv, and `peter/hermes-patches` remained untouched.

## Refresh result

The previously verified 70-commit candidate rebased cleanly over the 12 newer upstream commits. Range-diff classified all 70 commits as patch-identical (`=`), with no adapted, disappeared, or unexplained commits.

The missing fork-aware update-status patch was then integrated:

- `feb00ce956` → `b74ce0fb60` — compare fork installations against the configured canonical NousResearch remote.
- `6f65410573` → `d18af41ecf` — add and reconcile its patch-catalog entry.

The patch restores canonical upstream distance and carried-commit reporting for fork installations while retaining official-install, shallow-clone, SSH, fallback, and cache-invalidation behavior.

## Catalogue

- Refreshed all 29 previously retained active rows and report headers to the new rebased commit identities.
- Added the fork-aware status row, resulting in 30 active rows and 37 active source refs.
- Preserved earlier refs as lineage.
- Mechanical validation confirmed every active ref resolves, is an ancestor of the candidate, appears in its linked report, and every report link exists.

## Verification

- Fork-aware focused set: 56 passed across five files.
- All 40 candidate-changed Python test files: 1,392 passed, 4 skipped, 0 failed.
- Ruff across 78 candidate-changed Python files: passed; one pre-existing malformed-`noqa` warning remains in `run_agent.py`.
- `git diff --check`: passed.
- The prior candidate's TUI verification remains applicable: the refresh range-diff is patch-identical and the 12 upstream commits changed no `ui-tui` path. That prior gate passed the Ink build, TypeScript check, 1,555 tests with 1 skip, and lint with one warning in an unchanged upstream file.
- The seven live Hindsight profile configurations were already migrated and mechanically validated with `auto_recall: false`, `recall_sync: true`, and no legacy query strategy/wait keys.

## Publication gate

Publication must compare the live fork ref with the frozen lease baseline and use an explicit expected-object `--force-with-lease`. Any mismatch stops publication without weakening the lease or overwriting remote work. The live update command must not be shown until `git ls-remote` confirms the fork branch equals the exact candidate SHA.

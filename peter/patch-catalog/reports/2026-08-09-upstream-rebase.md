# 2026-08-09 Hermes patch-stack rebase

## Scope

- Canonical fork branch: `peter/hermes-patches`
- Preserved pre-rebase fork tip: `b261576d0108e31768cdb3e3b777af8b59a8d10c`
- Recovery ref: `recovery/hermes-update-remote-pre-rebase-20260809T114817Z`
- Pre-rebase upstream base: `fe6330de035c27f64c356a819a2218ee1cb05e93`
- Final upstream base: `2446c8bb6755ff5e6feff4d26e425661edd4019b`
- Candidate branch: `update/hermes-patches-20260809T114817Z`
- Source-stack tip before this report: `36c43a9813e02e43b6b5ed51bfcf58561c3b419c`

The rebase ran in `/home/kidroca/.hermes/worktrees/hermes-update-20260809T114817Z`; the live checkout at `/opt/hermes-agent` was not rebased or modified.

## Patch decisions

The source-stack range-diff, ending at `36c43a9813`, maps all 70 old commits to 70 candidate commits:

- 62 commits are patch-identical (`=`).
- 8 commits are adapted (`!`) to current upstream structure.
- No pre-existing source or documentation commit disappeared (`<`) or was added outside the old stack (`>`).
- No active local source patch is fully superseded by upstream; all 31 active catalogue rows remain retained.

This report and the reconciled catalogue are committed afterward as one deliberate 71st, documentation-only commit.

Adapted source commits:

- `a547eaa832` — preserve SSH tar metadata safeguards across upstream import changes.
- `0e7f68a806` — preserve session-database warnings while retaining upstream reattachment behavior.
- `3c7407e0d9` — preserve the Kanban memory-autoprefetch default across turn-context changes.
- `4506407813` — retain configurable TUI tool previews through the current session-history path.
- `59a62b3ba4` — retain Slack recall-query isolation through upstream thread-context handling.
- `47f6724134` — preserve explicit per-platform Kanban opt-in through toolset refactors.
- `94bb2d8215` — retain bounded Doctor state checks and accept both valid SQLite corruption diagnostics.
- `ef0ebcddbc` — reconcile the earlier patch-stack integration commit with current upstream files.

The high-overlap upstream proposals remain open rather than merged, including PRs `#58957`, `#64510`, `#62210`, `#73975`, `#62687`, `#26323`, `#42320`, `#60716`, `#31743`, `#28719`, `#29865`, `#18372`, `#43998`, `#42232`, and `#68047`.

## Catalogue reconciliation

- Updated all 31 active index rows and their report headers.
- Preserved historical/pre-rebase SHAs as lineage.
- Recorded 38 final active source refs.
- Mechanical validation confirmed every active ref belongs to `upstream/main..HEAD` and appears in its linked report.

## Verification

Final-tree checks after the second rebase onto `2446c8bb67`:

- Git ancestry at the source-stack tip: `upstream/main` is the exact merge base; divergence is `0` upstream / `70` source-stack commits. The final candidate adds this documentation-only commit.
- Source-stack range-diff: 70 mapped, 8 adapted, 0 disappeared, 0 added.
- Python changed/conflict areas: 808 passed, 0 failed.
- Project-tree and Hindsight project-bank coverage: 144 passed, 0 failed.
- TUI Ink build: passed.
- TUI TypeScript check: passed.
- TUI Vitest: 140 files passed; 1,552 tests passed and 1 skipped.
- ESLint across all 16 candidate-changed TUI files: no issues.
- Ruff across all candidate-changed Python files: passed.
- `git diff --check`: passed.

The repository-wide TUI lint command still reports five errors and four warnings in five files that are byte-identical to `upstream/main`; candidate-changed files are clean. A broad Python run was discarded as invalid evidence after a read-only reviewer changed the shared test environment while it was running; focused final-tree verification above was rerun in isolation.

## Review and publication gates

Independent supersession and catalogue audits found no patch to drop. The first semantic review found that upstream had advanced by five commits during the initial conflict-resolution run; the later autosquash rebased the full stack onto that newer tip and resolved the blocker. Final immutable-candidate review is the next gate after this report commit.

Publication must use an explicit lease against `b261576d0108e31768cdb3e3b777af8b59a8d10c`; an unguarded force push is forbidden.

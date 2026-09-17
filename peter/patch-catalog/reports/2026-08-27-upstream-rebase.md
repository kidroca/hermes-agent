# 2026-08-27 Hermes patch-stack rebase

## Scope

- Canonical fork branch: `peter/hermes-patches`
- Preserved pre-rebase fork tip: `de3d81f0519fe2e24d4c65f74531d98762fa56d2`
- Recovery ref: `recovery/hermes-update-remote-pre-rebase-20260827T092954Z`
- Previous upstream tracking tip: `6defe7eb6c462bb784d1f27f5afe7ca4b627fc70`
- Previous patch-stack base: `b766607b5b92879c21ffd767465487e6de725868`
- Initial captured canonical upstream base: `ca753b96cbc7d808280e2e6644e42e73ea067800`
- Intermediate refreshed canonical upstream base: `beb212dcc5444f629a84ce0d64ac332f958a0e06`
- Final refreshed canonical upstream base: `a9611f3c6f7ff287a4f10f71a77d7c5a808ea1c8`
- Candidate branch: `update/hermes-patches-20260827T092954Z`
- Source candidate before this report: `fad37e95363af6b148431591a50a2980d78ec416`

The rebase ran in an isolated worktree. The live checkout at `/opt/hermes-agent`, its venv, and the checked-out fork branch remained untouched.

## Patch decisions

The source-stack range-diff against the previous 75-commit stack classifies:

- 66 commits as patch-identical (`=`).
- 9 commits as adapted (`!`) to current upstream structure.
- No source patches as dropped (`<`).
- 1 intentional corrective source follow-up as added (`>`).

Canonical upstream first advanced by two unrelated commits during verification, then advanced by another 24 commits including browser timeout/session recycling that overlapped the stack's browser-tool surface. The complete candidate was refreshed at both boundaries patch-identically with no conflicts (`75 =` for the source stack; the second refresh also carried this report commit unchanged) before the catalogue was finalized.

Materially adapted patches:

- `edb594933a` → `6db7a6f887`: retained local CDP auto-launch and reachability semantics without restoring upstream's removed browser-snapshot extraction-model path.
- `ecb85ddccd` → `0eefbc09fd`: composed the fresh-bundle npm/build skip with upstream's stronger workspace lock-closure check and updated the launch behavior test.
- `c27bea8e6c` → `85da84a62b`: retained TUI SessionDB recovery/warning behavior while preserving upstream's fail-closed named-profile DB-open contract.
- `f52f4728a2` → `18e8cd7cde`, `2c83289366` → `599014f6be`, `98570a1f22` → `84cf96a4e6`, and `66bd3cd05f` → `d4ab176e98`: context-only reconciliations across upstream import and turn-lifecycle changes; local semantics remain intact.
- `856adb686c` → `a7b734af6d`: retained bounded shallow/deep Doctor checks alongside upstream's exclusive repair guard and snapshot helpers.
- `d853c44128` → `bf070c09f9`: combined the fork-aware cache schema with upstream's no-cache-on-fetch-failure behavior.
- `fad37e9536`: independent review found that the failed-fetch stale-ref fallback still hardcoded `origin/main`; the corrective follow-up uses the already selected canonical remote and adds a fork-specific regression test.

## Catalogue

- Reconciled all 29 retained active rows and report headers to the rebased commit identities while preserving earlier refs as lineage.
- No active patch family was dropped or retired.
- Mechanical validation of active refs and linked reports is part of the final verification gate below.

## Verification

- Canonical changed-area Python suite: 39 files, 1,554 passed, 11 skipped, 0 failed. The final run used eight workers and completed without the one-second thread-starvation retry seen under the host's default 40-worker saturation.
- Final-refresh browser, hook, cron, model, and plugin overlap suite: 10 files, 223 passed, 0 failed.
- Ruff passed across all 75 candidate-changed Python files; one pre-existing malformed-`noqa` warning remains in `run_agent.py`.
- Root `npm run check` passed across every workspace: TUI 160 files / 1,721 tests; desktop UI 617 files / 6,078 tests; desktop Electron 133 files and 1,934 tests passed with 2 files / 6 tests skipped; web 36 files / 278 tests; JavaScript integration 7 files / 38 tests. Typechecks, builds, plugin checks, and lint completed with no errors; upstream warnings remain.
- Candidate-only `npm ci --include=dev` used the repository lockfile with `NODE_ENV=test`; npm audit reported two high-severity dependency findings without changing dependencies or the lockfile.
- Independent review's only blocker was the fork failed-fetch fallback; the corrective follow-up passed 15 focused banner/update tests and Ruff.
- Catalogue validation confirmed 29 active rows and 37 active refs; every active ref is in candidate history, every linked report exists, and every active ref appears in its report.
- Source range-diff: 66 patch-identical, 9 intentionally adapted, 0 dropped, and 1 reviewed corrective addition. The two-commit and subsequent 24-commit upstream refreshes were patch-identical across the full pre-review candidate.
- `git diff --check`: passed.

## Publication gate

Freeze the final candidate, verify canonical upstream has not materially changed from the final refreshed base, obtain an independent read-only review of the immutable range-diff and conflict resolutions, then compare the fork ref with the frozen lease baseline and publish only with explicit expected-object `--force-with-lease`. Any mismatch aborts publication.

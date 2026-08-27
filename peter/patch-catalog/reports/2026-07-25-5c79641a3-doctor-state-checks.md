# Bound Doctor state checks and harden FTS verification

- Date: 2026-07-25
- Repo: `/opt/hermes-agent`
- Patch ref: original `5c79641a3`; reviewed rebase `3ddcb19a6` → `3369b6147` (pre-2026-08-09 active) → `94bb2d8215` (pre-2026-08-14 active) → `efc0fad22b` (pre-refresh active) → `26e282bc8c` (pre-2026-08-23 active) → `079a4c7da2` (pre-final-refresh active) → `856adb686c` (pre-2026-08-27 active) → `a7b734af6d` (pre-final-refresh active) → `92092c5137` (pre-final-refresh-2 active) → `04fee974fd` (active)
- Branch: `peter/hermes-patches`
- Local status: rebased onto `main` on 2026-07-25 with upstream schema-v23 overlap removed
- Motivation: keep one canonical searchable session database while preventing routine `hermes doctor` runs from scanning the entire multi-gigabyte store.
- Changed files: `hermes_cli/doctor.py`, `hermes_cli/subcommands/doctor.py`, `hermes_state.py`, `tests/test_state_db_malformed_repair.py`, `tests/hermes_cli/test_doctor_deep.py`, `website/docs/reference/cli-commands.md`
- Tests / verification: original patch: `486 passed, 1 warning`; `git diff --check`; two read-only side-worker reviews (first found writable shallow connections, fixed with SQLite `mode=ro`; final review found no issues). Live routine Doctor completed in **4.52 s** and explicitly reported that deep verification was skipped. Rebase verification: `2120 passed` across the conflict-sensitive Python suites; UI build plus `176 passed`; TypeScript `tsc --noEmit`; `git diff --check`.

## Local patch summary

Routine Doctor now performs only read-only schema/canonical-table checks and never runs `PRAGMA integrity_check`, FTS integrity commands, or synthetic trigger writes. `hermes doctor --deep` creates a point-in-time SQLite backup in the system temporary directory, runs full SQLite and FTS5 inverted-index checks against that stable snapshot, and deletes the snapshot afterward.

The 2026-07-25 rebase deliberately dropped the original patch's legacy-inline
repair implementation and FTS trigger rewrites. Upstream schema-v23 now owns
the FTS layout, deferred rebuild bookkeeping, opt-in legacy migration, CJK
index handling, and repair strategy; carrying the older local implementation
would have created a mixed and unsafe schema path.

Doctor also warns when the linked SQLite falls in the documented multi-process
WAL-reset corruption range, using upstream's canonical runtime classifier.

No sessions are archived, split, or deleted. Search remains against the single canonical `state.db`.

## Upstream overlap

- Updated `main` still performs the full state probe during routine Doctor, so
  the bounded default and explicit `--deep` mode remain local.
- Upstream `17bf3c828` and `953cbc030` (plus successors) now own managed-runtime
  repair and WAL-reset protection; the rebase retained those implementations.
- Upstream `9acc4b47f` and its schema-v23 successors now own FTS storage,
  migration, trigger, CJK, and repair behavior; the overlapping local code was
  dropped during rebase.

## Recommendation

Keep only the bounded routine Doctor and snapshot-based `--deep` behavior
locally until upstream adopts an equivalent mode. Continue using upstream's
SQLite runtime, FTS schema, migration, trigger, and repair implementations.

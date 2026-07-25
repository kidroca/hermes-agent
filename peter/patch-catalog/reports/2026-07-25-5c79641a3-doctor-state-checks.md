# Bound Doctor state checks and harden FTS verification

- Date: 2026-07-25
- Repo: `/opt/hermes-agent`
- Patch ref: `5c79641a34664e261273df40849022b51d2c8ded`
- Branch: `peter/hermes-patches`
- Local status: source patch committed as `5c79641a3`; catalogue update follows separately
- Motivation: keep one canonical searchable session database while preventing routine `hermes doctor` runs from scanning the entire multi-gigabyte store.
- Changed files: `hermes_cli/doctor.py`, `hermes_cli/subcommands/doctor.py`, `hermes_state.py`, `tests/test_state_db_malformed_repair.py`, `tests/hermes_cli/test_doctor_deep.py`, `website/docs/reference/cli-commands.md`
- Tests / verification: `486 passed, 1 warning`; `git diff --check`; two read-only side-worker reviews (first found writable shallow connections, fixed with SQLite `mode=ro`; final review found no issues). Live routine Doctor completed in **4.52 s** and explicitly reported that deep verification was skipped.

## Local patch summary

Routine Doctor now performs only read-only schema/canonical-table checks and never runs `PRAGMA integrity_check`, FTS integrity commands, or synthetic trigger writes. `hermes doctor --deep` creates a point-in-time SQLite backup in the system temporary directory, runs full SQLite and FTS5 inverted-index checks against that stable snapshot, and deletes the snapshot afterward.

The repair path now distinguishes external-content FTS tables from legacy inline tables. External-content indexes use FTS5 `rebuild`; inline indexes are transactionally recreated and repopulated from canonical `messages` rows under one exclusive transaction. Existing unconditional FTS update triggers are narrowed to indexed columns so metadata-only compaction/status updates do not rewrite both indexes.

Doctor also warns when the linked SQLite falls in the documented multi-process WAL-reset corruption range. The active runtime links SQLite 3.50.4, which is vulnerable; this warning is intentionally non-fatal because replacing the running interpreter is a separate operational change.

No sessions are archived, split, or deleted. Search remains against the single canonical `state.db`.

## Upstream overlap

- Upstream `origin/main` still calls the full state probe from routine Doctor, so updating alone does not replace the bounded/default-vs-deep behavior.
- Upstream commit `17bf3c828` adds managed-runtime repair for vulnerable SQLite builds. Prefer that upstream runtime mechanism rather than carrying a second local interpreter-cutover implementation.
- Upstream commit `9acc4b47f` introduces schema-v23 external-content, tool-row-free FTS storage optimization and `hermes sessions optimize-storage`. It substantially overlaps the local legacy-inline repair/trigger code and should be reconciled carefully on rebase.
- Upstream WAL-reset protection work (`953cbc030` and successors) overlaps the local warning helper and should supersede it once this branch reaches those commits.

## Recommendation

Keep the bounded Doctor behavior locally until upstream adopts an equivalent opt-in deep mode. Rebase carefully around schema-v23 FTS work and drop local overlap where upstream semantics are equivalent. Separately upgrade the managed Python runtime to a fixed SQLite release, then rebuild and deep-verify FTS before treating the live trigram index as durable.
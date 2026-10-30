# Close pre-agent cron fires without ghost picker sessions

Date: 2026-10-30. Source: `40dcfd5a5110dbb9fee874cbc3c79acbcaa2f24a`.
Base: `b6ffe5f6fc32` (abbreviated runtime receipt).

## Scope and cause

Canonical cron admission creates the session before script/prompt gating. Early
skip, error, cancellation or exception paths could return before agent-owned
session finalization, leaving empty rows open and visible in the human picker.
This is lifecycle/presentation cleanup, not a model change or removal of durable
cron admission history.

Production diff: **28 additions / 2 deletions across three files**:

- `cron/scheduler.py`: finalize admitted pre-agent returns/exceptions; move the
  agent import inside guarded setup and cover setup failure before a session DB
  is acquired.
- `gateway/session_cron.py`: `finish_pre_agent` uses the bounded cron DB view to
  set a title and end the canonical session as `cron_skipped` or `cron_error`,
  without closing the authority-owned DB.
- `gateway/session_listing.py`: omit ended, empty cron lineages from stored
  picker results; preserve pending cron, real cron conversation and non-cron
  entries. Both root and tip must be empty.

Empty gate-fire persistence **remains for deduplication and audit**. The contract
is no empty completed cron entry in the user picker, not zero database rows;
no synthetic conversation turns are created and admission receipts survive.

## Verification and review

Execution receipts supplied by the parent (not rerun by this documentation worker):

- TDD baseline: all **six regression cases RED** before the fix.
- New `tests/gateway/test_cron_gate_session_lifecycle.py`: 111 lines covering
  skip/error/cancelled/exception closure, the real `wakeAgent: false` admission
  and terminal receipt/idempotent resubmission path, and picker controls.
- Canonical checkout: **77 passed, zero failed across 13 files**.
- `scripts/check --commit HEAD --base HEAD^`: **all 12 checks passed**.
- Independent tool-free review of the supplied complete production diff and
  test contracts: **no concrete blockers**. Optional metadata-write-failure
  masking, additional setup-failure cases and a compression-tip regression were
  deferred; no current normal-path issue was identified. This was not an
  independent execution receipt.

## Approved historical cleanup

Parent live receipts identified **635** proven Todoist AI-review skips for job
`fd7e3e29142d`: zero canonical messages, zero API calls, all admissions terminal
completed, and saved `wakeAgent: false` results. Only this proven cohort was
ended as `cron_skipped` with a generation bump. **Zero deletes**; receipts were
unchanged. On the backup canary, full message/admission/state_meta fingerprints
were unchanged, as were session fields other than end metadata. Live cleanup
readback verified the target rows and preserved receipts; live `session.list`:
nine rows, zero Luna entries.

A WAL-consistent backup passed SQLite quick-check before cleanup:
`~/.hermes/backups/cron-ghost-20261030/before-cleanup.db`.
SHA-256: `e82bb16f52fba4fc45f03857c088107ad82bb570376e4c776a6fa5293f25980e`.
No secrets or transcripts are included here.

The culprit job was paused through the CLI. Its `gpt-5.6-luna` model is unchanged
pending user discussion. The separate script-only ten-minute sync is unchanged;
print monitors remain disabled.

## Integration is not activation

Peter approved the fix and live activation. Canonical `/opt/hermes-agent`, branch
`peter/hermes-patches`, fast-forwarded to `40dcfd5a51`. Peter subsequently approved
publication of the five outgoing commits to `origin/peter/hermes-patches`, plus
this catalogue-disposition update; no upstream PR was requested.
The gateway tool guard blocked restart from inside the gateway. The latest
parent receipt still reports PID **3072054**, code SHA **`b6ffe5f6fc32`**:
**the fix is integrated, not verified loaded**.

An external-shell gateway restart is required, followed by a new PID/loaded-SHA
readback and picker/lifecycle verification. Do not present historical cleanup
or passing source tests as runtime activation.

## Upstream disposition

Parent-supplied read-only research used four authenticated searches and direct
metadata/diff follow-up on three PRs. All three were **open, unmerged**
(`merged_at: null`); presence on current upstream main was not verified:

- [#143808](https://github.com/NousResearch/hermes-agent/pull/143808)
  (created/updated October 24): closest duplicate; `run_job` gate/blocked setup
  calls `session_cron.finish_pre_agent_run`, borrowing the DB and ending as
  `cron_skipped` / `cron_preflight_failed`, with tests but no title/picker fix.
  **High same-hunk overlap.**
- [#145135](https://github.com/NousResearch/hermes-agent/pull/145135)
  (created/updated October 26): execute-time `tracked_write` closes zero-message,
  unended sessions as `cron_skipped` plus `hidden=True`. Earlier closure by this
  local patch would skip that helper's hiding: **semantic conflict**, without a
  distinct failed-preflight reason.
- [#143562](https://github.com/NousResearch/hermes-agent/pull/143562)
  (created October 23, updated October 29): gate before admission, return a direct
  terminal response / `prepared_prompt`, and avoid the durable row entirely;
  three source and two test files. **High architectural and hunk overlap**;
  durable receipt semantics need explicit reconciliation.
- [Issue #145314](https://github.com/NousResearch/hermes-agent/issues/145314)
  (created October 27, updated October 28): same permanent empty quiet-cron
  symptom, **search metadata only**, not a directly inspected issue body.

No merge-likelihood claim or upstream-publication request. Drop or reconcile the local
patch when equivalent upstream behavior is adopted, verifying lifecycle,
picker visibility and durable-receipt contracts rather than stacking competing
finalizers blindly. Peter has been asked to run external WSL `hermes gateway restart`;
no restart has yet been verified.

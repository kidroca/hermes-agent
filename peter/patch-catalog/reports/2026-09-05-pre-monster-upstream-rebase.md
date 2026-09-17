# Pre-monster upstream rebase — 2026-09-05

- Repository: `NousResearch/hermes-agent`
- Branch: `update/hermes-patches-pre-monster-20260904T215242Z`
- Previous upstream base: `38b7d0f4cf8a11137d8da5e3d95d7b5b7e41fb46`
- Previous patch tip: `4ad8a5a30915a7b430e61be5d36ab722301adb8d`
- New upstream target: `63279301bcbdc185c1b07b98a9312eb0c862f26d`
- Excluded monster merge: `d3630f853239e8c41ce7201e09fbdf39bcbc5431` (PR #102117)
- Candidate patch tip before this report: `1935f68ea25f08d4c0c497757393163f6eccbeca`
- Status: verified and independently reviewed; ready for guarded publication

## Scope and safety gate

The update deliberately stops at the first parent of PR #102117. Git ancestry checks confirm that `63279301bcbdc185c1b07b98a9312eb0c862f26d` is an ancestor of the candidate and that monster merge `d3630f853239e8c41ce7201e09fbdf39bcbc5431` is not.

The bounded old-base-to-target blast-radius check covered 1,203 commits (1,124 first-parent), 1,682 files, 124,572 additions, and 59,817 deletions over 73.68 hours. The largest individual first-parent landing changed 118 files and 16,611 lines with seven side commits; the largest 72-hour edge window changed 1,676 files and 182,353 lines. Those values passed the workflow gate. The excluded PR #102117 was the abnormal event that triggered the pause and explicit pre-event target.

## Rebase outcome

The old stack contained 78 commits. The candidate also contains 78 commits: 66 patch-equivalent entries, 11 context-adapted entries, one deliberate drop, and one new corrective commit according to `git range-diff`.

### Deliberate drop

- `7e88edde68` — `fix: ring TUI bell on approval prompts`
  - Dropped because upstream `552159d222` provides the broader configurable `display.bell_on_prompt` path for clarify, approval, sudo, and secret prompts.
  - Upstream `632078bca7` additionally provides OSC 9/Warp notifications on the same alert flags.
  - Both upstream commits are included in the selected target.

### Corrective commit

- `1935f68ea2` — `fix(cli): avoid duplicate approval prompt bell`
  - Removes a redundant legacy helper left by the automatic rebase beside upstream's unified `_ring_bell` path.
  - Strengthens the approval regression test from “a BEL occurred” to “exactly one BEL occurred.”

### Context-adapted entries

- `b616ed07b5` → `0ef5268519`: TUI session-DB recovery composed with upstream changes.
- `269d04e78b` → `b0e2810921`: TUI memory-context display composed with upstream event changes.
- `efece3df9c` → `f305b88f10`: Slack memory notices retained alongside upstream executor-quiesce handling.
- `bee4d8d7a3` → `b79c8b4678`: Kanban worker memory defaults retained alongside upstream restart-safe worker arguments.
- `6a513467f6` → `dc7f9ad363`: short-input recall gate rebased over upstream Hindsight lifecycle changes.
- `0c2db8b397` → `f0a7b34e30`: retain preview rebased over upstream display changes.
- `17930897d1` → `477015f083`: separate Slack recall-query context retained while composing upstream platform-ID persistence and compression preflight handling.
- `e72bb10508` → `8dc731583e`: bounded Doctor checks composed with upstream state-store changes.
- `c19602270e` → `91a681cfc2`: prior rebase reconciliation retained. A redundant legacy approval-BEL helper that survived beside upstream's unified notifier was removed in corrective commit `1935f68ea2`; its regression test now requires exactly one BEL.
- `f965496f8c` → `1d9fe7129f`: Git-project bank routing composed with upstream memory changes.
- `894a9ab51c` → `1338e943d5`: canonical-upstream comparison combined with upstream noninteractive Git environment handling.

All remaining entries are patch-equivalent in the range-diff. The active catalogue and each active family report now preserve the previous ref as `pre-2026-09-05 active` and point to the corresponding rebased ref.

## Verification

Focused checks executed during conflict resolution:

- Slack memory-context display: 7 passed.
- Kanban worker spawn/turn-context/memory-provider checks: 31 passed.
- Slack recall-query composition: 23 turn-context, 1 finalization, 2 interruption, 237 Slack, 4 duplicate-user, 2 queue, and 5 steer tests passed; the Slack run emitted seven existing unawaited-`AsyncMock` warnings.
- Prior-reconciliation areas: terminal notifications 2, approval UI 18, clarify batching 13, Kanban spawn 4, TUI memory context 2, exact TUI gateway checks 2, browser/CDP 20, and Slack 237 passed; the Slack run emitted the same seven warnings.
- Fork-aware update/banner checks: 15 passed.
- Approval/clarify/terminal-notification checks after the duplicate-BEL correction: 33 passed.
- Final changed-area Python gate: all 39 changed test files passed — 1,609 passed, 10 skipped, 0 failed — with eight workers and isolated `HOME`/`HERMES_HOME`.
- Ruff passed across all 74 changed Python files; it emitted one non-blocking invalid-`noqa` warning at `run_agent.py:153`. `git diff --check` also passed.
- Repository-level `npm run check` completed the Desktop UI, Electron, JavaScript, build, typecheck, and lint gates. The TUI test leg reported 22 failures; the one backpressure failure passed on focused rerun, while the remaining 21 failures reproduced identically on this candidate and the exact upstream target in two files unchanged by the patch stack (`subscriptionOverlay.test.tsx` and `appChromeBlockedTimers.test.tsx`).
- A repository-wide Python run was not green under maximum parallelism. Its transient compression, session-hygiene, quickstart, stage-2 keygen, Termux, process-registry, and TUI-gateway failures passed on isolated or sanitized reruns. Ten deterministic non-update failures reproduced on the exact upstream target, and one representative failure from each affected update-test file (`test_update_head_moved_gate.py`, `test_update_yes_flag.py`, and `test_cmd_update.py`) also reproduced there; those update failures hit the live-gateway safety guard rather than a patch-stack assertion.
- Independent semantic review of source tip `1935f68ea2` found no blocking or non-blocking findings across all 11 adapted mappings, the upstream bell replacement, and the duplicate-BEL correction.
- Independent catalogue review of documentation commit `b9692f031c` verified all counts, refs, linked reports, ancestry, the one drop, and the corrective commit with verdict **READY**.

The broad-suite failures above are upstream-baseline or host/test-environment failures, not candidate-only regressions. All candidate-specific publication gates passed.

## Publication guard

Publication must use `--force-with-lease` against the frozen old remote tip `4ad8a5a30915a7b430e61be5d36ab722301adb8d`. The live checkout is not switched or updated by this candidate workflow; publication and live activation are separate operations.

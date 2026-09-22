# 2026-09-22 upstream rebase catalogue reconciliation

- Date: 2026-09-22
- Repo: `/home/kidroca/.hermes/worktrees/hermes-update-catalogue-20260922`
- Branch: `update/hermes-catalogue-20260922` (documentation integration worktree)
- Source candidate: `0769f3455b` (immutable; no source edits in this pass)
- Updated upstream base: `92dd332192`
- Old base: `691228447d`
- Recovery: `recovery/hermes-update-remote-pre-rebase-20260922T103949Z`
- Patch ref (active): `be991680f9`, `4af0015a74`, `9435889c90`, `9d8adff651`, `426c0f9258`, `c0933dc147`, `ce7b571fe6`, `388e15403d`, `d9a8d7495b`, `70b79d6498`, `727d0f8e92`, `ac070ab30e`, `dfbf559653`, `b3551b9ce0`, `054d15fd5c`, `c7e21c1950`, `1ec78b8d67`, `43dcbf1513`, `121fabf410`
- Local status: catalogue reconciled; final source verification/review runs separately.
- Motivation: retain user-valued contracts while removing obsolete duplicate architecture.
- Changed files: catalogue Markdown only; no dependency installs or source/test execution.

## Local patch summary and lineage

| Historical refs | Active refs | Contract and decision |
|---|---|---|
| `0addfd7e7a` + `321c18132a` + `208e2fcbb8` + `cdb2dfb828` + `6b1b034810` + `d9353e5ea3` | `be991680f9` + `4af0015a74` + `9435889c90` + `9d8adff651` + `426c0f9258` | Portable file-only SSH uploads: Keep pre-write validation, literal NUL manifest outside staging, POSIX remote paths and Windows containment; prompt no-sync is not a local production delta. |
| `891b4f2e54` + `5fc24844ab` + `686c6074cb` + `0d6a498c7a` | `c0933dc147` + `ce7b571fe6` + `388e15403d` + `d9a8d7495b` | ACP close, owned worker drain and runtime retirement: Reuse upstream command_op and failed-model handling; final ref is regression coverage, not a second model_lock. |
| `63eb7278a0` + `6b291310b2` + `885c83175d` | `70b79d6498` + `727d0f8e92` + `ac070ab30e` | Safe bounded shallow/deep Doctor: Keep tracked read-only connections, snapshot checks, VM deadlines and interrupt propagation. |
| `6a45562236` | `dfbf559653` | Canonical-upstream fork status and banner: Keep canonical remote selection, exact counts and comparison-aware cache. |
| `920aa29273` | `b3551b9ce0` | Dynamic Hindsight project routing, missions and notices: Retain these contracts only; retired recall/display policy stays retired. |
| `5d97cd142a` + `104bb14617` + `dc35eb4155` | `054d15fd5c` + `c7e21c1950` + `1ec78b8d67` | On-demand configured CDP launch: Keep launch and endpoint-scoped locks; retirement deferred pending explicit deployment/config switch. |
| `5b7b5b2f23` (DB recovery portion only) | `43dcbf1513` | Recover missing TUI session DB handles: Preview portion dropped by choice; finite estimates are not a local production delta. |
| `feff9231e0` | `121fabf410` | Doctor and CDP launch documentation: Keep synchronized with retained behavior. |

## Range comparison and path design

Compared exactly `691228447d..recovery/hermes-update-remote-pre-rebase-20260922T103949Z`
with `92dd332192..0769f3455b` using `git range-diff`. Equal patch identities still
receive new SHAs; all active index refs and this report header were refreshed.
Historical reports and their original test receipts remain explicitly historical.

- SSH: the old fixup `321c18132a` is folded into `be991680f9`, not a lost contract.
  `tools/environments/ssh.py` keeps remote archive names POSIX regardless of local OS,
  validates the whole batch before remote writes, and uses a file-only NUL-delimited
  manifest outside payload staging. This prevents literal-newline/option-shaped names
  and manifest-name collisions from becoming archive control data. Windows staging
  containment and rejection of unrepresentable names remain. Added GNU/BSD real-pipe
  cases are present in the diff; their presence alone is not an execution receipt.
- ACP: `acp_adapter/server.py`, `acp_adapter/session.py`, and `run_agent.py` retain
  explicit close, preserved history, compression-safe reopening, owned prompt/model
  work draining and safe replaced-runtime retirement. Upstream off-loop session
  construction and single-flight restore are reused. Duplicate persistence and
  failed-model handling are upstream-owned, not extra local fixes.
- Upstream `4987f668ae` owns state-mutating command admission (`command_op`),
  `a23984887a` owns response-before-queued-drain ordering, and
  `643b94bf9c` / `a9725ed50e` own failed-model/invalid-parameter handling.
  The local `model_lock` layer is removed. `ce7b571fe6` preserves cancellation-safe
  worker ownership: cancelled RPC callers do not release busy admission or drain the
  queue before the actual worker ends. `d9a8d7495b` is test-only coverage of upstream
  busy rejection and subsequent runtime retirement, not production serialization.
- Doctor: `hermes_cli/doctor_state.py` uses the current tracked connection owner and
  retains the retired-WAL-holder guard. Routine checks stay bounded/read-only;
  explicit deep checks use a snapshot and SQLite VM deadlines in
  `hermes_state_repair.py`, including short-walk entry/exit checks and FTS interrupt
  propagation. No live-database repair or safety-policy retirement is implied.
- Banner: `hermes_cli/banner.py` retains canonical-upstream remote selection,
  comparison-aware cache invalidation and fork-aware status/banner counts.
- Hindsight: `agent/agent_init.py`, `agent/runtime_cwd.py`, and the Hindsight provider,
  project and settings modules retain dynamic Git-common project bank routing,
  mission synchronization and demand-driven retain failure/recovery notices.
  Upstream context/platform ownership remains intact; no retired recall or debug
  display feature is reintroduced.
- Browser: `tools/browser_tool_cdp.py`, `tools/browser_camofox.py`,
  `tui_gateway/methods_browser.py` and config defaults retain configured endpoint
  compatibility, bounded first-use helper launch, canonical endpoint-scoped locks
  and stale-discovery cleanup.
- TUI: `tui_gateway/prompt_turn.py` retains only missing session DB handle recovery
  in `43dcbf1513`. Preview budget propagation is not part of this local delta.

## Explicit retirements and catalogue corrections

- User-selected retirement: `03adb5863d` and `aa12a7891d` (fast startup/workspace
  freshness and local systemd WSL PATH comparison). Neither is replayed. This is
  an explicit policy choice, not a claim that upstream is behaviorally identical.
- User-selected partial retirement: preview-budget portion of `5b7b5b2f23` dropped;
  DB recovery retained as `43dcbf1513`. Use upstream preview behavior.
- The old table's “skip prompt-probe sync” and “finite context estimates” claims
  overstate the production patch delta. There is no `agent/prompt_builder.py`
  delta in this candidate, and the retained TUI commit changes DB recovery only.
  These are catalogue corrections, not newly removed production behavior.
- Prior reduction retirements (Kanban policies, recall heuristics/provenance/debug
  displays and other historical entries) remain retired/parked. Historical keep
  recommendations do not authorize replay.
- Browser retirement is **deferred**: retain the launch patch until the replacement
  deployment path and explicit config switch are approved and verified. This
  documentation pass does not switch browser settings, remove helpers or claim a
  completed migration.

## Deployment caveat

Gateway multi-profile multiplexing is an upstream deployment change, not something
this patch catalogue enables. Before rollout, audit service topology, per-profile
home/secret/terminal scopes, child processes and deferred callbacks. Root guidance
requires real A→B→A profile-isolation verification for multiplex changes. The
bounded receipts below do not certify multiplex deployment or migrate existing
services/configuration; those checks remain with the parent rollout review.

## Tests / verification evidence boundary

Parent-provided actual bounded results **before the final base refresh**:

- ACP: 218 passed.
- Changed-area: 134 passed, 9 skipped.
- Nearby suites: 362 passed, 3 skipped.

These receipts are not attributed to the final `0769f3455b` / `92dd332192` range.
Final source verification is running separately; no final pass, full-suite result,
new platform smoke test or final independent approval is invented here. Historical
September 17 receipts apply only to their historical candidates.

This pass ran read-only Git range/diff inspection and catalogue-only verification.
See [mechanical verification receipt](2026-09-22-catalogue-verification.md).

## Upstream overlap and recommendation

No new upstream web research was performed. The local Git comparison and parent
instructions are the evidence for this reconciliation. Retain the listed contracts,
reuse upstream ownership, and keep browser retirement deferred. Parent must review
and cherry-pick this documentation commit, attach final verification separately,
and apply its publication lease/deployment gates. Nothing was pushed here.

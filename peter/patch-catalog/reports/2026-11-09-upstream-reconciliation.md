# 2026-11-09 upstream reconciliation

- Date: 2026-11-09
- Candidate branch: `update/hermes-patches-20261109`
- Reviewed source snapshot: `370cf2cc67a81270d7fed9bd4f90d96bbc7ea14c`; a later catalogue-only commit may follow.
- Old live/fork tip and frozen publication lease: `59eb40fa8d503082070778219b82df64705362ff`
- Recovery ref: `recovery/hermes-update-20261109` at that exact old tip.
- Old upstream base: `f3b5b980d6158794beb3d1044fd7b8ca4b8f0b23`
- New upstream base: `8ad89d45ac6a5da0c6b2cc641bcc12aa41ceb89b`
- Scope: isolated worktree preparation and verification, followed by guarded fork publication after the remaining gates. No live update, gateway restart, configuration migration or runtime activation is claimed.
- Active retained patch refs: `1555676d42`, `4fbb938355`, `029248e5e5`, `f536742a3e`, `fd80617053`, `bb1ab2ed2b`, `8b96c493a8`, `50e2d41660`, `7eeca3e0ec`, `c632658063`, `837340e9be`, `996bbd5d09`, `266cdb4f9e`, `ad345d8639`, `deec5144f1`, `f26abe24ec`, `8318e5a98b`, `1d0b48f427`, `f07904a942`, `680d8ffb8e`, `f62342fac0`, `0a6c1731b7`, `f8c5506019`, `8c61935a29`, `d3ef5ff94b`, `3ca6298238`.

This report and the November 9 table in `index.md` supersede all earlier active-stack claims. Earlier receipts remain historical records with their original SHAs and verification scope.

## Upstream delta and authorization

Peter explicitly authorized including the already reported large upstream delta and instructed the agent not to pause again for its size. Local Git objects show 5,586 first-parent landings from the old base, with a net delta of 6,495 files, 422,858 insertions and 137,425 deletions. The largest 72-hour window runs from November 5 08:39:58 +05:30 to November 7 19:06:57 -08:00: 1,763 first-parent commits, 2,439 distinct paths and 226,269 added/deleted lines. These counts describe the fetched snapshot, not a risk waiver for unrelated work.

The largest individual landing is Webapp-on-gateway PR #141864 (`d6b868b7ab`: 415 files, 37,467 added/deleted lines). The pnpm migration PR #149746 (`53a6ced422`: 304 files, 37,209 lines) is also material to verification setup. Upstream was checked again before final verification and still matched the frozen new base above.

## Retained and adapted patch lineage

| Family | Previous refs → active refs | Decision and preserved contract |
|---|---|---|
| Portable file-only SSH uploads | `ab77b1b0fe`, `6bef9fec10`, `625eedc9b1`, `872c5efd90`, `7ee1e480b7` → `1555676d42`, `4fbb938355`, `029248e5e5`, `f536742a3e`, `fd80617053` | Retain file-only archives, NUL manifests, POSIX remote paths, Windows staging containment and validation before remote writes. |
| Configured CDP launch | `3debae964c`, `1155511c27`, `ada56f5856` → `bb1ab2ed2b`, `8b96c493a8`, `50e2d41660` | Retain config-only bounded first-use launch, pure raw endpoint lookup, alias precedence and canonical endpoint lock identities. Configuration comments were shortened to keep the upstream file-size ratchet flat. |
| TUI database recovery | `0988d57974` → `7eeca3e0ec` | Retain recovery on the final synchronized/rebuilt agent; compose it after upstream's Daybreak synchronization. |
| External CDP activity leases | `559160ee29`, `1b64304918`, `838e2a0de8`, `f7044c220b` → `c632658063`, `837340e9be`, `996bbd5d09`, `266cdb4f9e` | Retain scoped endpoint leases, heartbeat lifetime and partial-publication cleanup. Keep upstream's current browser route/daemon ownership and reload behavior inside the lease wrapper. |
| Canonical ancestry status | `1ce79b79cb` → `ad345d8639` | Retain canonical-source ancestry reporting separately from the fork's installable-update selection. |
| External-memory notice bridge | `b656e03cfb`, `3f31c1730d` → `deec5144f1`, `f26abe24ec` | Adapt to `agent/agent_init_memory_provider.py`; retain optional structured notice/clear callbacks and upstream provider resolution/metadata. The obsolete local `agent_init_memory.py` does not remain in the final tree. |
| Doctor retirement documentation | `eb94493bc5` → `8318e5a98b` | Retain historical retirement documentation; no diagnostic implementation is restored. |
| Hindsight checkout hygiene | `e6c99cea50`, `509b3ae339` → `1d0b48f427`, `f07904a942` | Preserve original history and the root ignore rule; personal bank configuration stays local and untracked in the final tree. |
| Implicit CLI memory workspace | `bd1700f5db` → `680d8ffb8e` | Adapt to the same upstream memory helper, retaining CLI-only canonical cwd fallback without ambient gateway workspace inheritance. |
| Approval public display context | `8ac370a23e` → `f62342fac0` | Partially retain: entry-bound public context, worker scope, bound identity lookup and defensive copies remain. Discord retirement is upstream-owned; local retirement machinery is removed. |
| Linux stable session ownership | `8be151aa45` → `0a6c1731b7` | Retain boot UUID/start-tick process identity across wall-clock steps; preserve upstream's additional imports and locking changes. |
| Acknowledged SSH sync progress | `b7bef45e35` → `f8c5506019` | Retain bounded batches and acknowledged checkpoints across retries with upstream's content-confirmed sync planning. |
| ACP explicit close | `dd2f9a04c7` → `8c61935a29` | Retain per-editor prompt cancel/drain and detach without history deletion; upstream has no equivalent explicit close operation. |
| Gated cron ghost sessions | `40dcfd5a51` → `d3ef5ff94b` | Retain terminal handling before agent creation and omit only ended empty cron rows from pickers. Adapt the regression to upstream's `SessionActor` name. |
| Mounted TUI reconnect identity | `95a6b63c98` → `3ca6298238` | Adapt transport retirement to `apps/shared/src/node/gateway-client.ts`, with mounted durable-ID fallback in the TUI ready handler. Keep delayed/missing close, polling and interrupted-resume coverage without startup-prompt replay. |

## Dropped and partially superseded behavior

### Discord exact-request approvals: dropped local owner

`6ed0e4bbcd` is dropped. Upstream `cfed2ca71f` explicitly passes the request ID and `5ab58da1f6` prevents a stale card from resolving a later request. The current implementation is in `plugins/platforms/discord/adapter_exec_approval_view.py`, with `resolve_gateway_approval_card` and `observe_gateway_settle`.

The Discord portion of `8ac370a23e` is also superseded. Upstream subscribes to settlement before sending the card and buffers settlement during delivery, covering peer answers and settle-before-send/ack races. The local `adapter_exec_approval.py`, `retire_exec_approval` plumbing and Discord-only callback tests are not restored. The separate display-context contract remains in `f62342fac0`; its title still names the historical mixed patch, but its final delta is narrower. The retained effective-choice regression exercises upstream settlement logic without adding a second implementation.

Behavioral evidence: `tests/gateway/test_discord_exec_approval_content.py` covers exact IDs, stale cards and send-time settlement; `test_discord_approval_lifecycle.py` covers peer answers, terminal outcomes and click/edit/timer races. `test_approval_card_request_binding.py` covers the shared card contract.

### Shared satellite cron delivery: dropped local fix

`adbe42a737` is dropped. Upstream `01dffd3b47` supplies the equivalent `has_credential_platform` rule and `18e16bdd7d` supplies stable bot ownership. Scheduler, boot, drain, reconciliation and adapter-recovery paths already carry the behavior. Do not move that ownership back into the old local locations.

Behavioral evidence: `tests/cron/test_cron_multiplex_shared_route_delivery.py::test_multiplex_tick_routes_desktop_served_satellite_with_only_local_adapter` and `tests/gateway/test_multiplex_adapter_registry.py`. This does not supersede the separate empty gated-fire lifecycle patch.

## Conflicts and owner migrations

- `tui_gateway/prompt_turn.py`: keep upstream Daybreak sync and append the missing-store recovery after the final agent selection.
- `agent/agent_init.py` and `agent/memory_provider.py`: upstream moved initialization into `agent_init_memory_provider.py` (`e75f6675ac`). Port callbacks and CLI cwd there; keep `memory_agent_context`, parent identity and stored `resumed`/`message_count` metadata (`6b21d0564d`). Remove the obsolete helper rather than shadowing production.
- `hermes_cli/config_defaults_auxiliary.py`: upstream already extracted the same pure-data helper; keep its implementation and wording.
- Gateway/Discord approval conflicts: use upstream request binding and observer-owned settlement. Retain only the independent display-context additions in the authoritative approval entry and worker scope.
- `hermes_cli/active_sessions.py`: compose upstream threading/errno imports with the retained Linux process identity support.
- Shared satellite cron conflicts: drop the equivalent local patch rather than reinserting obsolete startup ownership wiring.
- `ui-tui/src/gatewayClient.ts`: upstream `ab334f6fdd` made this a thin wrapper. Port the transport delta to the shared client and import test timing constants from that owner; do not restore the old 978-line client.
- SSH/browser patches that applied cleanly were still compared by contract. In particular, activity leases wrap the current routing body rather than replacing upstream's route-generation, daemon reload or cleanup behavior.

The final source range contains 55 replayed commits versus 57 old commits. Exactly two old patches disappear; historical catalogue follow-ups remain as provenance. Every changed `!` mapping is explained above, including context-only moves and test imports. No policy retirement is claimed as equivalent supersession.

## Verification and review

All checks use the isolated candidate and disposable home/runtime state. Python dependencies come from PM's committed lock; JS workspaces use pinned pnpm 12.15.0 and Node 26.12.1. No raw pip/uv installation or live environment synchronization is part of this preparation.

- Required `scripts/check --base 8ad89d45ac6a5da0c6b2cc641bcc12aa41ceb89b`: all 15 checks passed, zero blocking/advisory code-health findings. An initial archive-guard finding was an in-checkout verification venv; verification dependencies were rebuilt outside the source tree and the disposable output removed.
- Focused TUI reconnect/client/startup-image tests: 3 files, 51 passed. Shared client/heartbeat tests: 2 files, 18 passed. TUI and shared typechecks passed; TUI production build passed.
- Initial Python memory/DB/ownership/display checks passed for those contracts. The first cron picker failure was a stale `Principal` import, corrected to `SessionActor` in its owning patch. ACP needed its declared optional dependency before collection.
- Broader ACP and upstream replacement run: 100 files, 560 passed, 2 failed, 1 skipped. Both failures were Teams cases in the shared card test missing `aiohttp`; after provisioning the declared messaging extra, the exact shared-card file passed all 15 tests. The broader run was not repeated.
- Browser/SSH/memory/status verification: 18 files, 259 passed and 10 host skips. Adjacent memory initialization/browser daemon/SSH/session ownership: 6 files, 76 passed and 12 host skips. Initial focused memory/DB/ownership/display tests passed 57 tests; the corrected cron lifecycle file subsequently passed all 6. These receipts overlap and are not summed as a unique test total.
- Full TUI suite: 260 files, 2,000 passed and 2 skipped, exit 0. An optional Python subprocess fallback printed a missing `ruamel` warning; no suite failure was reported. Changed TypeScript lint passed.
- Two independent read-only reviews approved exact source `370cf2cc67a81270d7fed9bd4f90d96bbc7ea14c`, with no blockers. No source changes followed that reviewed snapshot. The final catalogue-only commit is checked separately; publication uses the frozen explicit lease.

No live CDP, Discord, remote SSH, UI interruption or production cron canary was induced. Linux-only results do not establish Windows behavior. The complete repository-wide Python suite was not run; the verification scope is the retained patches and their affected areas.

## What is new for Peter

The incoming upstream adds TUI transcript backtracking/edit-and-fork, inline images, expandable pastes and background continuation after `/new`; a gateway-served Desktop Webapp; per-skill agent-write locks; live cron cancellation and per-job catch-up policy. Slack gains opt-in unaddressed-thread silence and better context/approval rendering. Discord changes are principally approval lifecycle and authorization reliability. Tools/delegation add opt-in batch prompt-cache warm-up. These are incoming capabilities, not features enabled or exercised in the live installation by this preparation.

## Deployment and publication boundary

The live checkout remains at the old tip above. The candidate is not a claim that any running Hermes process has loaded the new code. Publish only after final gates and an exact comparison against the frozen fork tip; use `--force-with-lease=refs/heads/peter/hermes-patches:59eb40fa8d503082070778219b82df64705362ff`, never bare force. A changed remote is a stop, not permission to overwrite it.

The Linux ownership change keeps the existing coordinated activation requirement: drain/stop/restart/reacquire together, never delete live leases. No profile configuration change is required by the retained patch-key adaptations. Browser controls stay opt-in; memory callbacks do not enable recall or retention. Installation and doctor remain separate operational gates after verified publication.

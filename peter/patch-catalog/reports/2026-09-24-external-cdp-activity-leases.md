# Publish external-CDP browser activity leases

> Historical report and execution receipt. Current refs and decisions are in the
> [September 29 reconciliation](2026-09-29-upstream-reconciliation.md). Former active refs below are lineage only.

- Date: 2026-09-24
- Repo: `NousResearch/hermes-agent`
- Base ref: `0592565e2b`
- Patch refs: `c57259c0e6` + `78b3c08653` + `3872af22de` + `ed0a742fa9`
- Branch: `peter/hermes-patches`
- Motivation: let an operator-owned watchdog stop a persistent external-CDP browser after genuine inactivity without racing an active `browser_exec` call.
- Changed files: `hermes_cli/config_defaults.py`, `tools/browser_cdp_activity.py`, `tools/browser_use_cli.py`, `tests/tools/test_browser_cdp_activity.py`, `tests/tools/test_browser_use_cli.py`
- Verification: focused browser suite `154 passed`; Ruff and `git diff --check` passed. Three independent review rounds found and drove fixes for heartbeat refresh, setup leaks, heartbeat shutdown ordering, and partial-publication cleanup; the final blocker-only review returned `PASS`.

## Local patch summary

The opt-in `browser.cdp_activity_dir` setting publishes one unique filesystem lease for each routed `browser_exec` operation when an explicit `browser.cdp_url`/`cdp_endpoint` is configured. Lease transitions and `last_used` updates are serialized with `state.lock`, and a heartbeat keeps long operations fresh. Cleanup waits for the heartbeat to terminate before unlinking so it cannot recreate a released lease.

Hermes owns only this activity protocol. Browser launch, process matching, idle duration, and shutdown remain external launcher/watchdog policy. The deployed WSL design keeps both the lease publisher and watchdog on the POSIX side, avoiding unsupported cross-OS lock interoperability.

## Upstream overlap

Authenticated GitHub research on 2026-09-24 found no merged or open upstream change with the same contract: cross-process filesystem-backed activity leases around every `browser_exec` call for an operator-owned external CDP browser.

| Item | Status | Overlap and risk |
|---|---|---|
| [PR #104010](https://github.com/NousResearch/hermes-agent/pull/104010) — reap idle real-profile Chrome without racing active tasks | Open; no review decision | Closest conceptual overlap, but uses process-local counters for Hermes-owned real-profile Chrome. It does not protect operator-owned `browser.cdp_url`. Moderate-high conflict risk in `tools/browser_use_cli.py`. |
| [PR #83739](https://github.com/NousResearch/hermes-agent/pull/83739) — keep cloud browser sessions alive during long calls | Open; no review decision | Adds periodic heartbeats to an in-memory cloud-session tracker, not an external-CDP watchdog protocol. Moderate textual conflict risk. |
| [PR #120739](https://github.com/NousResearch/hermes-agent/pull/120739) — reclaim detached Browser Use harness daemons | Open; mergeable; no review decision | Publishes owner-PID files for Browser Harness daemons. The marker means daemon ownership, not active browser work. Complementary, with likely conflict in `browser_use_cli.py`. |
| [PR #100865](https://github.com/NousResearch/hermes-agent/pull/100865) — reap persistent Browser Use daemons | Open; conflicting; no review decision | Tracks Harness ownership and in-flight reservations, not external browser activity. High textual conflict potential, not a replacement. |
| [Issue #94946](https://github.com/NousResearch/hermes-agent/issues/94946) / [PR #95006](https://github.com/NousResearch/hermes-agent/pull/95006) | Open | Internal Browser Use inactivity cleanup; does not coordinate a separately managed persistent browser. |
| [Issue #100945](https://github.com/NousResearch/hermes-agent/issues/100945) / [PR #102697](https://github.com/NousResearch/hermes-agent/pull/102697) | Open | Run-owned Harness/Chrome lifetime explicitly leaves an operator-owned CDP endpoint running. Complementary, not equivalent. |
| [Issue #110064](https://github.com/NousResearch/hermes-agent/issues/110064) / [PR #115633](https://github.com/NousResearch/hermes-agent/pull/115633) | Issue closed; PR merged | Human-control lease for the Bot Screen janitor only, not generic external-CDP activity publication. |

Related merged commits `2f2e3616b406` and `20f287547275` configure and implement internal browser-session inactivity cleanup. Commit `2a7ed25db860` covers external-CDP HAR capture while deliberately leaving the externally owned browser open. None supersedes this patch.

## Recommendation

Keep the local patch. Reconcile carefully if #104010, #83739, #120739, or #100865 lands because each may alter `tools/browser_use_cli.py`; drop only when upstream exposes an equivalent cross-process activity signal for externally managed CDP browsers.

## Raw search queries used

- `repo:NousResearch/hermes-agent "external CDP"`
- `repo:NousResearch/hermes-agent browser CDP idle`
- `repo:NousResearch/hermes-agent browser activity lease`
- `repo:NousResearch/hermes-agent browser watchdog`
- `repo:NousResearch/hermes-agent browser-use cleanup`
- `repo:NousResearch/hermes-agent persistent browser profile`
- `repo:NousResearch/hermes-agent browser session cleanup`
- `repo:NousResearch/hermes-agent cdp_url`
- `repo:NousResearch/hermes-agent browser shutdown`
- `repo:NousResearch/hermes-agent in:title,body "activity lease"`
- `repo:NousResearch/hermes-agent in:title,body "idle shutdown" browser`
- `repo:NousResearch/hermes-agent in:title,body "external CDP"`
- `repo:NousResearch/hermes-agent in:title,body "browser_harness"`

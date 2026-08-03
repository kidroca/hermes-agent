# Invalidate stale CDP discovery on browser cleanup

- Date: 2026-07-30
- Repo: `NousResearch/hermes-agent`
- Patch ref: `0bdcb31e5` (reviewed) → `ac4996f6e` (active)
- Branch: `peter/hermes-patches`
- Local status: committed as a narrow standalone patch after explicit scope review.
- Motivation: HTTP CDP discovery caches Chromium's process-specific WebSocket UUID. Browser cleanup removed the session but left that cached UUID behind, so the next session could reconnect to a dead browser generation.
- Changed files: `tools/browser_tool.py`, `tests/tools/test_browser_cleanup.py`
- Tests / verification: targeted cleanup suite `7 passed`; full browser suite `517 passed`; `py_compile`, `git diff --check`, and added-line security scan passed. Independent final review returned PASS with no blockers.

## Local patch summary

`cleanup_browser()` now clears `_cached_cdp_resolutions` before tearing down the requested session. The next sequential browser session therefore probes `/json/version` again and receives the current browser-process WebSocket UUID instead of reusing the dead generation.

The regression test exercises the behavior rather than inspecting cache contents: discovery returns a stale UUID, cleanup runs, and the next resolution must perform a second HTTP request and return a fresh UUID.

## Scope and accepted residual risk

This patch deliberately does not redesign browser lifecycle synchronization. A rare resolver already in flight when cleanup starts could repopulate the cache afterward; normal inactivity cleanup selects only sessions idle for `browser.inactivity_timeout` (default 120 seconds), making that overlap narrow. If it occurs, explicit cleanup or a later idle cleanup recovers the session. Full atomic coordination between discovery, session publication, supervisor registration, and cleanup belongs in a separate patch if operational evidence justifies it.

## Upstream overlap

Authenticated GitHub searches on 2026-07-30 for `CDP cleanup cache browser UUID`, `stale CDP`, `browser cdp_url cleanup`, `browser restart websocket`, and `json/version browser` found no matching open or closed issues/PRs in `NousResearch/hermes-agent`.

Conflict risk is low-medium and concentrated in `tools/browser_tool.py::cleanup_browser()` and CDP discovery caching. Any upstream change that removes process-generation caching or invalidates it during teardown may supersede this patch.

## Recommendation

Keep `0bdcb31e5` in the local patch stack. Drop it only when upstream guarantees that a browser restart cannot reuse a cached process-specific CDP WebSocket UUID. Preserve the stale→cleanup→fresh behavioral regression test during reconciliation.

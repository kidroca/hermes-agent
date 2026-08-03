# Honor configured TUI tool preview length

- **Date:** 2026-07-18
- **Repo:** `NousResearch/hermes-agent` (`/opt/hermes-agent`)
- **Patch ref:** `6480450d1` → `51e2dcdbe` (reviewed lineage) → `1c8dd46c4` (active)
- **Branch:** `peter/hermes-patches`
- **Local status:** retained in `peter/hermes-patches`; rebased patch is `51e2dcdbe`
- **Motivation:** The Ink TUI independently hard-coded an 80-character gateway label budget and a 64-character frontend budget, bypassing `display.tool_preview_length`. Values above 120 should be allowed to wrap naturally, while documented `0 = unlimited` behavior must remain intact. This patch deliberately excludes per-row expansion.
- **Changed files:** 13 files, **219 additions / 31 deletions**: `tui_gateway/server.py`, `tests/test_tui_gateway_server.py`, `tests/tui_gateway/test_protocol.py`, and ten `ui-tui` TypeScript/test files spanning gateway event handling, turn state, message hydration, types, rendering, and preview helpers.
- **Tests / verification:** final canonical isolated gateway run: 602 passed; focused UI: 133 passed; TUI TypeScript typecheck, ESLint, and `git diff --check` passed. Full UI suite: 1384 passed, 1 skipped, and 20 failures confined to two upstream-only files (`subscriptionOverlay.test.tsx` and `ink-backpressure.test.ts`); the same 20 failures reproduced on pristine updated `main`. Independent review found no behavioral blockers.

## Local patch summary

The patch resolves `display.tool_preview_length` from each active session/profile rather than mutating process-global display state. The gateway applies the resolved budget to live tool starts and hydrated history, emits `preview_max_len`, and preserves `0` as unlimited. The frontend stores and reapplies that budget through active, completed, verbose, and hydrated tool rendering; events without the new field retain the historical 64-character compatibility fallback. Existing `TreeTextRow` wrapping is left to handle longer previews naturally. Separately capped/redacted verbose arguments and results are unchanged, and no per-tool expansion state or retrieval path is introduced.

Conflict surface is concentrated in `tui_gateway/server.py` and the Ink tool-event/rendering pipeline (`createGatewayEventHandler.ts`, `turnController.ts`, `thinking.tsx`, `messages.ts`, `gatewayTypes.ts`, `text.ts`, and `types.ts`). The local implementation is materially broader than the two exact upstream fixes because it carries a session-scoped budget end-to-end and through history hydration.

## Rebase note — 2026-07-27

Rebased onto upstream `main` at `8eaaa5021`. Upstream commit `f0031abc3` moved live gateway tool rows from a phrased `build_tool_label` value to the raw `build_tool_preview` boundary; `cab6447d5` then extended that raw-preview path to resumed tool rows. Together they remove duplicated client phrasing but do **not** propagate `display.tool_preview_length` per session/profile or preserve the configured budget through frontend state and hydration.

The local patch was therefore retained and adapted: `_tool_ctx` now uses upstream's raw `build_tool_preview` contract while applying the session/profile budget, and the existing `preview_max_len` payload/frontend propagation remains authoritative. The initial upstream rebase mapped `9ad405d04` to `a47664801`; the later context-estimation retirement rewrite mapped `a47664801` to final patch `51e2dcdbe`. Conflict verification passed (5 Python tests and 133 TUI tests), followed by post-rebase TUI typecheck/lint and a canonical isolated run of 602 Python tests across the affected gateway surfaces.

## Upstream overlap

Evidence below was fetched with authenticated `gh` as `kidroca` on 2026-07-18. “Sweeper” comments/reviews are automated review output posted by `teknium1`; GitHub reports that account as `CONTRIBUTOR`, so these are useful repository-direction signals but are **not** treated as maintainer approval.

| Kind | # | Title | Age / status | Author signal | Maintainer / review signal | Files / size | Conflict risk | Cautious merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| Issue | [#41846](https://github.com/NousResearch/hermes-agent/issues/41846) | TUI `display.tool_preview_length` config ineffective | Created 2026-06-08 (40d); open; updated 2026-06-28 | `chliuqi`, `NONE` | One contributor comment points to #41854; no maintainer/collaborator endorsement visible | Exact symptom | **Very high semantic overlap** | Issue resolution likely eventually; timing/implementation unknown |
| Issue | [#52601](https://github.com/NousResearch/hermes-agent/issues/52601) | TUI truncates Terminal calls even with length 0 | Created 2026-06-25 (23d); closed same day as duplicate | `jcalfee`, `NONE` | `alt-glitch` (`COLLABORATOR`) explicitly marked it duplicate of #41846, identified the TUI path, reaffirmed `0 = unlimited`, and pointed to #41854 / #51067 | Exact symptom | **Very high semantic overlap** | Already closed as duplicate; strengthens likelihood that upstream accepts the bug premise, not a specific patch |
| Issue | [#51067](https://github.com/NousResearch/hermes-agent/issues/51067) | `tool_preview_length: 0` truncated by gateway falsy check | Created 2026-06-22 (26d); open | `liuhaibin0528`, `NONE` | Linked by collaborator triage on #52601; no comments on the issue itself | Exact zero/unlimited edge case | **High semantic overlap** | Unknown; no implementation or direct review signal |
| PR | [#41852](https://github.com/NousResearch/hermes-agent/pull/41852) | Honor configured tool preview length | Created 2026-06-08 (40d); open; **dirty/conflicting** | `shandian64`, `CONTRIBUTOR`; authenticated search found 0 prior merged PRs in this repo | Automated sweeper: real bug, but stale call site and unsafe process-global profile behavior; “keep open,” salvageability medium; no approval | 2 files, +47/-2: gateway server + protocol tests | **Very high**, especially `tui_gateway/server.py` | **Low as-is**; requires substantial port and session scoping |
| PR | [#41854](https://github.com/NousResearch/hermes-agent/pull/41854) | Respect config in TUI mode | Created 2026-06-08 (40d); open; **dirty/conflicting** | `liuhao1024`, `CONTRIBUTOR`; 11 prior merged PRs found | Automated sweeper: real bug, but entry-only initialization misses WebSocket and tests bypass propagation; requests positive + zero coverage; “keep open,” salvageability medium; no approval | 3 files, +36/-1: gateway entry/server + gateway tests | **Very high** in gateway/tests; does not cover the current frontend 64 cap | **Low-medium only after rework**; stronger author history, but current patch is incomplete/conflicting |
| Issue | [#16636](https://github.com/NousResearch/hermes-agent/issues/16636) | Expandable tool-call messages | Created 2026-04-27 (82d); open | `0xharryriddle`, `CONTRIBUTOR` | No maintainer signal; author links #16637 | Adjacent UX, not config bug | **Low semantic / medium future mechanical** | Unknown |
| PR | [#16637](https://github.com/NousResearch/hermes-agent/pull/16637) | Per-tool detail expansion | Created 2026-04-27 (82d); open; **dirty/conflicting** | `0xharryriddle`, `CONTRIBUTOR`; 0 prior merged PRs found | Automated sweeper flags unstable name-keyed IDs, modifier behavior, and uncapped raw results/OOM regression; salvageability low; no approval | 18 files, +515/-281; overlaps gateway and most Ink tool-rendering files | **High mechanical**, but intentionally out of local scope | **Low as-is** |
| PR | [#33946](https://github.com/NousResearch/hermes-agent/pull/33946) | Expandable tool visibility helpers | Created 2026-05-28 (51d); open; **dirty/conflicting** | `duclamvan`, `NONE`; 0 prior merged PRs found | Automated sweeper says completed-row premise remains relevant but active verbose arguments regress and newer agent-monitoring UI must be preserved; salvageability medium; no approval | 4 files, +254/-65, mainly `thinking.tsx` plus helper/tests | **Medium-high mechanical** in `thinking.tsx`; separate semantics | **Low as-is** |
| PR | [#28719](https://github.com/NousResearch/hermes-agent/pull/28719) | Declarative tool-preview schema | Created 2026-05-19 (60d); open; **dirty/conflicting** | `xxxigm`, `CONTRIBUTOR`; 42 prior merged PRs found | Automated sweeper says design fit is good / salvageability high, with one formatter exception gap; no approval | 4 files, +468/-0: `agent/display.py`, plugin, tests, docs | **Medium** at label-generation boundary; little direct Ink overlap | **Medium-low after refresh/fix**; credible author/design signal, but stale/conflicting and not a fix for TUI budget propagation |
| PR | [#34668](https://github.com/NousResearch/hermes-agent/pull/34668) | Show missing `display.*` keys in config output | Created 2026-05-29 (50d); open; mergeability unknown | `annguyenNous`, `CONTRIBUTOR` | Automated sweeper validates visibility gap / salvageability high, but flags incorrect `tool_progress` default and missing tests; no approval | 1 file, +11/-0: `hermes_cli/config.py` | **Low**; configuration visibility only | **Medium-low after correction**; not an implementation substitute |

## Notes on the most relevant upstream items

### Exact bug family: #41846, #52601, #51067, #41852, and #41854

The upstream record strongly validates the local bug report and the required `0 = unlimited` contract. The collaborator duplicate triage on #52601 is the clearest human repository signal. Neither competing PR currently implements the full local contract:

- #41852 mutates a process-global display limit and is stale relative to the current `build_tool_preview` boundary; automated review explicitly rejects that profile-scoping model.
- #41854 initializes only the stdio entry path, missing the shared WebSocket surface, and its tests set global state rather than testing propagation.
- Both are dirty/conflicting as of the evidence fetch.
- The local patch additionally removes the frontend’s independent 64-character truncation and carries the per-session budget through live state, completion, verbose rendering, and hydrated history.

Because the exact bug is acknowledged and two fixes remain open, upstream conflict risk is **very high**. However, cautious merge likelihood for either existing PR is no better than low-to-medium without rework; open status and automated “keep open” reviews are not approval.

### Expansion work: #16636/#16637/#33946

These items are adjacent rather than substitutes. Their scope requires row disclosure state, stable call identity, modifier interaction, and safe bounded/redacted detail transport. #16637’s review specifically warns that raw result forwarding could revive silent TUI OOM behavior. The local patch correctly avoids this scope. If expansion lands later, expect mechanical conflicts in `thinking.tsx`, turn state, gateway event types, and gateway tool payloads; preserve the local session-scoped preview budget and bounded verbose-detail guarantees during reconciliation.

### Declarative previews: #28719

This PR changes how tools declare and generate meaningful compact labels in `agent/display.py`; it does not remove the gateway’s explicit max or the Ink frontend’s second cap. Its label-generation work now overlaps upstream's raw `build_tool_preview` boundary, but its purpose remains complementary. Its author has substantial merged history and automated review calls the design fit good, which is a positive signal, yet the PR remains dirty/conflicting and lacks approval.

### Narrow-search gap check: #34668

Three authenticated narrow searches were run for `"tool_preview_length" TUI`, `"compactPreview"`, and `"preview_max_len"`. The latter two returned no open candidates. The first additionally found #34668, which only exposes display settings in `hermes config show`; it neither propagates nor renders the value and has low conflict risk.

## Recommendation

Keep `6480450d1` in the local patch stack for now. Watch #41852 and #41854 closely, but do not replace the local patch unless an upstream implementation demonstrably covers both stdio/WebSocket session/profile scoping, positive values above the old 80/64 caps, `0 = unlimited`, progress/completion, and hydrated history. During rebase, expect highest conflict pressure in `tui_gateway/server.py`, `createGatewayEventHandler.ts`, `turnController.ts`, `thinking.tsx`, and `text.ts`.

Treat per-row expansion as a separate future decision. If #16637 or #33946 is salvaged, reconcile UI mechanics without accepting uncapped raw details or weakening existing redaction/render-memory bounds. If #28719 lands, preserve its declarative label generation while retaining this patch’s per-session transport/render budget.

**Overall upstream risk:** very high exact semantic overlap and high future mechanical conflict risk.

**Cautious likelihood:** the bug itself is likely to receive an upstream fix, but no currently open exact PR is clearly merge-ready; timing and final design remain uncertain.

## Raw search queries used

```text
repo:NousResearch/hermes-agent is:open "tool_preview_length" TUI
repo:NousResearch/hermes-agent is:open "compactPreview"
repo:NousResearch/hermes-agent is:open "preview_max_len"
repo:NousResearch/hermes-agent is:pr is:merged author:shandian64
repo:NousResearch/hermes-agent is:pr is:merged author:liuhao1024
repo:NousResearch/hermes-agent is:pr is:merged author:0xharryriddle
repo:NousResearch/hermes-agent is:pr is:merged author:duclamvan
repo:NousResearch/hermes-agent is:pr is:merged author:xxxigm
```

Direct authenticated API views were also fetched for #41846, #52601, #51067, #41852, #41854, #16636, #16637, #33946, #28719, and #34668, including PR files, reviews, and issue comments where applicable.

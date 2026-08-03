# Add current-turn Hindsight recall strategy (historical setting names)

- Date: 2026-07-15
- Repo: `/opt/hermes-agent`
- Patch ref: `b4697a1e0` (reviewed) → `a6f99a6b8` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch inspected. Its original public settings were renamed by successor `2145e9a9b`; this report preserves the original names only as historical context.
- Motivation: offer a deliberate current-message recall path that waits before prompt construction, while retaining the established asynchronous prior-turn warming lifecycle as the default. Avoid stale prior-turn cache use in the current-turn mode, preserve short/empty gates, and make malformed wait configuration safe.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: provided post-commit verification: `/opt/hermes-agent/venv/bin/python -m pytest tests/plugins/memory -q -o 'addopts='` — **487 passed**. Final independent review found no blockers.

## Local patch summary

> **Historical terminology:** this patch originally introduced `recall_prefetch_strategy: previous|current_wait` and `recall_current_wait_seconds`. Successor `2145e9a9b` renamed the current public configuration to `recall_query_turn: previous_async|current_sync` and `recall_query_wait_seconds`, while retaining the old keys as read aliases. References to the original names below describe the `b4697a1e0` diff, not the recommended current configuration.

`recall_prefetch_strategy` originally defaulted to `previous`, preserving the end-of-turn warmup for next-turn injection. Selecting `current_wait` suppressed `queue_prefetch()` warmup and ran recall against the current user message during `prefetch()`, waiting up to `recall_current_wait_seconds` (default 30 seconds) before prompt construction. Those semantics are now exposed as `recall_query_turn: previous_async|current_sync` with `recall_query_wait_seconds`.

The current-wait path honors tools-only, disabled-auto-recall, shutdown, empty-query, and minimum-input-length gates. It begins a fresh worker, clears any prior result before that work, and only formats a result produced for the current request; it never falls back to a stale previous-turn cache. Invalid/missing/non-numeric wait settings safely use 30 seconds (negative values clamp to zero). Coverage includes defaults/config/schema, malformed wait values, latest-query selection rather than cache reuse, warmup suppression, and empty/short query suppression.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| PR | [#62687](https://github.com/NousResearch/hermes-agent/pull/62687) | fix(memory/hindsight): per-project banks, extra recall banks, and recall the current turn | created 2026-07-11; updated 2026-07-13 | `gcunharodrigues`, `NONE`; authenticated search found no prior merged upstream PR | `teknium1` says current-turn/cold-start goals are well founded but marked the proposal salvageability **medium** and identified worker-binding/lifecycle problems; no approval | 4 files, +407/-56; same Hindsight provider and provider test file | **Very high** semantic and mechanical overlap | Medium: open, sizeable, and needs review-directed rework |
| PR | [#5838](https://github.com/NousResearch/hermes-agent/pull/5838) | feat(memory): add sync_recall option for current-turn relevance | created 2026-04-07; updated 2026-07-12 | `heathley`, `CONTRIBUTOR`; authenticated search found no prior merged upstream PR | `teknium1` keeps it open with salvageability **medium**; says its generic sync mechanism is not synchronous for all providers and needs redesign. Earlier non-maintainer review approved. | 6 files, +65/-7; cross-provider agent/memory architecture, not the Hindsight plugin | **High semantic**, low direct-file overlap | Low-medium: old open PR with current maintainer redesign concerns |
| PR | [#64745](https://github.com/NousResearch/hermes-agent/pull/64745) | fix(hindsight): bind prefetch work to session identity | created/updated 2026-07-15 | `yingliang-zhang`, `CONTRIBUTOR`; authenticated search found no prior merged upstream PR | No reviews or maintainer comments yet | 2 files, +1875/-177; same provider and test file | **Very high** mechanical overlap; much broader lifecycle rewrite | Unknown: newly opened and unreviewed |
| Issue / PR | [#43891](https://github.com/NousResearch/hermes-agent/issues/43891) / [#43998](https://github.com/NousResearch/hermes-agent/pull/43998) | configurable Hindsight prefetch join timeout | issue created 2026-06-11; PR updated 2026-07-14 | #43998 `liuhao1024`, `CONTRIBUTOR`, 11 prior merged upstream PRs | #43998 has an approval, but `teknium1` later marked it salvageability **medium** because malformed config can crash initialization and join handling is incomplete | #43998: 3 files, +41/-2; same provider and tests | **High** configuration/wait-path overlap | Medium: real timing problem, but open and needs follow-up |

## Notes on most relevant upstream items

- **#62687 is the closest conceptual predecessor.** It explicitly proposes recalling the current turn and touches the exact provider/test files. Its maintainer review agrees with the goal but calls out lifecycle binding and bounded-wait issues. This local patch is intentionally narrower: a Hindsight-only, opt-in strategy that preserves `previous` by default, suppresses end-of-turn warming only in `current_wait`, and refuses stale-cache fallback.
- **#5838 shares the current-turn objective but uses a generic provider abstraction.** It is not a replacement for a provider-local strategy because the current maintainer review says the proposed generic mechanism is not synchronous for all providers. It would nevertheless affect the call path and must be reconciled if revived.
- **#64745 is a same-day, unreviewed broad rewrite of the exact Hindsight prefetch lifecycle.** Its stated session-identity binding goal is complementary to stale-work safety, but its 2,052-line diff makes it neither a safe substitute nor evidence of an accepted design. Expect direct conflicts around `_prefetch_result`, worker generation/session handling, `prefetch()`, and tests.
- **#43998 overlaps the bounded wait configuration.** It validates that configurable Hindsight timing is an upstream-recognized problem, but it uses a differently named setting and is not a replacement: the local patch selects a current-message strategy and safely parses the wait value; #43998 modifies joins more generally and still needs maintainer-requested hardening.
- Authenticated targeted searches found no open upstream item proposing this exact pair of Hindsight settings—`recall_prefetch_strategy` with `previous`/`current_wait`, plus `recall_current_wait_seconds`—or the exact no-stale-cache-fallback contract.

## Recommendation

Keep `b4697a1e0` locally as the historical behavior-introducing patch, with public nomenclature superseded by `2145e9a9b`. Upstream overlap is **very high** in the Hindsight prefetch/current-turn-recall area, but no reviewed upstream change replaces this narrowly scoped strategy. During rebase, first compare against #62687 and #64745; retain the default `previous_async` compatibility contract, `current_sync` warmup suppression, strict current-result-only behavior, query gates, and safe malformed-wait fallback unless upstream demonstrably covers each one. Re-run the complete Hindsight memory suite after any merge touching `prefetch()`, `queue_prefetch()`, `_prefetch_result`, or recall query-timing configuration.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open hindsight prefetch`
- `repo:NousResearch/hermes-agent is:open hindsight recall`
- `repo:NousResearch/hermes-agent is:open "recall_prefetch"`
- `repo:NousResearch/hermes-agent is:open "stale" prefetch`
- `repo:NousResearch/hermes-agent is:open timeout hindsight`
- `repo:NousResearch/hermes-agent is:pr is:open hindsight recall`
- Authenticated direct metadata/review/file queries: `gh api /repos/NousResearch/hermes-agent/{issues,pulls}/{62687,5838,64745,43998}` plus each PR's `/files`, `/reviews`, and issue `/comments` endpoints.

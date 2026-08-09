# Clarify Hindsight recall query-timing settings

- Date: 2026-07-15
- Repo: `/opt/hermes-agent`
- Patch ref: `2145e9a9b` (reviewed) → `1ec1958a5` (pre-2026-08-09 active) → `2f4203b7b8` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch inspected; this catalogue pass changes only `peter/patch-catalog/` documentation.
- Motivation: replace ambiguous public Hindsight timing names with names that state both the queried turn and synchronization behavior, while retaining existing profile compatibility and the established first/resumed/empty-cache recall bootstrap.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: `/opt/hermes-agent/venv/bin/python -m pytest tests/plugins/memory -q -o 'addopts='` — **489 passed** (rerun during this catalogue pass). `git show --check 2145e9a9b` returned clean.

## Local patch summary

The public configuration surface is renamed from `recall_prefetch_strategy: previous|current_wait` plus `recall_current_wait_seconds` to `recall_query_turn: previous_async|current_sync` plus `recall_query_wait_seconds`. The new schema descriptions make the two modes explicit: `previous_async` warms turn *N* for turn *N+1*, while `current_sync` queries the current message before prompt construction.

Runtime loading preserves legacy read aliases: `previous` maps to `previous_async`, `current_wait` maps to `current_sync`, and the old wait key remains a fallback when the new shared wait key is absent. New values take precedence. The one shared wait bound now governs `current_sync`, waiting for a prior `previous_async` query already in flight, and the `previous_async` current-query bootstrap when there is no consumable result. The patch deliberately retains the existing first/resumed/empty-cache bootstrap behavior and its short-query, tools-only, disabled-auto-recall, and shutdown gates.

This is a nomenclature and wait-scope clarification of local patch `b4697a1e0`; its historical public names are not the current recommended configuration surface. The `b4697a1e0` catalogue entry is updated accordingly.

> **2026-07-30 successor:** patch `034d505a4` keeps `recall_query_turn` but removes both Hindsight wait keys. External-provider turn latency is now governed by `memory.external_prefetch_timeout_seconds`; Hindsight's transport `timeout` remains separate. The wait-key behavior described in this historical report is no longer the recommended or active configuration contract.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| PR | [#62687](https://github.com/NousResearch/hermes-agent/pull/62687) | fix(memory/hindsight): per-project banks, extra recall banks, and recall the current turn | created 2026-07-11; updated 2026-07-13 | `gcunharodrigues`, `NONE` | `teknium1` says the current-turn/cold-start goals are well founded but marks the proposal salvageability **medium**; the author added generation-bound worker-result handling in response | 4 files, +407/-56; same provider/test files | **Very high** semantic and mechanical overlap | Medium: open and reworked, but no approval |
| PR | [#64745](https://github.com/NousResearch/hermes-agent/pull/64745) | fix(hindsight): bind prefetch work to session identity | created/updated 2026-07-15 | `yingliang-zhang`, `CONTRIBUTOR` | No reviews or maintainer comments | 2 files, +1875/-177; same provider/test files | **Very high** mechanical overlap | Unknown: newly opened and unreviewed |
| PR | [#62870](https://github.com/NousResearch/hermes-agent/pull/62870) | fix(memory): recall on cold start so first-turn hindsight auto-inject works | created 2026-07-11; updated 2026-07-12 | `logical-and`, `NONE` | `teknium1` marks salvageability **high**, but requires a true end-to-end cold-start budget and slow-backend coverage; author reports those revisions | 2 files, +338/-44; same provider/test files | **High** bootstrap-path overlap | Medium-high: focused open PR with reviewed follow-up |
| Issue / PR | [#43891](https://github.com/NousResearch/hermes-agent/issues/43891) / [#43998](https://github.com/NousResearch/hermes-agent/pull/43998) | configurable Hindsight prefetch join timeout | issue created 2026-06-11; PR updated 2026-07-14 | #43998 `liuhao1024`, `CONTRIBUTOR` | `teknium1` marks #43998 salvageability **medium**: malformed parsing and inconsistent join scope remain; earlier non-maintainer review approved | #43998: 3 files, +41/-2; same provider/tests/README | **High** wait-setting overlap | Medium: recognized problem but open and incomplete |

## Notes on most relevant upstream items

- **No exact upstream setting names were found.** Authenticated searches for `recall_query_turn` and `recall_prefetch_strategy` returned no open item using either exact configuration key. The local rename therefore does not collide with an already-proposed upstream public nomenclature.
- **#62687 is the closest current-turn and lifecycle overlap.** Its review and follow-up both concern bounded first/current-turn recall and stale late worker results. It could conflict directly in `prefetch()`, result publication, and tests, but it does not provide this four-name compatibility/migration contract.
- **#64745 is a broad same-file lifecycle rewrite.** It has no maintainer signal yet, so it is evidence of mechanical conflict risk rather than an accepted replacement.
- **#62870 validates cold-start bootstrap as an upstream-recognized problem.** Its focus is bounded first-turn retry behavior, not preserving the existing bootstrap under renamed settings. Reconcile the total-time-budget semantics if both patches are rebased together.
- **#43998 overlaps the configurable join wait but not the query-turn mode.** Its `prefetch_join_timeout` is a differently scoped name and still has maintainer-identified parsing/scope issues. It is not a substitute for `recall_query_wait_seconds` applying consistently to `current_sync`, in-flight `previous_async`, and bootstrap waits.

## Recommendation

Keep `2145e9a9b` only for its `recall_query_turn` (`previous_async|current_sync`) nomenclature and query-turn/bootstrap semantics. Patch `034d505a4` supersedes its provider-local wait contract and old wait-key aliases with `memory.external_prefetch_timeout_seconds`. On rebase, compare first with #62687, #64745, #62870, and #43998, but do not resurrect the duplicate Hindsight wait policy. Re-run the complete Hindsight memory suite after any merge touching `prefetch()`, `queue_prefetch()`, worker-result publication, or recall timing settings.

## Raw authenticated search queries used

- `repo:NousResearch/hermes-agent is:open "recall_query_turn"`
- `repo:NousResearch/hermes-agent is:open "recall_prefetch_strategy"`
- `repo:NousResearch/hermes-agent is:open hindsight "current turn"`
- `repo:NousResearch/hermes-agent is:open hindsight prefetch`
- Direct authenticated metadata, file, review, and comment queries for #62687, #64745, #62870, and #43998 via `gh api /repos/NousResearch/hermes-agent/{issues,pulls}/<number>`.

# Skip Hindsight automatic recall for short queries

- Date: 2026-07-14
- Repo: `/opt/hermes-agent`
- Patch ref: `b0c1ab57c` (reviewed) → `814d405ab` (pre-2026-08-09 active) → `ac4e5f5aa8` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch inspected; this catalogue pass changes only `peter/patch-catalog/` documentation.
- Motivation: prevent short acknowledgements/follow-ups from receiving stale Hindsight context while retaining legacy behaviour by default.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: reported focused suite: `venv/bin/python -m pytest tests/plugins/memory/test_hindsight_provider.py tests/plugins/memory/test_hindsight_recall_format.py tests/agent/test_memory_session_switch.py -q -o 'addopts='` — **142 passed**.

## Local patch summary

Adds backward-compatible provider configuration `recall_min_input_chars` (default `0`, preserving existing automatic-recall behaviour). When a stripped automatic query is shorter than a positive configured threshold, both `prefetch()` and `queue_prefetch()` skip recall; the patch clears cached prefetched context and increments a generation counter so an already-running prefetch cannot later inject its stale result. Focused regression coverage checks default/custom config, stale-cache clearing, queued-prefetch suppression, and invalidation of an in-flight prefetch.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#29865](https://github.com/NousResearch/hermes-agent/pull/29865) | fix(hindsight): key prefetch cache by session and query | created 2026-05-21; updated 2026-07-13 | `mentatzoe`, `NONE`; no prior merged upstream PR found in authenticated search | `teknium1` automated review says stale unqualified cache is real, but asks for lifecycle-aware redesign; no approval | 2 files, +141/-2; same provider and test file | **High** — same stale-prefetch cache/lifecycle behavior, but different proposed keying strategy | Medium: open and reviewer marks salvageability medium |
| PR | [#18372](https://github.com/NousResearch/hermes-agent/pull/18372) | fix(memory): guard stale recall and unsafe learning | created 2026-05-01; updated 2026-07-12 | `flyingdoubleG`, `NONE`; no prior merged upstream PR found in authenticated search | `teknium1` confirms stale-recall premise but requests splitting/rework of its broader sync-recall design; no approval | 8 files, +326/-20; includes same provider and provider tests | **High** semantic and file overlap if its Hindsight portion is revived | Low-medium: broad PR with requested redesign |
| Issue / duplicate PRs | [#43891](https://github.com/NousResearch/hermes-agent/issues/43891), [#43998](https://github.com/NousResearch/hermes-agent/pull/43998), [#42232](https://github.com/NousResearch/hermes-agent/pull/42232) | configurable Hindsight prefetch join timeout | issue created 2026-06-11; PRs updated 2026-07-14 | #43998 author `liuhao1024`, `CONTRIBUTOR`, 11 prior merged upstream PRs; #42232 author `UniGood`, `NONE`, none found | #43998 received an approval, then a `teknium1` review requesting safer parsing/consistent joins; #42232 has only review comments requesting corrections | each PR: 3 files; same provider + provider tests (+41/-2 and +141/-3) | **Medium** physical overlap in prefetch/config initialization, but no short-query or stale-result-discard contract overlap | #43998 medium; #42232 low-medium — both open/blocked and need follow-up |

## Notes on most relevant upstream items

- **#29865 is the closest overlap.** It addresses the same unqualified `_prefetch_result` stale-context leak by binding cache contents to session and query. Its reviewer identifies a lifecycle constraint: warming is performed after one turn and consumed for the next, so exact query matching would miss normal consecutive turns. The local patch deliberately takes a narrower path: it suppresses short automatic queries and makes stale in-flight results non-publishable; retain this lifecycle distinction when reconciling.
- **#18372 validates the stale-recall concern but is not a drop-in replacement.** Its Hindsight proposal introduces synchronous current-turn recall within a much broader memory/prompt/skill change; review asks that this be split and that background warming be suppressed in sync mode. It does not document `recall_min_input_chars` or the local generation invalidation contract.
- **#43891 is related only at the prefetch-control level.** Its duplicate PRs configure how long a prefetch is awaited; they do not filter short queries or prevent cached/in-flight results from being injected after a short acknowledgement. Nevertheless, they touch the same config and prefetch paths and can create rebase conflicts.
- Authenticated targeted searches for `recall_min_input_chars` / `recall_max_input_chars`, `hindsight prefetch`, `hindsight recall`, and `memory short query` found no open upstream item proposing this exact minimum-length configuration key or the generation-based stale-result discard semantics.

## Recommendation

Keep `b0c1ab57c` locally. Its default is backward-compatible and its narrow guard covers a stale-result case not solved by the timeout proposals. Treat upstream risk as **high** because #29865 and #18372 target the same provider lifecycle: on rebase or if either lands, compare their end-of-turn → next-turn semantics against the local short-query contract, retain the explicit stale-cache/in-flight invalidation behavior if upstream does not cover it, and rerun the focused 142-test suite. Watch #43998/#42232 only for mechanical conflicts in Hindsight config/prefetch code, not as functional replacements.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open hindsight prefetch`
- `repo:NousResearch/hermes-agent is:open hindsight recall`
- `repo:NousResearch/hermes-agent is:open "recall_max_input_chars"`
- `repo:NousResearch/hermes-agent is:open memory "short query"`
- `repo:NousResearch/hermes-agent is:pr is:merged author:mentatzoe`
- `repo:NousResearch/hermes-agent is:pr is:merged author:flyingdoubleG`
- `repo:NousResearch/hermes-agent is:pr is:merged author:liuhao1024`
- `repo:NousResearch/hermes-agent is:pr is:merged author:UniGood`

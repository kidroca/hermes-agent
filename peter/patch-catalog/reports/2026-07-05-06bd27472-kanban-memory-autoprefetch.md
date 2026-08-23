# Disable Kanban worker memory autoprefetch by default

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `06bd27472` (reviewed) → `2f22c5b31` (pre-2026-08-09 active) → `3c7407e0d9` (pre-2026-08-14 active) → `4bb58c22fc` (pre-refresh active) → `70c7e3d7dd` (pre-2026-08-23 active) → `7c849b8cbd` (active)
- Branch: `peter/hermes-patches`
- Local status: branch ahead of `peter/peter/hermes-patches` by 3 commits at inspection time; no source changes made by this report task.
- Motivation:
  - Fully autonomous dispatcher-spawned Kanban workers start with low-signal prompts such as `work kanban task t_xxx`.
  - External memory auto-prefetch on that prompt can inject irrelevant context before the worker reads the real card.
  - Human-in-the-loop sessions should keep the existing default automatic recall behavior.
  - Workers should keep explicit memory tools, built-in memory, turn-start hooks, and explicit hindsight/session recall available.
- Changed files:
  - `agent/turn_context.py`
  - `hermes_cli/config.py`
  - `hermes_cli/kanban_db.py`
  - `tests/agent/test_turn_context.py`
  - `tests/hermes_cli/test_kanban_worker_spawn_toolsets.py`
- Tests / verification:
  - Side worker review reported no blockers; `git diff --check` passed; focused tests passed.
  - Main verification after applying non-blocking test suggestion: `git diff --check && uv run --with pytest --with pytest-xdist python -m pytest tests/hermes_cli/test_kanban_worker_spawn_toolsets.py tests/agent/test_turn_context.py tests/run_agent/test_memory_provider_init.py -q -o 'addopts='` -> 23 passed in 1.94s.

## Local patch summary

Commit `06bd27472` introduces a narrow opt-out for automatic external-memory prefetch. `agent/turn_context.py` now checks `HERMES_MEMORY_AUTO_PREFETCH`; unset preserves the historical default of enabled, while `0/false/no/off` suppress `prefetch_all()` only. `on_turn_start()` still fires.

`hermes_cli/config.py` adds `kanban.memory_auto_prefetch`, defaulting to `false`. `hermes_cli/kanban_db.py` resolves that setting from the assignee profile's `HERMES_HOME` and exports `HERMES_MEMORY_AUTO_PREFETCH=0` or `1` into dispatcher-spawned worker processes. Tests cover default suppression, opt-in behavior, and preservation of the memory toolset in worker CLI toolsets.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | 45743 | [feat(memory): govern automatic memory context injection](https://github.com/NousResearch/hermes-agent/pull/45743) | 22 days | `waldmanz`; 1 PR comment; author association not exposed by `gh pr view`; prior-merge search not re-run | 1 comment, no reviews via PR API; no clear maintainer direction seen | 9 files, +946/-6; includes `agent/turn_context.py`, `agent/memory_manager.py`, governance docs/tests | Medium-high: overlaps the same conceptual policy boundary and directly edits `agent/turn_context.py` | Unknown / medium if governance direction is accepted; open without visible maintainer approval |
| PR | 50217 | [fix: skip oneshot memory prefetch](https://github.com/NousResearch/hermes-agent/pull/50217) | 14 days | `hugoalvespereira`; 1 PR comment; prior merged PR signal not re-checked | No maintainer signal seen; author comment notes conflict resolution against newer `main` | 5 files, +72/-6; `agent/agent_init.py`, `hermes_cli/oneshot.py`, `run_agent.py`, tests | Low-medium: same prefetch suppression theme but for one-shot flow, not Kanban worker spawn | Unknown / low-medium; open, recently updated for conflicts |
| PR | 44353 | [fix(cli): suppress memory prefetch for single-query runs](https://github.com/NousResearch/hermes-agent/pull/44353) | 24 days | `hyper-ariadne`; 2 PR comments; prior merged PR signal not re-checked | 2 comments, no reviews via PR API; no maintainer signal seen | 5 files, +231/-7; CLI setup/run-agent tests, no `turn_context.py` | Low-medium: same automatic prefetch lifecycle concern for `chat -q`/single-query execution | Unknown; open with positive contributor review but no maintainer approval observed |
| PR | 50800 | [fix(memory): bound prefetch_all() per-provider with a timeout to prevent ACP hang](https://github.com/NousResearch/hermes-agent/pull/50800) | 13 days | `ygd58`; prior merged PR signal not re-checked | No comments/reviews via PR API | 2 files, +139/-2; `agent/memory_manager.py`, tests | Low: changes behavior inside `prefetch_all()` rather than whether workers call it | Unknown; open, small, no maintainer signal |
| PR | 55600 | [fix(kanban): strip parent credentials from worker env](https://github.com/NousResearch/hermes-agent/pull/55600) | 5 days | `necoweb3`; prior merged PR signal not re-checked | 1 `COMMENTED` review by `tonydwb`; no approval seen | 2 files, +61/-8; includes `hermes_cli/kanban_db.py` | Medium: both modify worker subprocess environment construction in `kanban_db.py`; semantic goals are compatible | Unknown / medium; small and security-motivated but no maintainer signal seen |
| PR | 56018 | [feat(kanban): fire worker start lifecycle hook](https://github.com/NousResearch/hermes-agent/pull/56018) | 4 days | `rayjun`; 1 PR comment; prior merged PR signal not re-checked | 1 comment; previous triage notes say it implements #56008 and complements merged dispatcher hooks | 3 files, +88/-2; CLI/plugins/tests, not `kanban_db.py` | Low: could become an alternative place to observe/alter worker startup, but does not touch memory prefetch | Medium: collaborator triage context exists, but not approval/merge |
| PR | 31564 | [fix: harden memory and kanban reliability](https://github.com/NousResearch/hermes-agent/pull/31564) | 42 days | `Thawpoint`; prior merged PR signal not re-checked | No comments/reviews via PR API | 30 files, +4579/-269; includes `hermes_cli/config.py`, `hermes_cli/kanban_db.py`, memory/hindsight files | Medium-high due broad changes in both Kanban and memory config paths | Low / unknown; large, old, no maintainer signal seen |
| Issue | 57100 | [Memory provider plugin for Metronix: prefetch injection + write-through + cross-profile](https://github.com/NousResearch/hermes-agent/issues/57100) | 3 days | `toomij99`, `NONE` | No maintainer signal seen in search result | N/A | Low: provider integration may increase the value of configurable prefetch policy but does not directly overlap worker spawn | Unknown |
| Issue | 57793 | [Legacy memory tool should be gated when an external memory provider is configured](https://github.com/NousResearch/hermes-agent/issues/57793) | 2 days | `bedpan`, `NONE` | No maintainer signal seen in search result | N/A | Low: tool gating differs from keeping tools available while suppressing auto-prefetch | Unknown |
| Issue | 40645 | [Kanban: worker profile custom_providers not inherited from default config](https://github.com/NousResearch/hermes-agent/issues/40645) | 29 days | `ashanzzz`, `NONE` | No maintainer signal seen in search result | N/A | Low-medium: worker profile config resolution is adjacent to this patch's per-profile config lookup | Unknown |

## Notes on most relevant upstream items

- **#45743 is the highest conceptual overlap.** It proposes a broader governance layer for automatic memory context injection and touches `agent/turn_context.py`. If merged, Peter's local env-var gate may need to be rebased into that governance policy rather than remaining as a standalone conditional.
- **#50217 and #44353 independently validate the underlying pain:** automatic memory prefetch can be inappropriate for short/one-shot/low-signal execution modes. They do not directly solve dispatcher-spawned Kanban workers, but they indicate upstream attention to mode-specific prefetch suppression.
- **#55600 is the most direct file-conflict risk in Kanban worker spawning.** It modifies environment handling in `hermes_cli/kanban_db.py`, the same area where this patch injects `HERMES_MEMORY_AUTO_PREFETCH`. The desired semantics appear compatible: scrub unsafe inherited environment, then explicitly pass safe worker-scoped env keys.
- **#56018 may become a cleaner extension point** for worker-start policy or observability, but the current patch deliberately avoids plugin dependence and keeps behavior deterministic via config/env.
- Authenticated `gh pr view` refreshed PR sizes, comments, reviews, and mergeability where available. Author-association/prior-merged-PR signals remain incomplete because `gh pr view` does not expose association and the broad GitHub search sweep hit an authenticated search-rate-limit response; these are not inferred.

## Recommendation

Keep the local patch for now. It is narrow, opt-in reversible, and addresses a Peter-specific autonomous-worker quality issue without disabling explicit memory access. Watch upstream #45743 most closely; if a memory-governance framework lands, port this default into that policy surface. Also watch #55600 for worker env construction conflicts during rebase.

Suggested future upstream shape if proposing this: avoid a global `HERMES_MEMORY_AUTO_PREFETCH` user-facing knob alone; expose it as a documented execution-mode or Kanban worker policy so one-shot, cron, and autonomous-worker behaviors can converge under one memory injection governance model.

## Raw search queries used

```text
repo:NousResearch/hermes-agent is:open kanban memory
repo:NousResearch/hermes-agent is:open kanban prefetch
repo:NousResearch/hermes-agent is:open memory prefetch
repo:NousResearch/hermes-agent is:open HERMES_MEMORY_AUTO_PREFETCH
repo:NousResearch/hermes-agent is:open memory_auto_prefetch
repo:NousResearch/hermes-agent is:open kanban worker config
repo:NousResearch/hermes-agent is:pr is:open turn_context memory
repo:NousResearch/hermes-agent is:pr is:open kanban worker
repo:NousResearch/hermes-agent is:issue is:open external memory
repo:NousResearch/hermes-agent is:pr is:merged author:hugoalvespereira
repo:NousResearch/hermes-agent is:pr is:merged author:<relevant-author>  # broad search-rate-limited during refresh
```

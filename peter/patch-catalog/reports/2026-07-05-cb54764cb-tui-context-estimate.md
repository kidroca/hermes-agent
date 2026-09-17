# Estimate TUI context usage without provider token counts

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch lineage: `cb54764cb` → pre-2026-07-27 stack `64519d142` → transient rebase `3d85322ca`; dropped on 2026-07-27
- Branch: peter/hermes-patches
- Local status: historical; no longer present in `peter/hermes-patches`
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: tests/test_tui_gateway_server.py, tui_gateway/server.py
- Tests / verification: after retirement, the canonical isolated gateway run passed 602 tests across `test_auto_continue.py`, `test_failed_turn_retention.py`, `test_protocol.py`, and `test_tui_gateway_server.py`.

## Local patch summary

Makes the TUI gateway produce a useful context estimate when provider token usage is absent, avoiding a dead/blank context meter for providers that do not return token counts.

## Retirement note — 2026-07-27

The patch was dropped after rebasing onto upstream `main` at `8eaaa5021`. Upstream commit `83b7c52ec` deliberately emits no context gauge when a real current-window occupancy value is unavailable: unknown is preferable to a plausible-looking estimate. The built-in compressor still reports real `last_prompt_tokens` after a turn, so ordinary context reporting is unaffected.

The local fallback was display-only. It estimated message and system-prompt text with a rough tokenizer heuristic, did not improve compression or context management, and added message-history plumbing plus a second `_get_usage` argument that repeatedly conflicted with upstream and test fixtures. Retiring it restores upstream's intentional unknown-state contract; this is a policy supersession, not equivalent upstream fallback functionality.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #56746 | fix(desktop): align context usage and compaction status | created/updated 2026-07-02 | `Git-on-my-level` | no comments/reviews via PR API | 8 files, +178/-10 | Medium: context-usage semantics adjacent, but desktop-focused | Unknown: no maintainer signal |
| PR | #34282 | fix(cli): keep context meter live without usage | created 2026-05-29; updated 2026-06-20 | `stephenschoettler` | no comments/reviews via PR API | 2 files, +47/-0 | High: same blank/dead context-meter symptom when usage is absent | Medium-low/unknown: focused but no maintainer signal |
| Issue | #42617 | state.db input_tokens and cache_read_tokens incorrectly recorded for MiMo/xiaomi provider | created/updated 2026-06-09 | `willingning-coder` | 3 comments | n/a | Medium: provider token-accounting source may affect estimate inputs | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Keep this report as historical context. Do not restore the rough fallback unless a concrete provider/user problem justifies estimated precision over upstream's explicit unknown state; prefer real current-window token accounting.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open TUI context usage provider tokens`
- `repo:NousResearch/hermes-agent is:open context meter live without usage`
- `repo:NousResearch/hermes-agent is:open state.db input_tokens provider`

# Show Slack memory context debug notices

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `6e547a2c0` (reviewed) → `231f2eecd` (pre-2026-08-09 active) → `6bfadc1e6c` (pre-2026-08-14 active) → `dd5d9162c6` (pre-refresh active) → `fdfae440b1` (pre-2026-08-23 active) → `2537142766` (pre-final-refresh active) → `82979d8a43` (pre-2026-08-27 active) → `b66511c378` (pre-final-refresh active) → `3cdb1516f7` (pre-final-refresh-2 active) → `e954cfe08e` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: gateway/display_config.py, gateway/run.py, hermes_cli/config.py, tests/gateway/test_slack_memory_context_display.py
- Tests / verification: commit contains focused tests: Slack memory context display tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Adds Slack gateway display configuration and run-path handling so memory context debug notices can be surfaced in Slack when enabled.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #13767 | feat(gateway): add Microsoft Teams platform adapter V2 | created 2026-04-22; updated 2026-06-19 | `AlexLuzik` | 4 comments, no reviews via PR API | 37 files, +6542/-30 | Low-medium: gateway platform/display architecture adjacent, not direct Slack memory context | Low/unknown: large, stale, no approval |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Low-to-medium overlap found; keep local patch. Re-run Slack gateway tests after gateway/display_config.py or gateway/run.py upstream changes.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open Slack memory context debug notices`
- `repo:NousResearch/hermes-agent is:open gateway display memory context Slack`
- `repo:NousResearch/hermes-agent is:open Slack recalled memory context`

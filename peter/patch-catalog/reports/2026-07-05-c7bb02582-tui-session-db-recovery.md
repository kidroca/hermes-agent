# Recover and warn when TUI session DB is locked or unavailable

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `c7bb02582`, `bd2740267` (reviewed) → `4e5278808` + `ec22e73cb` (pre-2026-08-09 active) → `5e739d034e` + `0e7f68a806` (pre-2026-08-14 active) → `21e6282757` + `ba0691c254` (pre-refresh active) → `838f1de450` + `c9cd4f9d6c` (pre-2026-08-23 active) → `d5c283e08e` + `65a5866a82` (pre-final-refresh active) → `20888a2dca` + `c27bea8e6c` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: tests/test_tui_gateway_server.py, tui_gateway/server.py
- Tests / verification: commit contains focused tests: TUI gateway DB lock/unavailable tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Adds gateway resilience around session DB startup failures: recover after startup lock where possible and send an explicit TUI warning when the session DB remains unavailable.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | #44795 | _try_wal_checkpoint checkpoint failure silently swallows exceptions, corrupts state.db WAL to zero bytes | created 2026-06-12; updated 2026-06-27 | `kaluluosi` | 3 comments | n/a | Medium: same state/session DB reliability class, not TUI startup warning specifically | Unknown |
| Issue | #56815 | FTS5 virtual table schema loss orphans shadow tables, breaking session_search permanently after interrupted migration | created/updated 2026-07-02 | `V0aRyn` | 0 comments | n/a | Medium: adjacent DB-unavailable failure, different root cause | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Keep the local guard and warning. Conflict risk is medium in tui_gateway/server.py if upstream centralizes DB health handling.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open TUI session DB lock unavailable`
- `repo:NousResearch/hermes-agent is:open state.db WAL checkpoint unavailable`
- `repo:NousResearch/hermes-agent is:open session_search DB startup lock`

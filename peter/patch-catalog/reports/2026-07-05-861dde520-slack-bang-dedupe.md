# Dedupe Slack bang commands before slash rewrite

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `861dde520`
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: plugins/platforms/slack/adapter.py, tests/gateway/test_slack.py
- Tests / verification: commit contains focused tests: Slack bang command rewrite/dedupe tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Fixes Slack adapter command normalization so bang commands are deduplicated before slash-command rewrite, avoiding duplicate command handling in Slack threads/channels.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | #26813 | Gateway: /stop and /interrupt are fed to agent as steer text instead of command | created 2026-05-16; updated 2026-06-21 | `jlukenoff` | 2 comments | n/a | Medium-high: command-normalization and interrupt rewrite path overlap | Unknown |
| Issue | #12688 | Configurable command prefix for the messaging gateway | created 2026-04-19; updated 2026-06-28 | `huesagi` | 6 comments | n/a | Medium: command-prefix redesign could supersede local Slack bang/slash logic | Unknown |
| Issue | #26884 | Universal interrupt keywords for gateway sessions | created/updated 2026-05-16 | `zccyman` | 0 comments | n/a | Medium: platform command consistency adjacent | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Dropped during the 2026-07-25 rebase. Upstream `5f3f1948b7` introduced
`_rewrite_known_bang_command`, applies it before event deduplication, and carries
focused Slack thread/channel coverage. That implementation supersedes the local
normalization patch.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open Slack bang commands slash rewrite`
- `repo:NousResearch/hermes-agent is:open Slack !cmd rewrite /stop interrupt`
- `repo:NousResearch/hermes-agent is:open Configurable command prefix gateway Slack`

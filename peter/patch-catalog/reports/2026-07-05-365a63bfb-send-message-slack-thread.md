# Preserve Slack thread id in send_message

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `365a63bfb`
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: tests/tools/test_send_message_tool.py, tools/send_message_tool.py
- Tests / verification: commit contains focused tests: send_message Slack thread preservation test; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Fixes send_message target parsing so Slack thread identifiers survive routing instead of being dropped/flattened.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | #51198 | Slack send_message omits MEDIA attachments | created/updated 2026-06-23 | `greptile` | 1 comment | n/a | Medium: same Slack send_message routing surface, different payload dimension | Unknown |
| Issue | #20104 | send_message text/media/files are delivered to general topic instead of current thread | created 2026-05-05; updated 2026-05-27 | `bashrusakh` | 1 comment | n/a | Medium-high: directly matches thread-aware send_message routing semantics | Unknown |
| Docs | gateway-internals | Thread-aware platforms may include thread IDs in chat_id | main docs | upstream docs | documents desired behavior | docs only | low | n/a |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Dropped during the 2026-07-25 rebase. Upstream `93e25ceb13` added the
thread-aware adapter/standalone delivery contract, and `d9fe008db` routed Slack
text sends through that path. The shared `_send_via_adapter` now passes
`thread_id` to both the live adapter metadata and standalone sender, replacing
this Slack-specific patch with the generalized implementation.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open send_message Slack thread id`
- `repo:NousResearch/hermes-agent is:open Slack send_message thread-aware platforms`
- `repo:NousResearch/hermes-agent is:open send_message delivered to general topic Slack`

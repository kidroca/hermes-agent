# Expose TUI memory recall context

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `fa2eff205` (reviewed) → `8799ab6bf` (pre-2026-08-09 active) → `b84e0d066e` (pre-2026-08-14 active) → `d0b4dcbc9c` (pre-refresh active) → `c8007de510` (pre-2026-08-23 active) → `4aafc06193` (pre-final-refresh active) → `f52f4728a2` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: agent/conversation_loop.py, agent/turn_finalizer.py, hermes_cli/config.py, run_agent.py, tests/run_agent/test_memory_context_finalization.py, tests/test_tui_gateway_memory_context.py, tui_gateway/server.py, ui-tui/src/__tests__/memoryContext.test.ts, ui-tui/src/app/createGatewayEventHandler.ts, ui-tui/src/app/turnController.ts, ui-tui/src/components/messageLine.tsx, ui-tui/src/gatewayTypes.ts, ui-tui/src/types.ts
- Tests / verification: commit contains focused tests: memory context finalization, gateway, and TUI rendering tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Carries recalled memory context through turn finalization/gateway events into the TUI so users can see/debug what memory was injected for a turn.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #53222 | fix(memory): gate auto recall + scrub inline-echoed recall block (#40170) | created 2026-06-26; updated 2026-06-28 | `erosika` | 2 comments, no reviews via PR API | 11 files, +380/-15 | Medium-high: changes recall routing/display policy and could affect finalization payloads | Unknown |
| PR | #40425 | fix(memory): keep recalled context off customer and downstream paths (#40170) | created 2026-06-06; updated 2026-06-29 | `rodboev` | 2 comments, no reviews via PR API | 39 files, +3089/-268 | High: broad recall-routing changes could conflict with exposing recall context to TUI | Unknown/low-medium: large, no visible approval |
| Issue | #42292 | [Feature]: Conversation Memory Locations | created 2026-06-08; updated 2026-07-05 | `chrislyons` | 1 comment | n/a | Medium: user-facing memory location/visibility concept | Unknown |
| PR | #44586 | feat(memory+delegation): layered memory types, proposal gate, retrieval pack, integration plugins, delegation governance | created/updated 2026-06-12 | `ZERONE2018` | review `CHANGES_REQUESTED` by `mxnstrexgl` | 38 files, +8158/-84 | High if revived: broad memory pipeline redesign | Low/unknown: changes requested, large PR |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Medium-high conflict risk across agent turn finalization and TUI event types; preserve local debug visibility but reconcile with any upstream memory governance/display design.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open TUI memory recall context`
- `repo:NousResearch/hermes-agent is:open memory recalled context downstream paths`
- `repo:NousResearch/hermes-agent is:open Conversation Memory Locations`

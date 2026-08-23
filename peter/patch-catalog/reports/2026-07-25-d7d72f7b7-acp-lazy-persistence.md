# Defer ACP session persistence until first prompt

- Date: 2026-07-25
- Repo: `/opt/hermes-agent`
- Patch ref: `d7d72f7b7` (reviewed) → `acce69a54` (pre-2026-08-09 active) → `524509a777` (pre-2026-08-14 active) → `97a22e5917` (pre-refresh active) → `7668e67efc` (pre-2026-08-23 active) → `9ece37ed16` (active)
- Branch: `peter/hermes-patches`
- Local status: committed independently from ACP close lifecycle support so it can be dropped when upstream adopts equivalent lazy persistence.
- Motivation: `session/new` previously created durable empty rows that survived abandoned editor drafts and accumulated in `state.db`.
- Changed files: `acp_adapter/session.py`, `tests/acp/test_session.py`, `tests/acp/test_session_db_private_access.py`
- Tests / verification: focused ACP session tests passed; the full ACP suite passed before the close patch and the final combined suite passed (`336 passed`); `ruff check` and `git diff --check` passed.

## Local patch summary

New ACP sessions remain provisional in memory while their canonical history is empty. The central persistence guard also covers pre-prompt metadata changes, so changing model, mode, or cwd cannot accidentally materialize an empty row. The first real prompt uses the existing `AIAgent` persistence path, which writes the accepted inbound user message before model execution; existing sessions and forks with history remain durable. Session metadata is preserved when the durable row is created.

No canonical messages are deleted or rewritten by this patch.

## Upstream overlap

Upstream issue [#50799](https://github.com/NousResearch/hermes-agent/issues/50799) is open and explicitly documents first-real-activity persistence as the ghost-session fix. It recommends keeping abandoned drafts out of `state.db` while representing transient live sessions separately in Desktop UI state. That is very high semantic overlap with this patch, although #50799 targets gateway/Desktop visibility rather than the ACP adapter implementation.

## Recommendation

Keep this narrow patch until upstream applies the same first-prompt persistence contract to ACP. If equivalent behavior lands, drop `d7d72f7b7` independently; preserve the tests that pre-prompt metadata cannot create a row and that the accepted first user message is durable before model execution.

# Separate Slack Hindsight recall query context

- Date: 2026-07-19
- Repo: `/Users/Shared/AI/hermes-agent`
- Patch ref: `578c68e6a` (reviewed; authored externally as `d75472ae0`) → `95b101e1c` (pre-2026-08-09 active) → `59a62b3ba4` (pre-2026-08-14 active) → `6e39c6976b` (active)
- Branch: `peter/hermes-patches` (authored on `peter/hindsight-slack-query` before integration)
- Local status: functional patch committed; this catalogue pass changes only `peter/patch-catalog/`.
- Motivation:
  - Slack enriches message text with Block Kit quotes, link previews, files, reply metadata, and first-entry thread history before the agent sees it.
  - Hindsight's automatic recall minimum/maximum input gates were therefore measuring adapter scaffolding instead of the current authored request, allowing a short continuation to trigger recall and letting truncation discard the actual new intent.
  - The first agent turn in an existing Slack thread still needs hydrated prior discussion because no Hermes conversation history exists yet.
- Changed files: `agent/conversation_loop.py`; `agent/turn_context.py`; `agent/turn_finalizer.py`; `gateway/platforms/base.py`; `gateway/run.py`; `plugins/platforms/slack/adapter.py`; `run_agent.py`; and focused tests under `tests/agent/`, `tests/gateway/`, and `tests/run_agent/`.
- Tests / verification: relevant gateway/agent suite **329 passed**; focused Hindsight provider suite **138 passed** with the `hindsight` extra; Ruff, `py_compile`, and `git diff --check` passed. `ty` still reports hundreds of repository-baseline diagnostics, but rerunning with the worktree on `PYTHONPATH` produced no `memory_query_message` unknown-argument or positional-signature diagnostics. Independent review of the final integrated commit found **no blocking findings**; its non-blocking notes were already covered by the typed nullable field, current-first truncation regression, direct current/queued prefetch tests, explicit `/queue`/`/steer` propagation tests, and the proxy-mode residual risk below.

## Local patch summary

`MessageEvent.memory_query_text` gives platform adapters a separate optional query for automatic external-memory recall while leaving `MessageEvent.text` untouched for the model and persisted transcript. Slack sets this query from normalized, mention-stripped authored text before Block Kit, unfurl, file, reply, and thread enrichment can affect it.

For a continuation with an active Slack thread session, Hindsight receives only the newly authored text. For the first agent turn in an existing Slack thread, Slack appends hydrated thread context to the recall query **after** the current request; a maximum-length truncation therefore drops oldest context before current intent. The model continues to receive the existing context-first enriched payload.

The optional query is threaded through gateway dispatch, `AIAgent.run_conversation()`, turn-start memory notifications, synchronous/current prefetch, and completed-turn queued prefetch. Durable memory synchronization still uses the original persisted user payload. `/queue` and turn-boundary `/steer` fallbacks rebuild the recall query from the stripped follow-up text so queued synthetic `MessageEvent` copies do not lose the separation.

The separately managed `slack-dm` and `slack` profiles both raise `recall_max_input_chars` from 800 to 2000: `~/.hermes` commits `af3fffd` and `41abb89`, respectively. Those profile configurations are deliberately not part of this source patch.

## Upstream overlap

| Kind | # | Title | Current upstream state / signal | Conflict risk | Relationship to this patch |
|---|---:|---|---|---|---|
| PR | [#66310](https://github.com/NousResearch/hermes-agent/pull/66310) | `fix(slack): preserve typed command integrity` | Open; +393/-51 across 5 files. Contributor review found no static correctness issue and says salvage should be mechanical, while the PR remains labelled `needs-decision`. | **Very high mechanical** in `plugins/platforms/slack/adapter.py` and `gateway/run.py` | Moves first-entry thread history from `text` into `MessageEvent.channel_context` and preserves it through `/queue`/`/steer`. It is orthogonal to Hindsight query gating but changes the exact enrichment boundary this patch observes. |
| PR | [#66069](https://github.com/NousResearch/hermes-agent/pull/66069) | `fix(slack): preserve thread context for commands` | Open; focused predecessor now substantially overlapped by #66310. Review asks whether it should close in favor of the broader command-integrity path. | **High mechanical** in the same Slack first-thread-turn block | Also separates first-entry thread history from command text. It does not add a memory-only query contract or carry it through agent prefetch/finalization. |
| PR | [#29865](https://github.com/NousResearch/hermes-agent/pull/29865) | `fix(hindsight): key prefetch cache by session and query` | Open; maintainer review validates end-of-turn warming → next-turn consumption and rejects naïve exact-current-query matching. | **High semantic**, low direct hunk overlap | Relevant to queued prefetch lifecycle and query identity, but it does not distinguish platform-authored text from model/persistence payloads. |
| PR | [#18372](https://github.com/NousResearch/hermes-agent/pull/18372) | `fix(memory): guard stale recall and unsafe learning` | Open; maintainer requests the broad change be split and reworked around correct Hindsight background warming. | **Medium semantic** | Adjacent stale-recall work; not a replacement for adapter-selected query text. |

## Notes on most relevant upstream items

### #66310 — expected rebase conflict

This is the main rebase hazard. If it lands, Slack will preserve prior thread discussion in `channel_context` rather than prepend it to `text`. Rebase the local query selection onto that representation: continuation recall remains authored text only; first-turn recall remains current authored text followed by the fetched thread context. Preserve `memory_query_text` when #66310's `/queue` and `/steer` `MessageEvent` copies are merged with the local equivalents.

### #29865 — lifecycle semantics remain separate

This patch changes which text identifies a recall request; it does not change the established previous-async/current-sync timing contract or durable `sync_all()` payload. Any future adoption of keyed prefetch caches must key and queue the selected memory query without requiring the next visible message to match it.

### No exact upstream replacement found

Public GitHub issue/PR searches found Slack thread-context and Hindsight prefetch work, but no proposal that lets a platform adapter provide a raw-authored external-memory query while retaining enriched model/persistence text across both current and queued prefetch paths.

## Residual risks

- Gateway proxy mode posts the enriched visible message through the existing OpenAI-compatible API and has no protocol field for `memory_query_text`. The deployed `slack-dm` profile uses the local/shared-workspace path, so this patch's target runtime is covered; proxy deployments need an API contract extension before they get the same behavior.
- First-turn detection still depends on `_has_active_session_for_thread()`. A genuinely missing/stale session intentionally falls back to the full hydrated first-turn query.
- The Hindsight maximum cap can still truncate very long first-turn history by design; current authored intent remains at the front and the `slack-dm` cap is separately widened to 2000 characters.

## Recommendation

Keep `578c68e6a` as the narrow cross-layer query-separation patch. On rebase, treat #66310/#66069 as high-risk Slack adapter conflicts and preserve the invariant independently of whether thread history lives in `text` or `channel_context`: continuation recall uses authored text only; first-turn recall uses current authored text first plus hydrated context; model and durable persistence retain their richer payloads. Re-run the gateway/agent and Hindsight suites after any change to MessageEvent copying, Slack enrichment order, `build_turn_context()`, or completed-turn prefetch.

## Raw public search queries used

GitHub REST/web search on 2026-07-19 (the local `gh` CLI was unavailable):

- `repo:NousResearch/hermes-agent is:pr slack "thread context"`
- `repo:NousResearch/hermes-agent is:pr hindsight slack recall`
- `repo:NousResearch/hermes-agent is:pr "memory query"`
- `repo:NousResearch/hermes-agent is:pr "recall_min_input_chars"`
- Targeted public API views for PRs #66310, #66069, #29865, and #18372, including changed files and public review/comments where available.

# Surface failed Hindsight retention through the notice rail

- Date: 2026-07-13
- Repo: `/opt/hermes-agent`
- Patch ref: `95ae1dd56`
- Branch: `peter/hermes-patches`
- Motivation: automatic Hindsight retains run in a background writer. Previously a failure only reached the private log, so Peter could lose long-term-memory writes for days without a TUI or Discord signal.
- Changed files: `agent/agent_init.py`, `plugins/memory/hindsight/__init__.py`, `tests/run_agent/test_memory_provider_init.py`, `tests/plugins/memory/test_hindsight_provider.py`
- Tests / verification: focused memory-provider, notice-spine, and gateway notice tests passed (`149 passed`); the provider test covers the real writer exception path, one-shot alerting, failed switch-flush handling, and recovery.

## Local patch summary

The agent now forwards its existing notice and notice-clear callbacks to memory providers. The Hindsight provider uses them only for automatic-retain writer transitions:

- first failed retain emits a sticky `hindsight.retain` error notice;
- repeated failures do not spam;
- a later successful retain clears the sticky local notice and emits one recovery notice;
- the notification text is intentionally sanitized (`Check Hermes logs`) so raw upstream exception payloads are not pushed into a Discord/group conversation.

The existing gateway notice rail renders the event in the TUI and delivers a single sender/thread-aware platform notice for Discord. No polling, timers, provider probes, new daemons, or new delivery channel are introduced.

## Upstream overlap

| Kind | Query / area | Result | Conflict risk |
|---|---|---|---|
| GitHub issues / PRs | `repo:NousResearch/hermes-agent Hindsight retain notification OR notice` | No exact open candidate returned by authenticated GitHub search on 2026-07-13 | Medium |
| Source | `agent/agent_init.py` memory-provider initialization kwargs | Existing upstream changes here can conflict with callback threading | Medium |
| Source | `plugins/memory/hindsight/__init__.py` writer loop | Existing/upstream Hindsight queue or error-policy work can conflict | Medium-high |
| Source | gateway `AgentNotice` rail | Reused rather than extended | Low |

## Recommendation

Keep this as a narrow local patch. During rebases, re-check memory-provider callback initialization and the Hindsight writer loop. If upstream adds a provider-level background-operation status interface, replace this provider-specific bridge with that upstream contract.

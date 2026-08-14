# Unify external-memory prefetch deadlines and queued recall queries

- Date: 2026-07-30
- Repo: `NousResearch/hermes-agent`
- Patch ref: `034d505a4` (reviewed) → `630f674e1` (pre-2026-08-09 active) → `02e84d55ad` (pre-2026-08-14 active) → `87d27ae8a0` (active)
- Branch: `peter/hermes-patches` (authored on `peter/memory-prefetch-deadline`)
- Local status: functional source commit passed independent review; catalogue documentation is a separate follow-up commit.
- Motivation:
  - Upstream's fixed eight-second `MemoryManager` guard was deliberately added to fail open around wedged external providers, but it also capped the local Hindsight `current_sync` path before Hindsight's separate 30-second `recall_query_wait_seconds` elapsed.
  - A queued/busy gateway follow-up preserved `MessageEvent.memory_query_text` on the event but dropped it at the recursive `_run_agent()` boundary, causing enriched reply/thread text to replace the authored recall query and bypass short-input gates.
- Changed files: `agent/agent_init.py`; `agent/memory_manager.py`; `gateway/run.py`; `hermes_cli/config.py`; `plugins/memory/hindsight/__init__.py`; and focused tests under `tests/agent/`, `tests/gateway/`, and `tests/plugins/memory/`.
- Tests / verification: **466 passed** across focused Hindsight, MemoryManager/config, gateway queue, and config suites. Ruff, `py_compile`, `git diff --check`, and the added-line security scan passed. The independent delegated review returned **PASS with no blocking findings**; its sole non-blocking note was to document migration from the removed Hindsight wait settings, covered below.

## Local patch summary

`memory.external_prefetch_timeout_seconds` is now the single user-facing current-turn latency budget for external memory providers. It defaults to the upstream-compatible eight seconds and is passed from profile config into `MemoryManager`; direct `MemoryManager` users retain the same default.

Hindsight no longer exposes, parses, or applies `recall_query_wait_seconds` or its legacy `recall_current_wait_seconds` alias. Its `prefetch()` waits for the provider worker, while `MemoryManager` owns the fail-open deadline and suppresses overlapping provider prefetches until a timed-out worker eventually returns. Hindsight's stock `timeout` / `HINDSIGHT_TIMEOUT` remains separate and still bounds the underlying API transport.

The gateway's queued-event drain now carries `pending_event.memory_query_text` into the recursive agent call. Enriched model/persistence text remains unchanged, but automatic recall receives the authored query. For the interrupt fallback where no `MessageEvent` exists, the pending raw message is used as the query.

## Configuration migration

Remove the obsolete provider-local setting from `hindsight/config.json`:

```json
"recall_query_wait_seconds": 30
```

Set the generic turn budget in profile `config.yaml` instead:

```yaml
memory:
  external_prefetch_timeout_seconds: 15
```

Existing Hindsight wait keys are intentionally ignored rather than migrated at runtime. This avoids preserving two competing timeout policies. Hindsight's transport `timeout` remains valid and should not be removed or tied to the turn budget.

## Upstream overlap and rebase risk

- Upstream commit `d77c455d7d` introduced fail-fast external prefetch handling; follow-up `8d1c96fd2f` established the fixed eight-second guard. This patch preserves that default and only makes it profile-configurable through the normal `config.yaml` surface.
- The local Hindsight `current_sync` strategy and its former wait knob came from local patches `b4697a1e0` and `2145e9a9b`. The query-turn strategy remains; only the duplicate wait policy is superseded.
- Local patch `578c68e6a` introduced `MessageEvent.memory_query_text` and propagated it through normal gateway/agent paths. This patch closes the omitted queued/busy recursive boundary. Rebase both patches together if upstream changes event copying, queue draining, or `_run_agent()` signatures.
- Mechanical conflict risk is high in `plugins/memory/hindsight/__init__.py` and `gateway/run.py`, but the invariants are narrow: one generic external-prefetch deadline, a separate provider transport timeout, and authored recall-query preservation across recursive queued turns.

## Recommendation

Keep `034d505a4` in the local patch stack. On rebase, retain the upstream-compatible eight-second default while preserving profile overrides, and drop it only when upstream provides an equivalent generic config key plus queued-event recall-query propagation. Re-run the focused MemoryManager, Hindsight, and gateway queue suites after any reconciliation.

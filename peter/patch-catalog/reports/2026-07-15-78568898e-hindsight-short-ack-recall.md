# Preserve Hindsight recall after short acknowledgements

- Date: 2026-07-15
- Repo: `/opt/hermes-agent`
- Patch ref: `78568898e` (reviewed) → `7b85e970e` (pre-2026-08-09 active) → `f120632b37` (pre-2026-08-14 active) → `dc959bb70f` (pre-refresh active) → `8e7a126e4c` (pre-2026-08-23 active) → `ddb78e01f9` (pre-final-refresh active) → `af44c7fa21` (pre-2026-08-27 active) → `4edc96188b` (pre-final-refresh active) → `b7d23d5569` (pre-final-refresh-2 active) → `a34bde06de` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch inspected; this catalogue pass changes only `peter/patch-catalog/` documentation.
- Motivation: Hindsight intentionally queues recall from turn *N* for injection on turn *N+1*. The preceding short-input gate incorrectly evaluated the *N+1* acknowledgement (for example, `ok`) and discarded/cancelled turn *N*'s already completed or slow recall.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: provided post-commit verification: `/opt/hermes-agent/venv/bin/python -m pytest tests/plugins/memory -q -o 'addopts='` — **480 passed**. Two independent reviewers found no blockers; the second explicitly checked the slow (>3-second) prior-turn race.

## Local patch summary

This is the corrective follow-up to local patch `b0c1ab57c`. `recall_min_input_chars` now gates only **starting a new** automatic recall in `queue_prefetch()`; it no longer clears a completed `_prefetch_result` or advances the generation counter in `_skip_short_auto_recall()`.

`prefetch()` therefore continues to consume the prior turn's cached result even when the current message is short. If the prior prefetch is still running, it remains eligible to finish: a short acknowledgement that reaches the prefetch wait timeout gets no immediate context but does not cancel the turn-*N* request or prevent its result from being available for the following turn. The schema/help text and focused regressions were updated for completed-cache, in-flight, and deliberately slow prior-turn cases.

## Upstream overlap

| Kind | # | Title | Current upstream state / maintainer signal | Conflict risk | Relationship to this patch |
|---|---:|---|---|---|---|
| PR | [#29865](https://github.com/NousResearch/hermes-agent/pull/29865) | fix(hindsight): key prefetch cache by session and query | Open; `teknium1` review says the unqualified cache leak is real, but rejects exact current-query matching because the supported lifecycle is end-of-turn warming → next-turn consumption; asks for lifecycle-aware coverage. | **High semantic / same provider and test file** | Closest item. Its review explicitly validates the local patch's core invariant: recall from *N* must be consumable on *N+1*, not matched to the acknowledgement text. Its proposed cache-key implementation is not a replacement. |
| PR | [#18372](https://github.com/NousResearch/hermes-agent/pull/18372) | fix(memory): guard stale recall and unsafe learning | Open; `teknium1` says the stale-Hindsight premise is real but requests the Hindsight work be split and reworked, including correct background-warming behavior. | **High semantic / broader cross-layer change** | Related stale-recall work, but it introduces synchronous recall and unrelated runtime/skill changes. It does not provide this short-acknowledgement preservation contract. |
| Issue / duplicate PRs | [#43891](https://github.com/NousResearch/hermes-agent/issues/43891), [#43998](https://github.com/NousResearch/hermes-agent/pull/43998), [#42232](https://github.com/NousResearch/hermes-agent/pull/42232) | configurable Hindsight prefetch join timeout | All open. `teknium1` identifies incomplete parsing/join-scope behavior in both PRs; #43998 is labelled duplicate of #42232. | **Medium mechanical** | They alter the same `prefetch()` wait neighborhood and make slow recalls more likely to span turns, but they do not address whether a short *N+1* must preserve turn-*N* work. Reconcile this lifecycle invariant if either lands. |

## Notes on most relevant upstream items

- **#29865 is direct upstream evidence for the local semantics.** Its maintainer review states that the provider queues the completed turn's `user_text` and consumes prefetch on the next turn's message. That is exactly why a 20-character check on the later acknowledgement must not invalidate the earlier query/result. The local patch is narrower than #29865: it retains that supported lifecycle while still suppressing a *new* recall for a short input.
- **The slow-path test matters independently of the existing 3-second join.** A short acknowledgement can observe no result after the join timeout; it must still leave the earlier background request live. The patch's slow regression asserts this without depending on a specific timeout setting, so it remains valid if #43891/#43998/#42232 change the configured wait.
- **No exact upstream proposal was found.** Authenticated GitHub issue/PR searches for Hindsight/prefetch/recall and short-query memory found no open item proposing `recall_min_input_chars` with the completed-and-in-flight prior-turn preservation rule. Authenticated GitHub code search for `recall_min_input_chars` returned zero upstream matches.

## Recommendation

Keep `78568898e` locally and treat it as the required corrective successor to `b0c1ab57c`, not an independent competing policy. Upstream overlap is **high** in the Hindsight prefetch lifecycle area, especially #29865/#18372, but no upstream item currently replaces this fix. On rebase, preserve the explicit invariant that the length gate governs only creation of a new recall; it must not erase or cancel eligible prior-turn work. Re-run the Hindsight memory suite, including the completed, in-flight, and slow (>3-second) acknowledgement regressions, after any merge touching `prefetch()` or `queue_prefetch()`.

## Raw authenticated search queries used

- `gh search issues hindsight --repo NousResearch/hermes-agent --limit 100`
- `gh search issues 'prefetch recall' --repo NousResearch/hermes-agent --limit 100`
- `gh search issues '"short query" memory' --repo NousResearch/hermes-agent --limit 100`
- `gh search prs hindsight --repo NousResearch/hermes-agent --limit 100`
- `gh search prs 'prefetch recall' --repo NousResearch/hermes-agent --limit 100`
- `gh search prs '"short query" memory' --repo NousResearch/hermes-agent --limit 100`
- `gh api /repos/NousResearch/hermes-agent/issues/{29865,18372,43891,43998,42232}` and `gh pr view {29865,18372,43998,42232}`
- `gh api /search/code?q=repo:NousResearch/hermes-agent recall_min_input_chars`

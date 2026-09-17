# Preserve provider retry output caps

- Date: 2026-08-03
- Repo: `NousResearch/hermes-agent`
- Patch ref: `2a381430193d652989e064fc91e856b45ec5f217` → `555d077a4` (pre-2026-08-09 active) → `e506a696e3` (pre-2026-08-14 active) → `e923efb3f6` (pre-refresh active) → `c9519c86e3` (pre-2026-08-23 active) → `0339000898` (historical; dropped 2026-08-23)
- Branch: `peter/hermes-patches`
- Local status: dropped during the 2026-08-23 rebase after a current-code contract audit.
- Motivation: the chat-completions transport resolves the one-shot `ephemeral_max_output_tokens` cap before calling provider profile hooks, but profile hooks can add top-level kwargs afterward. A profile that computes `max_tokens` therefore had no way to preserve a smaller retry/overflow cap instead of overwriting it with its normal value.
- Changed files: `agent/transports/chat_completions.py`; `providers/base.py`; `tests/agent/transports/test_chat_completions.py`
- Tests / verification: `scripts/run_tests.sh tests/agent/transports/test_chat_completions.py -q` passed 33 tests when the patch was dry-run cherry-picked onto `origin/peter/hermes-patches`; `git diff --check` passed.

## Local patch summary

`ChatCompletionsTransport.build_kwargs()` now passes the already-resolved `ephemeral_max_output_tokens` value into `ProviderProfile.build_api_kwargs_extras()`. The base hook documents this optional transport metadata. Provider profiles that supply top-level `max_tokens` can use it to retain the smaller one-shot cap on retry or overflow requests.

The intended regression was to use a profile override that returned top-level `max_tokens`. The test actually returned the value in the `extra_body` half of the hook tuple, so its final assertion was satisfied by the transport's already-existing ephemeral-first resolution rather than by this patch.

## Upstream overlap and rebase risk

The 2026-08-23 audit found that current upstream initially resolves output caps in priority order `ephemeral > user > profile default`, but profile top-level extras are merged afterward and can still overwrite that value. No bundled provider profile reads `ephemeral_max_output_tokens` from `build_api_kwargs_extras()` context, so the local metadata extension has no production consumer. The patch was therefore retired as unused/speculative metadata, not as upstream-equivalent ordering. The only asserted behavior remains present after removing it because the regression did not place a competing value in the top-level tuple.

Mechanical conflict risk is low today, concentrated in the transport's profile-hook call and its base contract documentation. Recheck this invariant if upstream changes request-kwargs ordering: a provider-specific top-level cap must not erase a smaller retry cap merely because profile extras are merged later.

## Recommendation

Keep this report as historical context. If a future provider genuinely emits a top-level output cap after transport resolution, fix the ordering directly—make the ephemeral cap authoritative after profile extras merge—and add a regression that places the competing value in the hook's top-level tuple. Do not restore this unused metadata-only patch.

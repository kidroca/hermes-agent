# Preserve provider retry output caps

- Date: 2026-08-03
- Repo: `NousResearch/hermes-agent`
- Patch ref: `2a381430193d652989e064fc91e856b45ec5f217` → `555d077a4` (active on `peter/hermes-patches`)
- Branch: `peter/hermes-patches`
- Local status: cherry-picked onto the reconciled patch branch; catalogue entry is a separate follow-up commit.
- Motivation: the chat-completions transport resolves the one-shot `ephemeral_max_output_tokens` cap before calling provider profile hooks, but profile hooks can add top-level kwargs afterward. A profile that computes `max_tokens` therefore had no way to preserve a smaller retry/overflow cap instead of overwriting it with its normal value.
- Changed files: `agent/transports/chat_completions.py`; `providers/base.py`; `tests/agent/transports/test_chat_completions.py`
- Tests / verification: `scripts/run_tests.sh tests/agent/transports/test_chat_completions.py -q` passed 33 tests when the patch was dry-run cherry-picked onto `origin/peter/hermes-patches`; `git diff --check` passed.

## Local patch summary

`ChatCompletionsTransport.build_kwargs()` now passes the already-resolved `ephemeral_max_output_tokens` value into `ProviderProfile.build_api_kwargs_extras()`. The base hook documents this optional transport metadata. Provider profiles that supply top-level `max_tokens` can use it to retain the smaller one-shot cap on retry or overflow requests.

The regression test uses a profile override that returns top-level `max_tokens`. It confirms the hook receives `4_096` and the final outgoing kwargs retain that cap rather than the ordinary `131_072` value.

## Upstream overlap and rebase risk

Exact source searches for `ephemeral_max_output_tokens` and the `build_api_kwargs_extras`/`max_tokens` combination found no matching upstream patch on 2026-08-04. The patch is a small additive contract change: the base profile hook already accepts `**context`, so profiles only need to opt in when they emit top-level output caps.

Mechanical conflict risk is low today, concentrated in the transport's profile-hook call and its base contract documentation. Recheck this invariant if upstream changes request-kwargs ordering: a provider-specific top-level cap must not erase a smaller retry cap merely because profile extras are merged later.

## Recommendation

Keep active patch `555d077a4` until upstream either forwards the same retry-cap metadata to provider profile hooks or makes the retry cap authoritative after provider extras are merged. On rebase, retain the regression covering a profile-generated `max_tokens` value alongside a smaller ephemeral cap.

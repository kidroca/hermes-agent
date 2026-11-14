# Early Slack plugin selection — review candidate

## Status

- Branch: `feat/slack-early-admission-current`.
- Exact base: `8bac3a7fde9378a009bc72c4a307b37c95f91fb4` (fetched `origin/peter/hermes-patches`).
- Source commit: `9c438148494e6b73bbe8be5e1012938ebe8596df`.
- Isolated worktree: `/Users/hermes/hermes-slack-admission-current`.
- November 14: Peter approved local fast-forward integration into `peter/hermes-patches`; publication remains reserved for Peter using `kidroca`.
- Activation pending: no gateway restart, consumer activation, or live Slack acceptance is included. The on-disk source must not be described as verified loaded by the running gateway.
- Parent reran scoped regression: **648 passed, 0 failed across 42 per-file subprocesses**, including 39 new contract cases.
- Additional platform/session run: **100 passed, 0 failed across 5 files**, including a rerun of the same 39 hook cases; these counts are not disjoint.
- All **15 pinned code-health checks passed** against the exact base, including Ruff; boundary lint and whitespace checks passed.
- Independent review found no confirmed hook defects. Remaining test gaps: real session-bookkeeping root/follow-up integration and broader multi-workspace own-identity cases. Live tests are deferred until source and consumer activation.

## Purpose and upstream overlap

The pinned base has `pre_gateway_dispatch`, but that occurs after Slack bot/mention eligibility and cannot select a first, otherwise-ineligible channel root. Ordinary hook dispatch suppresses callback failures/None, which is unsuitable for a fail-closed admission decision. No equivalent early selection hook was found in this base. No network/upstream PR search was performed under the offline task constraint; future upstream equivalence remains unverified.

Keep CI-card classification, canonical API validation, claim storage and automation actions in the separate `hermes-gitlab-automation` consumer. This patch supplies only a generic eligibility seam and native Slack integration. Drop/reconcile it when an upstream equivalent preserves the same authorization, profile and failure semantics.

## API and implementation

Register `ctx.register_hook("pre_platform_message", callback)`. Immutable string kwargs:

- `platform` (`"slack"` for this integration)
- `profile_home` (receiving adapter's construction/transport-owner profile)
- `team_id` (Slack workspace)
- `bot_user_id` (own Slack user identity for the workspace)
- `event_json` (normalized event snapshot including available blocks/attachments)

Return exactly `"delegate"`, `"skip"`, or `"select"`. No registration delegates unchanged native eligibility. Any skip, exception, or invalid return vetoes this event, including after another callback selects it. Otherwise any select wins. Narrow signatures and async callbacks work. Async callbacks honor the configured hook timeout (zero disables it); synchronous callbacks must be short/nonblocking. Caller cancellation propagates.

`gateway/platforms/inbound_selection.py` binds a copied context and explicit home override. The strict dispatcher is separate from fail-open observer dispatch. Its published capability import is `gateway.platforms.inbound_selection.bind_inbound_selector` (also in the public API manifest/generated docs).

`plugins/platforms/slack/adapter_admission.py` extracts the existing early prefilter and applies selection after edit normalization, replay and ignored-channel filtering. Native self identity is tracked by team, including bot IDs. `select` bypasses only bot/mention eligibility; native channel restrictions, other-user-address rules, disabled DMs, authorization, subtype restrictions, deduplication and downstream bot-loop checks remain. Source user/team/bot provenance and transport reference are retained. A selected first message uses native root-timestamp thread routing.

The existing synthetic-reaction path now passes a trusted caller keyword rather than accepting `_hermes_force_process` from raw event data. Reaction tests were adapted; a spoofed raw flag cannot select an event.

## Consumer prerequisites and limitations

The running runtime must include the source commit above (or its equivalent), not merely accept registration of an unknown hook name. Install the consumer in the transport-owner profile, not just a later routed profile. The public helper import is a capability check; activating new source remains a separate operator action.

Selection is **not authorization**. Userless bot posts can still be rejected. Tests prove identified senders remain rejected without native permission and may pass an explicit `SLACK_ALLOWED_USERS` match; selection does not enable `allow_bots` or allow-all or manufacture a user ID.

Do not consume durable automation claims in this early hook: downstream channel/user authorization can still reject the event. Claim only at an appropriately authorized downstream stage. No new post-authorization lifecycle hook is introduced here.

Live Slack delivery, a running gateway, isolated plugin-host deployment, and the separate consumer are not acceptance-tested by this patch. No credentials, network, model requests, settings changes, runtime restarts, or deployments were used.

## Verification

RED/GREEN slices covered missing hook behavior, selected root delivery, self-echo/raw-flag guards, bot provenance, profile binding (including environment-home changes), and zero-disabled async timeout handling. The contract suite uses an actual temporary out-of-tree `ctx.register_hook` plugin. It also covers delegated native human mentions, invalid/error vetoes, callback recovery on a later event, multi-hook veto ordering, async timeout, channel restrictions, adapter authorization, and real runner authorization decisions.

Final scoped command (from the candidate worktree):

```sh
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin \
  HOME=/Users/hermes/.hermes/profiles/operator/cache/scratch/slack-admission-test/home \
  TMPDIR=/Users/hermes/.hermes/profiles/operator/cache/scratch \
  HERMES_RUNTIME_DIR=/Users/hermes/.hermes/profiles/operator/cache/scratch/slack-admission-test/runtime \
  HERMES_PYTHON=/Users/Shared/AI/hermes-agent/.venv/bin/python \
  scripts/run_tests.sh tests/plugins/platforms/slack/test_early_selection.py \
  tests/gateway/test_slack*.py tests/hermes_cli/test_plugins.py -q -j 6
```

Result: 42 files, 648 passed, 0 failed. Prescribed runner uses a clean per-file environment and its isolated pytest homes. This is scoped verification, not the full repository suite.

`python scripts/boundary_lint.py` passed; `git diff --check` passed; the public API documentation generator completed successfully.

`python scripts/check --base 8bac3a7fde9378a009bc72c4a307b37c95f91fb4` was attempted offline and refused to proceed: it requires Ruff **0.15.22**, while the available binary is **0.15.14**. No network install or version bypass was used. The separately requested non-Ruff checks passed with:

```sh
python scripts/check --base 8bac3a7fde9378a009bc72c4a307b37c95f91fb4 \
  --only footguns,shebangs,no-tmp,detached-spawns,install-root,config-writers,config-readers,os-marker-fakes,agents-md,case-collisions,lazy-deps,profile-archives,blob-size
```

Result at the original November 13 checkpoint: `scripts/check: 13 checks, ok`. This historical partial result was superseded on November 14 by a successful complete run:

```sh
/Users/Shared/AI/hermes-agent/.venv/bin/python scripts/check --base 8bac3a7fde9378a009bc72c4a307b37c95f91fb4
```

Result: `scripts/check: 15 checks, ok`, including pinned Ruff and code health (zero blocking/advisory findings). Parent also reran boundary lint and `git diff --check` successfully.

Additional prescribed-runner invocation, using the same isolated environment as above:

```sh
scripts/run_tests.sh tests/plugins/platforms/slack \
  tests/gateway/test_session_group_peers.py \
  tests/gateway/test_session_group_controls.py \
  tests/gateway/test_session_continuity.py -q -j 6
```

Result: 5 files, 100 passed, 0 failed. The 39 early-selection cases overlap the 648-test run.

An offline temporary probe used the actual registered root-only selector, native adapter handlers, canonical `build_session_key`, and outgoing thread resolver. A selected CI root followed by a different, explicitly mentioning human sender produced identical profile/workspace/channel/root session keys and identical original-root reply destinations; bot/human provenance remained distinct. The probe mocked final delivery and did not create a real model session. It is not a durable session-bookkeeping or live Slack acceptance test.

With `strict_mention=true`, unmentioned human follow-ups remain ineligible: selecting a root does not permanently exempt its thread from native mention rules. Full native-session follow-up and multi-workspace own-identity tests remain deferred, not claimed as passed.

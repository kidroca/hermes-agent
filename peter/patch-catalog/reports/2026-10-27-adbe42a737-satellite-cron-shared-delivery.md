# Shared cron delivery for satellites with local sessions

Date: 2026-10-27. Source: `adbe42a737e8b8aac7701b4d826b3a5e44b60e8b`.
Base: `436fc0c13056dd44979c17413cee3552ff5b9a15`.
Branch: `peter/cron-shared-delivery-candidate`.
Candidate worktree removed after integration; the candidate branch remains available.

Integrated into canonical `/opt/hermes-agent` on `peter/hermes-patches` by an
authorized fast-forward to `b7a5731dd2`. Runtime activation receipt follows below.
No push or publication is authorized. Author and committer: `🤖 Codex`, retaining
the configured Git email.

## Root cause

`gateway.run._drain_restart_safe_cron_deliveries()` selected `SharedRouteAdapters`
only for an empty satellite adapter map. A local session adds `Platform.LOCAL`
to that map through `gateway.session_local_recovery.local_adapter_map`, without
giving the satellite a bot credential. That nonempty map skipped the wrapper.
`cron.scheduler.drain_delivery_queue()` passed it unchanged through
`_deliver_result()` to `_resolve_target_transport()`. The latter correctly did
not see a shared grant and applied the satellite's native `enabled: false`,
returning `platform 'discord' not configured/enabled`.

The existing shared resolver and authorized-transport forwarding are effective
when the wrapper reaches them; there is no class-identity or map-conversion
defect in the reproduced path. The multiplex ticker had the same emptiness test.

`has_credential_platform()` now excludes LOCAL from credential ownership. Both
handoffs retain the existing target-aware shared view. Stable
`_profile_bot_platforms` is recorded before connecting a secondary bot, initialized
with the runner, passed to the ticker, and removed on profile teardown. A bot
that disconnects, fails connection, or is reconnecting remains its profile's
credential boundary; the primary bot cannot be borrowed meanwhile.

No target/profile authorization or native enabled checks were removed. Unmatched,
disabled, wrong-profile, and guild-only routes remain closed. No credentials,
profile config, production job state, delivery receipts, or production database
rows were changed. The paused-session/not_found issue is untouched.

## Evidence and limits

The specified production delivery row was read with SQLite `mode=ro` and
`query_only=ON`: status failed, owner PID 1670425, exact reported platform error.
Persisted gateway state reports Discord connected, lad-studio served, and code
SHA `436fc0c13056dd44979c17413cee3552ff5b9a15`, matching the candidate base.
PID 1670425 was absent from this environment's `/proc`; loaded Python modules and
that historical process's adapter-map contents could not be inspected. This is
a reproduced source defect consistent with production evidence, not proof of
the historical map contents. No oMLX/SSH check or production cron was repeated;
the satellite `.env` was not inspected.

## Minimal patch

Production: 25 additions / 7 deletions across seven files: scheduler preflight
and provider; gateway drain, adapter lifecycle, bootstrap, runtime initialization,
and profile teardown. Tests: 165 added lines across three files. No new delivery
mechanism or persistent format is introduced.

## RED to GREEN and independent review

On unchanged base source, the new real queue-drain/resolution regression returned
failed instead of delivered for an exact guild+chat route and a LOCAL-only
satellite with Discord explicitly disabled and no satellite credential. Its log
contained the exact production error. Six controls passed on that base.

Final canonical runner: **147 passed, zero failed, nine files**, Python 3.11.15.
Disposable HOME, HERMES_HOME and HERMES_RUNTIME_DIR were used, alongside per-test
temporary homes; the repository home-I/O guard remained enabled. Only synthetic
credentials and adapters were used. Test files:

- `tests/gateway/test_cron_shared_queue_delivery.py`
- `tests/cron/test_cron_shared_tick_delivery.py`
- `tests/gateway/test_multiplex_adapter_registry.py`
- `tests/cron/test_scheduler_provider.py`
- `tests/gateway/test_multiplex_hot_serve.py`
- `tests/gateway/test_runner_fatal_adapter.py`
- `tests/gateway/test_cron_delivery_housekeeping.py`
- `tests/cron/test_cron_multiplex_shared_route_delivery.py`
- `tests/cron/test_restart_safe_worker.py`

Invocation pattern, with disposable scratch directories assigned to `test_home`
and `test_runtime`: `HOME="$test_home"
HERMES_HOME="$test_home/hermes"
HERMES_RUNTIME_DIR="$test_runtime"
HERMES_PYTHON=/opt/hermes-agent/.venv/bin/python bash scripts/run_tests.sh
<the nine files above> -j 2 --file-retries 0`.

The queue regression exercises enqueue, profile-scoped gateway drain, real
delivery resolution/router, fake primary send, terminal status and a second
drain. It verifies one send for the authorized and ordinary-primary cases,
no primary sends for denied routes or an owned disconnected bot, and no duplicate.
Additional tests cover ownership before a failed connect and ticker propagation.

`python scripts/check --base 436fc0c130 --staged`: all **12 checks passed**;
`git diff --check` passed. The existing commit hook passed with pinned Ruff
0.15.22 supplied through `uvx --from ruff==0.15.22`; no hook was bypassed.
Canonical tests required sandbox escalation because the runner uses `/var/tmp`.

Independent read-only review of exact committed range
`436fc0c130..adbe42a737`: **no blockers**. Review findings were corrected before
commit: synchronize adapter-loop startup and add ownership/ticker tests. The
reviewer inspected committed blobs; test execution receipts belong to the parent.

## Existing upstream correction

This is a narrow backport/adaptation, not another implementation:

- [01dffd3b478f](https://github.com/NousResearch/hermes-agent/commit/01dffd3b478fd2a52cc427daaa6db481ac8b387e): LOCAL-aware shared adapter selection.
- [f18ef0a15c1d](https://github.com/NousResearch/hermes-agent/commit/f18ef0a15c1d4b706a2f2d306d03d68da6bf1dce): initial reconnecting-bot guard.
- [18e16bdd7d01](https://github.com/NousResearch/hermes-agent/commit/18e16bdd7d01c082760a0e59e73a72be768874de): stable ownership guard; unrelated relay and general authorization changes excluded.
- [PR #139827](https://github.com/NousResearch/hermes-agent/pull/139827): alternative proposal, closed unmerged.
- [PR #116649](https://github.com/NousResearch/hermes-agent/pull/116649): earlier authorized-transport forwarding correction, already in the base.
- [Issue #143953 B](https://github.com/NousResearch/hermes-agent/issues/143953), [#115656](https://github.com/NousResearch/hermes-agent/issues/115656), and [PR #108428](https://github.com/NousResearch/hermes-agent/pull/108428): symptom/prior fixes checked; old tests alone did not cover the LOCAL-only queued case.

Latest upstream source inspected at `3f2b1722b1e15b12e9ca199a19cb04012493288a`
contains the stronger ownership-aware implementation. Direct rebase overlap is
likely in the seven touched source files. Drop this candidate when the maintained
base includes equivalent upstream behavior and the authorization tests pass.

## Approved integration and activation

Peter separately authorized integration and gateway restart through the Windows
WSL root path. The root identity probe succeeded for distro Ubuntu. The command
runner belongs to `/init.scope`, outside the target service's cgroup
`/system.slice/hermes-gateway.service`.

Canonical `peter/hermes-patches` fast-forwarded to `b7a5731dd2` without changing
the reviewed production/test blobs. Fresh integrated-checkout verification:
147 passed / nine files; all 12 checks passed with `scripts/check --staged`.
The working-directory check also found unrelated ignored desktop packager
archives; they were left untouched. Literal temporary paths in this report were
replaced with a scratch-directory invocation pattern before the staged check.

Installed `ExecReload=/bin/kill -USR1 $MAINPID` and `Restart=always` were verified.
At 2026-10-27 15:00:28 UTC, the approved WSL root path invoked
`systemctl reload hermes-gateway.service`. In Hermes this requests a graceful
restart, not an in-process reload: drain active work, exit, then systemd relaunch.
The old PID 1670425 entered draining and waited for an existing chat turn; no
force-kill, production-job rerun, or live delivery canary was requested.

The chat completed naturally. At 15:09:56 UTC Hermes logged the after-turn wait
complete with zero active work. Shutdown emitted its configured built-in home
channel notifications; no custom/test messages were sent. Idle-cache cleanup
exceeded its 30-second budget and continued; adapters disconnected before
systemd relaunched the gateway. No cleanup workaround was applied.

Activation verified at 15:12:39 UTC: service active/running, new PID **375348**,
service start 15:11:56 UTC, persisted gateway state running and loaded code SHA
**b7a5731dd2dfda8dfb6659a91ff21563ac6b9e8e**. Discord connected at 15:12:36 UTC
with writer PID 375348 and no platform error; lad-studio is among ten served
profiles. The final catalogue follow-up changes documentation only; production
and test blobs remain identical to the reviewed and loaded source.

## Separate live canary proposal — not authorized or executed

Under separate approval for the live send and temporary job state, use a
dedicated no-agent canary with a unique marker at the authorized satellite
destination; inspect its execution/delivery outcome and confirm only one
message. Do not rerun the existing production job. Runtime startup verification
alone does not establish live end-to-end cron delivery.

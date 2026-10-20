# Linux session ownership identity — local-only candidate

## Source and disposition

- Approved source: `72cfc15381ea7312142833263b97b7c521cfeb83` (`fix(sessions): 🛠️ Keep Linux ownership stable across clock steps`). Parent: `410c7114c25e578698ad2357ccb3715de4a56f0d`.
- Candidate branch: `peter/ownership-clock-01`. **Not integrated into `peter/hermes-patches`, not pushed, not activated.** This catalogue receipt is documentation only; source preparation is separate from integration and activation. No live configuration, services or leases changed.
- Source delta: `hermes_cli/active_sessions.py` (+35/−1) and new `tests/hermes_cli/test_active_session_clock_identity.py` (179 lines): 214 additions, 1 deletion.

## Motivation and contract

Live Linux/WSL epoch-based `create_time` drift was observed in the handoff diagnosis. The exact comparison can prune a living canonical Bot Chat owner; isolated same-process and real-child regressions reproduced that failure. Historical production lease deletion was not observed. A caller's registry snapshot can itself trigger pruning.

New Linux leases store `process_start_time` as `linux-v1:<bootUUID>:<ticks>`, reusing `hermes_cli.web_server_lifecycle._process_start_marker` and its robust `/proc/<pid>/stat` parser. Identity comparison is exact, with no clock tolerance; start ticks distinguish PID reuse and the boot UUID guards reboot reuse. Unreadable identity for a new lease raises `ActiveSessionRegistryError`; unknown existing identity refuses strict operations and is retained by lenient reads rather than discarded.

Legacy numeric epoch entries and non-Linux behavior remain unchanged. Legacy leases retain their old clock sensitivity until turnover. Old strict readers reject the new string format (safe refusal): **this is not rolling-compatible**. Comments remain brief; the implementation reuses the existing parser rather than duplicating it.

## Verification receipt

Implementation verification supplied by the parent task (not rerun for this docs-only update):

- Canonical `scripts/run_tests.sh`, disposable HOME, retries disabled: **122 passed across 11 files, zero failures**. `HERMES_PYTHON=/home/kidroca/.hermes/cache/scratch/ownership-testenv-full/bin/python` (Python 3.14.7; PM-built dev/test/messaging environment).
- Files: `tests/hermes_cli/{test_active_session_clock_identity,test_active_sessions,test_active_session_exclusivity}.py`; `tests/tools/test_bot_live_owner_delivery.py`; `tests/tui_gateway/{test_bot_live_owner_delivery,test_bot_relay_methods,test_retirement_admission,test_notification_turn_release}.py`; `tests/gateway/{test_host_rendezvous,test_peer_dm_into_open_bot_chat}.py`; `tests/cron/test_cron_live_bot_delivery.py`.
- New regression file: **14 tests**. Core same-process and real-child drift regressions failed before the change and passed afterward. Coverage includes exact boot/tick mismatch, unusual process names, unreadable/malformed identities, conservative retention, legacy comparison and dead-child pruning.
- Precommit `scripts/check --staged --base HEAD` and fresh postcommit `scripts/check --commit HEAD --base HEAD^`: all 11 checks passed; health: 0 blocking, 0 advisory. Ruff and diff checks passed. The 122-test receipt was repeated successfully on the committed source.
- Independent read-only precommit snapshot review: **APPROVE**, no blockers; reviewer did not rerun tests.

## Upstream overlap and retention

Prior upstream glance supplied by the parent task found main `d87e7536e042` still affected. No upstream searches or publication were performed for this report.

- [Issue #105714](https://github.com/NousResearch/hermes-agent/issues/105714), Kanyuchi, September 8: open.
- [Fix PR #105720](https://github.com/NousResearch/hermes-agent/pull/105720), liuhao1024, September 8: open, unmerged, conflicting, no formal reviews in that snapshot.
- Alternative #105722: closed, superseded.

This implementation is inspired by the upstream work, **not a cherry-pick**. Semantic conflict risk is **high**: the same `active_sessions.py` identity hunks overlap. Keep the candidate local; drop it only after an upstream equivalent contract and regression coverage are verified, not merely because a related PR merges.

## Separately authorized activation gate

Activation requires an explicitly authorized idle window: drain active sessions; stop all old registry readers/writers sharing the registry, including CLI, TUI, serve and background bridges; integrate the candidate into the canonical checkout; restart relevant owners; reacquire fresh Linux leases. **Do not delete live leases.** Mixed old/new readers are not a safe rollout.

Live end-to-end phone, voice, PWA and push acceptance remains reserved for the `proactive-hermes` follow-up. Neither those flows nor live activation are claimed by the unit/integration receipt above.

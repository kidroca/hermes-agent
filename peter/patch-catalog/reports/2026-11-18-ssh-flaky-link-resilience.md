# SSH terminal backend: flaky-link resilience

- Date: 2026-11-18
- Repo: `/opt/hermes-agent` (Peter's fork)
- Patch refs: `bda02a6a82` `af6cc9b1e9` `c8cd3d4e54` `9362a57c75` `9102ba95e1` `87db5c4cb7` `1b0980a3d7`
- Base: `peter/hermes-patches` @ `99a14664e4`; candidate branch `peter/ssh-flaky-link-resilience`
- Local status: reviewed candidate; integration and runtime activation pending Peter's approval
- Disposition: local patch; upstream publication not requested

## Motivation

On 2026-11-17 (17:52–19:56 EET) the lad-studio `ssh` terminal backend (WSL → Mac Studio over
Tailscale) was unusable for ~2 h during a WAN degradation (Mac-peer endpoint churn 16–29/30 min and
WireGuard handshake failures; Wi‑Fi ruled out: both endpoints measured 100 % on wired `en0`).
A gateway restart did not help. Every command first re-ran a ~6.7 MB support-file upload to its
146 s timeout (a failed sync never rate-limits itself, #39945), the lifecycle guard's remote script
read triggered the same sync under a 30–60 s deadline ("process-identity probe wedged"), and the
mux master had no keepalives.

## Changes (production +83/−8 lines in 5 files, comments included; tests and docs separate)

| Commit | Behaviour |
|---|---|
| `bda02a6a82` | `ServerAliveInterval=15`, `ServerAliveCountMax=3` on terminal-backend ssh (gateway transport values) |
| `af6cc9b1e9` + `87db5c4cb7` | First sync failure still retries next cycle; from the 2nd consecutive failure, non-forced cycles back off 30→60→120→240→300 s; success resets; `force=True`/`HERMES_FORCE_FILE_SYNC` bypass |
| `c8cd3d4e54` + `9102ba95e1` + `1b0980a3d7` | `skip_file_sync()` contextvar + `may_be_file_synced()`; guard reads skip sync only for absolute paths certainly outside the detected remote `~/.hermes` (case-, `//`- and NFC-insensitive); relative/`~` paths, a guessed home and backends without the hook keep syncing |
| `9362a57c75` | Terminal guard timeout text no longer blames the identity probe (execute_code wording kept: its deadline wraps only that probe) |

Accepted residuals: a symlink outside the sync tree pointing into it is read unsynced; while sync is
backing off (≤ 300 s) remote commands may see stale skills/credentials (previously they did not run);
a mux master idle > 45 s on a dead link now dies and takes its sessions with it; ssh_config cannot
loosen the keepalive values; a master started before activation keeps old options until
ControlPersist (300 s) expires it.

## Verification

- TDD: every new test observed failing first. New: `tests/tools/test_file_sync_backoff.py` (6),
  `tests/tools/test_guard_read_skips_file_sync.py` (20), keepalive case in `test_ssh_environment.py` (2).
- `scripts/run_tests.sh` with isolated HOME: tools/cron/restart-loop guard selection 3376 passed;
  final `-k "sync or ssh or guard"` 1756 passed. Failures in voice_mode, termux, subprocess_stdin_guard,
  bot_desktop_idle and the `fal_client` import reproduce on the unmodified base.
- Black-hole relay against the real Mac with dedicated masters: keepalive master → stalled mux client
  returned in 63 s and the master exited; no-keepalive master → still hung at 159 s, master "running".
- Live lad-studio smoke through the patched worktree: cold env 77.1 s, warm command 0.4 s, exit 0.
- Two independent reviews: first raised relative-path, case, unset-home and SSH-path coverage
  issues (all fixed in `9102ba95e1`); final review: no blockers; `//` and NFC notes fixed in `1b0980a3d7`.

## Upstream overlap

| Kind | # | Relevance | Decision |
|---|---:|---|---|
| PR | 62800 | ssh keepalives, 13 files, configurable; stale, author calls it a drive-by | own 3-line version; adopt upstream if it lands |
| Issue/PR | 39945 / 40048 | established immediate retry after one failure | contract preserved |
| Issue | 139383 | sync restarts whole upload on slow remotes | addressed earlier by `f6febd69a7`; backoff complements it |
| Issue | 149085 | guard wedges on identity probe (different cause) | message fix only |

Upstream main (1364 commits ahead at merge-base `ce4de3cdc2`) touches `base.py`/`ssh.py`/`terminal_tool_guards.py`
lightly (cwd-fallback work); expect small textual conflicts at the next rebase, no semantic overlap.

## Phase 2 (not implemented)

Compression/smaller upload batches (cold start is 77 s at 143 ms RTT) and isolating the remote sync
root from the Mac's own `~/.hermes` (collisions, full-tree sync-back, absolute-symlink extraction failure).
Plan: `~/.hermes/plans/2026-11-18_121500-ssh-backend-flaky-link-resilience.md`.

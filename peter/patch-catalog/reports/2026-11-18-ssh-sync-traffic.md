# SSH file sync: move only what the remote lacks

- Date: 2026-11-18
- Repo: `/opt/hermes-agent` (Peter's fork)
- Patch refs: `cbaa49a50d` `1618f6eb73` `dca9c5dfaf` `e41f74bc71` `bd2fd93d6e` `0bfecd9cab` `32be5d0450`
- Base: `peter/hermes-patches` @ `46d3526184`; candidate branch `peter/ssh-sync-scope`
- Follows: [SSH flaky-link resilience](2026-11-18-ssh-flaky-link-resilience.md) (Phase 2 of that plan)
- Disposition: local patch; upstream publication not requested

## Motivation

The lad-studio `ssh` backend (WSL → Mac over a transatlantic Tailscale link) moved far more data
than the work needed:

- **Upload:** a new `FileSyncManager` per session has no record of earlier pushes, so every cold
  start re-uploaded the whole support tree: 1860 files, 150.6 MB, all already on the Mac. The
  first command took 77 s on a healthy link; on a degraded one, the 16 MiB batches kept timing out.
- **Download:** teardown sync-back tars the entire remote `~/.hermes` (312 MB, 269 MB of it
  `cache/`) to apply a few changed files. lad-studio syncs no credential files and Peter uses
  only this host, so the download protects nothing.

Rejected: excluding `cache/web`, `cache/spillover` and `cache/delegation` from upload. Upstream
syncs them deliberately (`ee8cbfdc03`, `8a770aae0d`, `35a0803a3b`): tools hand the model those
paths to page through with `read_file`, which runs on the remote. Also rejected: lowering the
16 MiB batch cap, which would slow every healthy cold start for a benefit only on a bad link.
Deleting the existing remote cache is out of scope (Peter: do not delete remote files on the
assumption that they are unused).

## Changes (production +113/−7 lines in 3 files, comments included; tests and docs separate)

| Commit | Behaviour |
|---|---|
| `cbaa49a50d` + `e41f74bc71` + `32be5d0450` | `terminal.sync_back` (default `true`); `false` skips the teardown download. An unreadable config keeps it on. Docs warn not to disable it on Modal/Daytona. |
| `1618f6eb73` + `bd2fd93d6e` + `0bfecd9cab` | `FileSyncManager(remote_hashes_fn=…)`: one remote SHA-256 listing per manager, used for the first planning cycle only (cleared even if planning fails). A remote file whose bytes equal the host's is recorded as pushed and not uploaded. SSH lists only the synced roots (two levels under `cache/`) with one `sh -c` call (sha256sum or macOS shasum, NUL-safe find/xargs, 30 s timeout). A failed listing logs once and falls back to a full upload. |
| `dca9c5dfaf` + `bd2fd93d6e` + `0bfecd9cab` | gzip on the tar upload stream, only once the listing has shown `gzip` on the remote; otherwise the original uncompressed command. The upload deadline still scales with uncompressed bytes. |

Accepted residuals:
- A remote copy whose bytes match but whose file mode differs is no longer re-pushed, so the mode is not corrected.
- Files directly at the top of `~/.hermes` are not listed and always upload.
- A tar that has `gzip` on PATH but no `-z` support (an exotic BusyBox build) would fail the upload.
- With `sync_back: false`, remote edits to synced files stay remote, and the next session's upload overwrites them.

Peter's lad-studio profile sets `terminal.sync_back: false`.

## Verification

- TDD: each new test was observed failing first. New files: `test_file_sync_back_optout.py`,
  `test_ssh_sync_remote_hashes.py` and `test_ssh_upload_compression.py`.
- Each functional commit was tested on its own in a detached worktree. The final focused selection
  (`-k "sync or ssh or modal or daytona or vercel or credential"`) passed 1167 tests. Earlier
  broader selections had failures in subprocess_stdin_guard, bot_desktop_idle, webapp_private_launch
  and user_providers_model_switch, plus the `fal_client` import error. All of these reproduce on
  the unmodified base.
- Live, against the real Mac:
  - The listing returned 5604 files in 0.97 s across 8 roots, and showed gzip present.
  - A lad-studio cold start uploaded 0 bytes and its first command took **3.9 s**, down from 77.1 s; warm commands took 0.4 s.
  - A 0.98 MB probe file was uploaded compressed and arrived byte-identical, then was removed from both sides.
  - gzip compressed web-cache files 5.9×, and macOS bsdtar extracted them intact.
- Two independent reviews. The first raised the gzip fallback, stale-listing and listing-scope
  issues, an unreadable config, and the sandbox warning. The final review found no blockers;
  its notes on failed planning and out-of-base paths are fixed in `0bfecd9cab`.

## Post-deployment fix (`32be5d0450`)

The first live gateway run after the restart still downloaded the whole tree: stall capture
`20261118T181706Z` was a child of the restarted gateway. The gateway's process HERMES_HOME is the
default profile, and each turn binds its profile in a ContextVar. Tools inherit that binding via
`copy_context`, but teardown runs on the idle-cleanup thread with no scope, so `load_config()`
there read the default profile and ignored lad-studio's `sync_back: false`. The pre-merge live
test ran with lad-studio's HERMES_HOME as the whole process home, so it could not catch this. The
fix resolves the setting in `FileSyncManager.__init__`, inside the creating turn. A review found
no blockers. `terminal.sync_back_max_bytes` and the sync-back lock path still resolve at teardown
(pre-existing upstream behaviour with the same cross-profile limitation); left as is.

## Upstream overlap

Not researched (local-only, per Peter's scope). This touches the same `FileSyncManager` and
`_ssh_bulk_upload` as the local `f6febd69a7` and the flaky-link patches, so rebase them as one family.

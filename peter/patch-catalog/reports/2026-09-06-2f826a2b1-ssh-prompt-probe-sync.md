# Skip SSH file sync for prompt metadata probes

- Date: 2026-09-06
- Repo: `NousResearch/hermes-agent` (local fork worktree)
- Patch base: `a042aa4c08f0d510757d2b0cb8507be2baac3138`
- Patch ref: `2f826a2b19027547b3af2475fde16ff08d7a49f4`
- Branch: `peter/hermes-patches`
- Local status: patch commit inspected cleanly; catalogue files are the only intended worktree changes from this pass
- Motivation: fresh `lad-studio` sessions and model changes stalled before inference because every prompt metadata probe constructed a normal `SSHEnvironment` and forced an upload of 1,319 files / 89.9 MiB, although the probe only reads `uname`, `whoami`, and `pwd`.
- Changed files: `agent/prompt_builder.py`, `tools/terminal_tool.py`, `tools/environments/ssh.py`, `tests/tools/test_ssh_probe_file_sync.py`
- Tests / verification supplied with the patch: TDD red with 2 expected failures; 145 passed and 5 skipped across focused/changed-area tests; Ruff clean; `py_compile` clean; `ty` retained the same 28 diagnostics as the base. Live `lad-studio` probing returned Darwin/user/home/cwd; a fresh first message completed in 13.94s and a `gpt-5.6-luna` model override completed in 9.30s.

## Local patch summary

The patch introduces a process-local `sync_files: bool = True` constructor option on `SSHEnvironment`, forwards it through `_create_environment`, and sets it to `False` only in `_probe_remote_backend("ssh")`. With sync disabled, the temporary probe skips remote Hermes-directory creation, `FileSyncManager` construction, the forced initial upload, per-command sync checks, and sync-back. Default behavior remains unchanged for real SSH tool environments: initial forced synchronization, change detection before commands, and cleanup sync-back remain enabled.

The implementation is deliberately narrower than the exact upstream proposal: it changes only file-sync policy for this metadata-only call site. It does not add a user-facing setting, persistent state, probe-specific socket identity, or broader backend lifecycle behavior.

## Upstream overlap

Authenticated GitHub searches on 2026-09-06 found one exact open PR and several adjacent open PRs. No separate exact open issue was found.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#77933](https://github.com/NousResearch/hermes-agent/pull/77933) | fix(ssh): isolate prompt backend probes from file sync | 34 days | Zhou-Ruichen; `NONE`; no prior merged PRs found | No reviews, comments, or checks | 5 files, +150/-6 | **Very high / exact**: same three production files and same prompt-probe sync bypass | **Low-to-unknown currently**: exact and well-tested, but stale, GitHub reports `CONFLICTING`/`DIRTY`, and there is no maintainer signal |
| PR | [#72594](https://github.com/NousResearch/hermes-agent/pull/72594) | fix(runtime): clean up remote backend probes | 41 days | Christoffer91; `NONE` | One comment review from a contributor; no approval observed | 4 files, +100/-9; overlaps `agent/prompt_builder.py` | High mechanical, medium semantic: generic post-probe cleanup does not avoid SSH constructor-time upload | Unknown |
| PR | [#77508](https://github.com/NousResearch/hermes-agent/pull/77508) | fix(tools): stop one SSH session cleanup from killing other live sessions to the same host | 34 days | fangliquanflq; `CONTRIBUTOR` | No reviews or comments observed | 2 files, +120/-4; overlaps `tools/environments/ssh.py` | Medium-high mechanical; lifecycle/socket cleanup is adjacent rather than a replacement | Unknown |
| PR | [#100761](https://github.com/NousResearch/hermes-agent/pull/100761) | fix(ssh): make remote file sync work against BSD/macOS hosts | 5 days | patrykkopycinski; `NONE` | No reviews or comments observed | 11 files, +613/-24; overlaps `ssh.py` and `terminal_tool.py` | High mechanical in SSH/file-sync code, low semantic replacement risk | Unknown |
| PR | [#26323](https://github.com/NousResearch/hermes-agent/pull/26323) | fix(ssh): support macOS tar during file sync | 114 days | verybigdog; `CONTRIBUTOR` | Contributor sweeper said the bug remains relevant and requested test repair; no approval | 2 files, +177/-6; overlaps `tools/environments/ssh.py` | Medium mechanical, low semantic: tar portability applies when sync is enabled | Low-to-medium |

## Notes on most relevant upstream items

### #77933 is an exact upstream implementation

PR #77933 states the same root cause: prompt construction creates a normal SSH environment, so constructor-time directory setup and forced upload happen before the metadata command. It modifies `agent/prompt_builder.py`, `tools/terminal_tool.py`, and `tools/environments/ssh.py`, exactly the local production footprint.

Its approach is broader than `2f826a2b1`: a `probe_only` mode skips remote-home detection and session initialization as well as file sync, gives every probe an isolated ControlMaster socket, and explicitly cleans up the temporary environment on success and failure. Its tests cover cleanup/error paths and socket isolation. The local patch instead uses a narrowly named `sync_files=False` policy and preserves the rest of ordinary SSH construction. That makes the local change smaller and directly tied to the measured 89.9 MiB upload, while #77933 may eventually provide a more comprehensive probe-lifecycle replacement if refreshed and accepted.

As of this research pass, #77933 has no reviews, comments, or checks, has not been updated since 2026-08-03, and GitHub reports it conflicting with current main. The author has no discoverable merged PRs in this repository. Exact overlap is strong evidence of upstream awareness, not evidence that merge is imminent.

### #72594 and #77508 explain why a future replacement needs comparison

#72594 adds generic remote-probe cleanup, but cleanup occurs after SSH construction and therefore cannot prevent the initial forced upload. It is complementary rather than sufficient for this incident.

#77508 addresses shared ControlMaster teardown among concurrent normal SSH environments. It is relevant if the local minimal patch is later replaced by #77933's explicit probe cleanup and socket isolation; blindly adding cleanup without preserving socket ownership could reintroduce cross-session disruption.

### File-sync portability PRs are conflict surfaces, not substitutes

#100761 and #26323 edit `tools/environments/ssh.py` to make enabled sync safer or portable. They do not remove unnecessary prompt-probe sync. Future rebases may conflict mechanically, but the local invariant remains simple: prompt metadata probing must not instantiate or invoke file synchronization, while real tool environments retain normal synchronization.

## Recommendation

Keep `2f826a2b1` in the local patch stack for now. Watch #77933 as the exact upstream replacement candidate, but do not drop the local patch unless upstream lands equivalent behavior and verification demonstrates that prompt probes perform no file scan/upload/sync-back while normal SSH tool environments retain bootstrap, change detection, and sync-back.

When rebasing across #77933 or related SSH lifecycle work, compare semantics rather than choosing hunks mechanically. Prefer upstream's broader lifecycle handling only if its isolated socket and cleanup paths remain safe and its current-main tests pass. Expect very high conflict risk in all three production files if #77933 is refreshed or merged.

## Raw search queries used

```text
repo:NousResearch/hermes-agent is:open SSH file sync prompt probe
repo:NousResearch/hermes-agent is:open SSH sync_files
repo:NousResearch/hermes-agent is:open SSH repeated upload
repo:NousResearch/hermes-agent is:open SSH full upload
repo:NousResearch/hermes-agent is:open model switch hang SSH
repo:NousResearch/hermes-agent is:open startup hang SSH
repo:NousResearch/hermes-agent is:open prompt_builder SSH
repo:NousResearch/hermes-agent is:pr is:open SSH file sync
repo:NousResearch/hermes-agent is:issue is:open SSH file sync
repo:NousResearch/hermes-agent is:pr is:merged author:Zhou-Ruichen
```

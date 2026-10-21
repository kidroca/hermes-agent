# SSH sync: retain acknowledged progress across retries

- Date: 2026-10-22.
- Repo / branch: `/opt/hermes-agent`, `peter/hermes-patches`.
- Patch ref: `7afc5e3adb6d357257ca1a1a95118986e01697e9` (integrated source/test commit; prior-art credit in commit body).
- Local status: integrated locally, not activated in existing processes. Personal/local-only; no push or upstream publication requested. No profiles modified or processes restarted; Peter will authorize restart separately.
- Motivation: prevent large/slow SSH sync retries from retransmitting already acknowledged work, without allowing stale remote files to overwrite unconfirmed host changes. This does not fix the underlying slow network.
- Evidence: exact commit inspected in a disposable detached checkout; execution and authenticated upstream findings below are supplied parent/independent-review receipts, not rerun by this documentation worker.

## Local patch summary

SSH alone opts into upload batches of at most 256 files or 16 MiB; an oversized individual file travels alone. Other bulk backends retain single-call uploads unless limits are supplied. Each successful upload/delete call checkpoints confirmed progress in memory; staged snapshot hashes describe the bytes actually uploaded, not a later host read. Failure retains earlier acknowledgements and does not advance the rate-limit clock, so the remainder can retry immediately.

Same-metadata files are compared against confirmed content hashes, detecting same-size edits with unchanged timestamps. This adds hashing cost across eligible unchanged files. SSH upload deadlines become `120 + upload_bytes / (256 * 1024)` seconds (256 KiB/s budget plus overhead), rather than a fixed 120 seconds.

Sync-back rejects unconfirmed explicit mappings and existing inferred host targets, including a missing host file with an explicit mapping. Genuinely new remote files with absent inferred host targets remain importable. The final guard fixes the reviewer's stale-B overwrite case after a partial successful A push.

Dependencies: existing portable file-only tar upload and shared `FileSyncManager` contracts; preserve NUL manifests, pre-write validation, POSIX remote paths and Windows containment. This is an adaptation to the personal stack, not a transplant of an upstream proposal.

### Maintenance surface

Exact `git show --numstat` receipt (catalogue docs excluded):

| File | Added | Deleted |
|---|---:|---:|
| `tools/environments/file_sync.py` | 87 | 59 |
| `tools/environments/ssh.py` | 7 | 2 |
| **Production: 2 existing files** | **94** | **61** |
| `tests/tools/test_file_sync.py` | 2 | 2 |
| `tests/tools/test_file_sync_progress.py` (new) | 170 | 0 |
| `tests/tools/test_ssh_sync_deadline.py` (new) | 24 | 0 |
| **Tests: 3 files, 2 new** | **196** | **2** |

No new production module or persistent format. Shared planning/checkpoint/sync-back hot paths change, alongside SSH construction/deadline integration; expect semantic rebase work in those methods, not merely a constants conflict.

## Tests / verification

- Fresh integrated canonical suite: **143 passed, 0 failed, 15 skipped across 12 files**; parent and independent reviewer obtained the same result. Independent final review **APPROVED**, after the initial stale sync-back overwrite finding was fixed.
- Normal Ruff checks clean. Strict source hook failed on the existing unchanged-base `FURB122` manifest-write loop; reproduced on the base. Strict lint over all five changed files passed ignoring only that pre-existing rule. The source commit bypassed the hook after manual lint; do not describe the strict hook as passing unmodified.
- Parent live macOS SSH test: **1,527 files / 117 MB**, isolated remote prefix. Injected failure before batch three retained **512** confirmed files; retry sent only the remainder in **7** batches, for **9 successful batches** total. Subsequent unchanged sync uploaded **0** files. Remote SHA-256 readback covered **1,527 files, 0 mismatches**; total **229.1 seconds**. Remote probe deletion was verified. BSD tar upload worked.
- That live test preceded the final sync-back guard. The final guard has unit/real-tar regression evidence (**4 RED, then GREEN**), not a post-guard live macOS rerun.
- No full-repository suite or native Windows test run claimed. Documentation worker verified exact source SHA, numstat, diff and catalogue-only scope; did not repeat runtime tests.

### Limitations

Checkpoints are in-memory only: a new process still performs its first sync. There is no persistent cross-process manifest, atomic remote extraction, or file-level resume inside a failed batch; an unacknowledged batch may be replayed even if some remote writes occurred. Source integration is not runtime activation. No rolling/process-reload claim or network-throughput improvement is made.

## Upstream overlap

Authenticated findings supplied by parent, checked 2026-10-22; no additional research in this docs-only pass. Upstream main inspected at `55ee4acdd822b73fb9573a2321531ae3a9d0b3e0` still used rollback and a fixed 120-second deadline.

| Item | Verified status / signal | Conflict risk | Merge likelihood |
|---|---|---|---|
| [PR #139385](https://github.com/NousResearch/hermes-agent/pull/139385), jerbao | Open, unmerged; created Oct 15 19:24Z, updated Oct 17 07:37Z; head `d15593dce543d055398fd8fac4ea94367d72bbdf`. Actual diff inspected: bounded 500-file / 64-MiB batches and success checkpoints. No comments; no endorsement inferred. | High direct overlap with shared sync progress/batching. | Unknown; open status/silence is not approval. |
| [PR #131146](https://github.com/NousResearch/hermes-agent/pull/131146), liuhao1024 | Open; created Oct 2. Adjacent GNU-tar probing proposal. | Portable-tar compatibility risk; preserve BSD/macOS behavior. | Unknown. |
| [PR #96935](https://github.com/NousResearch/hermes-agent/pull/96935), keisha-gabo | Open; created Aug 28. Native-workspace SSH lifecycle proposal against an older contract. | Adjacent lifecycle overlap; do not transplant. | Unknown. |

## Notes on most relevant upstream items

#139385 is credited prior art in the integrated commit body. Its proposed batching/checkpoint idea was adapted to the current portable-tar implementation, with tighter SSH batch bounds, size-scaled deadlines, snapshot/content correctness and unconfirmed sync-back protection. Do not equate that open proposal with code present on upstream main. The two adjacent proposals are compatibility/watch items, not dependencies or evidence of maintainer support.

## Recommendation

Retain the integrated local patch and portable-tar guarantees. On rebase, inspect #139385 and shared sync-back semantics directly; drop the local change only after equivalent acknowledged-progress, failure-clock, content and host-protection contracts are verified upstream. Keep activation separate: no restart, profile changes, push or publication belongs to this catalogue task.

## Raw search queries used

Parent supplied four authenticated searches covering upstream SSH bulk timeout, file-sync retry and transactional progress. Exact query strings were not included in this worker's evidence; not reconstructed or rerun. Direct PR/main refs above identify the verified findings.

# Support macOS BSD tar during SSH file sync

- Date: 2026-07-16
- Repo: /opt/hermes-agent
- Patch ref: `c9895f4cf` (reviewed) → `53a7b903a` (pre-2026-08-09 active) → `b9b4f366b0` (pre-2026-08-14 active) → `77ba2d467f` (pre-refresh active) → `3edc972c42` (pre-2026-08-23 active) → `0366d7db77` (active)
- Branch: `peter/hermes-patches`
- Local status: committed at `HEAD`; pre-existing `package-lock.json` modification left untouched; catalogue docs updated without modifying source or tests
- Motivation: stock Hermes invokes GNU-only `--no-overwrite-dir` on the remote extractor; macOS bsdtar 3.5.3 rejects it and aborts support-file synchronization. The existing local manifest patch already prevents parent-directory headers, so portable extraction can preserve the directory-mode safety contract without the GNU-only flag.
- Changed files: `tools/environments/ssh.py`, `tests/tools/test_ssh_bulk_upload.py` (29 insertions, 9 deletions)
- Tests / verification: TDD RED observed for the command contract while the GNU-only flag remained; 22 focused SSH bulk-upload tests passed; 38 SSH/file-sync tests passed; Ruff and diff/security scans passed; independent review approved with no blockers. Live macOS BSD-tar profile sync uploaded sentinel v1, overwrote it with v2, and retained modes (home 750, `~/.hermes` 755, cache/documents 755), then cleaned the sentinel locally and remotely. Broad tools suite reached 580 passed before an unrelated Camofox test failed because localhost:19999 returned HTTP 404 rather than connection refused.

## Local patch summary

This patch removes `--no-overwrite-dir` from the remote SSH tar extraction command and strengthens regression coverage by opening a generated archive and proving it contains only the expected regular-file entries. It relies on the safety premise established by Peter's earlier SSH tar metadata patch family (`474150a67`, rebased as `23224f34a`): bulk archives use an explicit file manifest, exclude the staging root and remote-home parent entries, dereference staged symlinks, and suppress macOS copyfile/xattr metadata.

Treat `c9895f4cf` as a portability follow-up to that existing patch, not a replacement for its history. The prior patch removes parent metadata from the archive; this follow-up then removes the GNU-only extraction guard that is no longer needed.

## Upstream overlap

| Kind | # | Title | Created / updated | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| open PR | [26323](https://github.com/NousResearch/hermes-agent/pull/26323) | fix(ssh): support macOS tar during file sync | 2026-05-15 / 2026-07-15 | `verybigdog`, association `NONE`; no prior merged PRs found by authenticated author search | Collaborator linked the competing #13955 design; automated contributor review said keep open/high salvageability but identified tests needing updates. No maintainer approval found. | 2 files, +177/-6; same `ssh.py` path plus SSH tests | **very high**: exact bug and command path; current PR adds probing and a BSD fallback rather than always-portable extraction | medium/unknown: exact active work and recently refreshed, but blocked and without maintainer approval |
| closed issue | [17767](https://github.com/NousResearch/hermes-agent/issues/17767) | SSH backend: `tar xf - -C /` corrupts remote home directory mode, breaks sshd StrictModes | 2026-04-30 / 2026-04-30 | `luismartinezs`, association `NONE` | Collaborator marked it likely duplicate of #10205 | issue only | semantic safety overlap; no direct merge conflict | already closed; defines the safety contract this patch preserves |
| closed PR | [13955](https://github.com/NousResearch/hermes-agent/pull/13955) | fix(ssh): avoid remote tar metadata failures during file sync | 2026-04-22 / 2026-06-04 | `zwcf5200`, association `CONTRIBUTOR` | Collaborator explicitly linked #10205; no reviews or approval found | 2 files, +65/-4; exact same source/test files | **very high historical overlap**: manifest, explicit entries, and macOS metadata suppression closely match the `474150a67`/`23224f34a` prerequisite | none as submitted: closed unmerged |
| closed PR | [10205](https://github.com/NousResearch/hermes-agent/pull/10205) | harden(ssh): scope bulk sync tar extraction to .hermes | 2026-04-15 / 2026-05-25 | `Stark-X`, association `CONTRIBUTOR` | Cited by collaborator as the duplicate/root-cause fix for #17767 | 2 files, +47/-8 | high historical overlap in extraction scope and parent-mode safety | none as submitted: closed unmerged |

## Notes on most relevant upstream items

### Proven overlap

PR #26323 is an exact current upstream analogue. It targets the same macOS/bsdtar rejection of `--no-overwrite-dir`, modifies the same SSH bulk-upload path, and now also archives explicit staged file entries rather than `.`. Its implementation is broader than the local follow-up: it probes remote tar support, keeps the GNU flag when available, and falls back to `tar xmf` for BSD tar. The local patch instead relies on its already-proven file-only archive invariant and uses one portable extraction command everywhere. Any merge or rebase involving #26323 is therefore expected to conflict mechanically and requires a semantic comparison rather than stacking both implementations.

PR #13955 is the strongest historical match for the prerequisite patch family: explicit manifest entries plus macOS metadata suppression. It was closed without merge. PR #10205 and issue #17767 establish the parent-directory metadata/StrictModes hazard that makes simply deleting `--no-overwrite-dir` unsafe unless archive contents are constrained. The local family preserves that contract and adds live macOS evidence.

### No additional direct overlap confirmed

Authenticated narrow searches found other open SSH/tar PRs (#63979, #47492, #53262, #62065, #41362), but their subjects are subprocess cleanup/timeouts, sync-back size or archive-expansion bounds, and Python tarfile compatibility. They share subsystem files or terminology but do not address remote BSD-tar extraction flags or the file-only archive safety premise, so they are not listed as direct overlap.

## Recommendation

Keep `c9895f4cf` as a clearly documented follow-up to `474150a67`/`23224f34a`, and watch PR #26323 closely. Upstream overlap and conflict risk are very high, but replacement is not yet justified: #26323 remains open/blocked, has no maintainer approval found, adds capability-probe complexity, and lacks the reported live macOS mode/overwrite verification. If #26323 or a successor merges, compare these contracts before dropping the local pair: explicit regular-file-only archive members, no parent-directory metadata, overwrite semantics, unchanged remote directory modes, and portable macOS extraction.

## Raw search queries used

All searches were run with authenticated `gh` CLI against `NousResearch/hermes-agent` on 2026-07-16.

- `repo:NousResearch/hermes-agent is:open "no-overwrite-dir"`
- `repo:NousResearch/hermes-agent is:open "BSD tar"`
- `repo:NousResearch/hermes-agent is:open macOS tar SSH`
- `repo:NousResearch/hermes-agent is:open SSH "bulk upload" tar`
- `repo:NousResearch/hermes-agent is:open "file sync" permissions tar`
- `repo:NousResearch/hermes-agent is:pr is:open SSH tar sync`
- `repo:NousResearch/hermes-agent is:pr is:merged author:verybigdog`
- Direct authenticated views: issues/PRs `#17767`, `#26323`, `#13955`, and `#10205`, including PR files, reviews, issue comments, and review comments where applicable

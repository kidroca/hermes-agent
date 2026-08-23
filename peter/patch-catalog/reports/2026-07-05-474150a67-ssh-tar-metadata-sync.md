# Avoid SSH tar metadata failures during file sync

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `474150a67` (reviewed) → `ed44e31a3` (pre-2026-08-09 active) → `a547eaa832` (pre-2026-08-14 active) → `3ae8460bb3` (pre-refresh active) → `ed77ecde2a` (pre-2026-08-23 active) → `9f42ba4db3` (pre-final-refresh active) → `481b3f9502` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: tests/tools/test_ssh_bulk_upload.py, tools/environments/ssh.py
- Tests / verification: commit contains focused tests: SSH bulk upload tar metadata regression tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Adjusts SSH file sync so tar extraction does not fail on metadata/ownership/permission operations that remote accounts cannot perform, with bulk-upload tests covering the safer tar invocation/path.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| none found | — | No directly overlapping open upstream issue/PR was confirmed by authenticated refresh | — | — | — | — | low | unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Narrow searches for SSH/tar/bulk-upload overlap still did not confirm a directly matching open upstream issue/PR.

No strong upstream analogue was confirmed. Broad GitHub search later hit the authenticated search-rate limit, so keep the honest caveat that absence of search results is not proof no upstream overlap exists.

## Recommendation

Keep local patch; upstream overlap was not found. Conflict risk is limited to SSH environment sync code; retain until upstream lands equivalent robust tar flags.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open ssh tar metadata bulk upload`
- `repo:NousResearch/hermes-agent is:open ssh bulk upload tar`
- `repo:NousResearch/hermes-agent is:open tools/environments/ssh.py tar`

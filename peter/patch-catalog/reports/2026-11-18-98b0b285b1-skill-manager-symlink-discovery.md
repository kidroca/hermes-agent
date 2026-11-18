# Skill-manager discovery through symlinked categories

- Date: 2026-11-18.
- Source / standalone cherry-pick ref: `98b0b285b1d10df6b1dc07ccf681963b1f7d1b0b`.
- Parent / latest fork base: `99a14664e4616abc88e66c01aa99477bb66f5a2d`.
- Candidate branch: `fix/skill-manager-symlink-discovery`. Catalogue drafted in a disposable detached checkout at the exact source ref, then verified and transferred by the parent.
- Local status: reviewed candidate only; NOT integrated, deployed or pushed. Live Mac source remains `5e367d534b` (parent-supplied receipt, not checked here).
- Scope: personal candidate; no upstream PR requested. Catalogue documentation is committed separately from the source commit.
- Motivation: `skill_view` can find skills behind external category symlinks while manager discovery misses them, preventing in-place management.
- Production: `tools/skill_manager_tool.py`, +15/-3, one existing file/helper; no new production module.
- Tests: new `tests/tools/test_skill_manager_symlink_discovery.py`, +140/-0.

## Local patch summary

`_iter_skill_dirs` replaces `Path.rglob` with `os.walk(..., followlinks=True)`.
It prunes excluded paths before consuming resolved-path identities, deduplicates real directories and bounds branching symlink cycles.
This ordering prevents an excluded `.archive` alias visited first from hiding an allowed alias to the same target.
Existing local-over-external precedence and the out-of-root delete guard remain unchanged; patching linked external skills does not create a local copy.
The shared `iter_skill_index_files` was considered but not reused because it lacks cycle deduplication; this change is deliberately scoped to manager discovery.

## Tests / verification

Receipts below are supplied by the parent/implementation agents; this catalogue pass inspected the exact parent-to-source diff and ran no tests.

- Implementation RED: five regression cases failed before the fix.
- Parent rerun on the candidate: focused five passed.
- Parent rerun on committed source: 915 passed / 0 failed / 1 skipped across 44 files. Implementation `scripts/check`: 19 OK; source `git diff --check` clean.
- Coverage: directory/frontmatter-name patch lookup, actual in-place target edits, archive-first exclusion ordering, local precedence, excluded support/archive paths, delete refusal and branching-cycle deadline.
- Symlink regressions are POSIX-marked and executed on macOS; Windows behavior and the full suite were not verified.
- Independent precommit review: APPROVE, no blockers; artifact-only read, not an independent test execution.
- Commit hooks ultimately passed without bypass. An isolated `just` 1.58 was needed because host 1.51 cannot parse `default-list`; testing used a separate disposable environment, not source/environment changes in this catalogue checkout.

## Upstream overlap

Evidence is from an earlier delegated, bounded unauthenticated public REST read supplied by the parent, not fresh network research here.
Four searches inspected the first 20 results each, with direct metadata, diffs and discussion follow-up; not exhaustive. Current upstream-main ancestry was NOT checked.

| Item | State / dates | Author / review signal | Relevant surface | Conflict / merge outlook |
|---|---|---|---|---|
| [Issue #155776](https://github.com/NousResearch/hermes-agent/issues/155776), exact symlink-discovery report | Open; created/updated Nov 14 | robertroosalu, NONE; no comments | Exact reported symptom | Exact relevance; not evidence of a merged fix |
| [PR #156015](https://github.com/NousResearch/hermes-agent/pull/156015), exact manager fix | Open, unmerged, non-draft; created Nov 15, updated Nov 16 | adindamochamad, NONE; no formal reviews | Manager +17/-3; `tests/tools/test_skill_manager_tool.py` +158 | High direct conflict; merge likelihood unknown |
| [PR #143312](https://github.com/NousResearch/hermes-agent/pull/143312), shared cycle-safe scanner | Open, unmerged; created Oct 23 | teknium1, COLLABORATOR; no formal review; automated discussion | `agent/skill_utils.py`, `agent/prompt_builder.py`, `tests/agent/test_prompt_builder.py`; +61/-12 | Medium semantic scanner overlap; merge likelihood unknown |

## Notes on most relevant upstream items

PR #156015 had `mergeable: true` with `unstable` merge state; neither is maintainer approval.
Contributor kvnloo [identified the archive-alias-first dedup problem](https://github.com/NousResearch/hermes-agent/pull/156015#issuecomment-6908391809); the author [acknowledged a revision](https://github.com/NousResearch/hermes-agent/pull/156015#issuecomment-6910220875).
These are contributor discussion, not formal review or proof of adoption into main. Prior merged-author history was not established by the supplied research.

## Recommendation

Keep the reviewed source as an unintegrated candidate until Peter separately authorizes integration; preserve the standalone source SHA for later cherry-pick.
Do not alter the retained-stack history or infer deployment from this report. No source integration, restart, fork push or upstream submission is authorized by catalogue work.
On a future rebase, compare #156015 and shared scanner #143312 against the then-current main; replace the local helper only after equivalent exclusion-before-dedup, bounded-cycle, precedence and delete-guard behavior is verified.

## Raw search queries used

- `repo:NousResearch/hermes-agent symlink skill`
- `repo:NousResearch/hermes-agent "_iter_skill_dirs"`
- `repo:NousResearch/hermes-agent "external_dirs" "skill_manage"`
- `repo:NousResearch/hermes-agent "iter_skill_index_files"`

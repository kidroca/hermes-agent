# Label and bootstrap Hindsight recall context

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `ef4fd42dc`, `8729cde09`, `04fa2c25a` (reviewed) → `ddd0f5e6f` + `9226a750d` + `42fca3fbf` (pre-2026-08-09 active) → `a0006f51a2` + `983849d42c` + `01d82afd79` (pre-2026-08-14 active) → `b7243c4db6` + `9fb637e06b` + `75377f5cfd` (pre-refresh active) → `00ee62c47c` + `3aa9c029b2` + `de31697c00` (pre-2026-08-23 active) → `b6aef53af8` + `ec86ca14e2` + `38e7ba34f3` (pre-final-refresh active) → `8cdb7c5093` + `575c368cd2` + `02213d9f90` (pre-2026-08-27 active) → `62995257ff` + `4b2130bb99` + `4c50954f21` (pre-final-refresh active) → `e92cc75b71` + `6af863cff6` + `38b907ba6e` (pre-final-refresh-2 active) → `ce0b86e1ac` + `0aa9495f63` + `e1b51e5c1d` (pre-2026-08-31 active) → `add40eaaae` + `fc49f0989b` + `e6c4ab410a` (pre-2026-09-05 active) → `d6fa59f518` + `ef633c6406` + `459cdb72c4` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: agent/memory_manager.py, plugins/memory/hindsight/__init__.py, tests/plugins/memory/test_hindsight_provider.py, tests/plugins/memory/test_hindsight_recall_format.py
- Tests / verification: commit contains focused tests: Hindsight provider and recall-format tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Improves Hindsight recall formatting by labelling recalled context with source profile when tagged, avoiding labels for untagged recall, and bootstrapping recall even when prefetch is empty.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | #3943 | [Feature] Introduce `MemoryProvider` interface for long-term memory integrations | created 2026-03-30; updated 2026-05-03 | `danhdoan` | 1 comment | n/a | Medium: memory-provider architecture adjacent to Hindsight provider behavior | Unknown |
| Docs | main branch | `plugins/memory/hindsight` README/source files | current main | upstream code/docs | not applicable | same plugin files | Medium: direct file overlap if upstream edits Hindsight formatting | n/a |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Keep these small provider-local fixes; re-check plugins/memory/hindsight/__init__.py on rebase because conflicts are likely if upstream changes Hindsight recall formatting.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open Hindsight recall profile source empty prefetch`
- `repo:NousResearch/hermes-agent is:open Hindsight recall format profile`
- `repo:NousResearch/hermes-agent is:open MemoryProvider interface long-term memory`

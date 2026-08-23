# Restore Kanban profile invocation guard

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `16b715b68` (reviewed) → `16838a406` (pre-2026-08-09 active) → `1c8431de0a` (pre-2026-08-14 active) → `8f6f1307cc` (pre-refresh active) → `28e7566d64` (pre-2026-08-23 active) → `fcd0d68195` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: hermes_cli/kanban_db.py, hermes_cli/profiles.py, tests/hermes_cli/test_kanban_db.py, tests/hermes_cli/test_profiles.py
- Tests / verification: commit contains focused tests: Kanban DB/profile guard tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Restores safeguards that prevent inappropriate Kanban CLI/profile invocation paths, preserving the separation between human CLI/dashboard use and worker tool access.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | #16102 | RFC: review the Kanban — multi-profile collaboration board | created 2026-04-26; updated 2026-04-30 | `teknium1` | 13 comments; RFC/architecture discussion | n/a | Medium: mentions agent guard and Kanban invocation contracts | Unknown |
| Issue | #26675 | Managed Agent Runtime contracts on top of agent_control / Kanban / SessionDB | created 2026-05-16; updated 2026-06-28 | `zycaskevin` | 3 comments | n/a | Medium: profiles/Kanban runtime contracts adjacent | Unknown |
| Docs | kanban docs | Workers drive board through dedicated kanban_* tools instead of shelling to hermes kanban | main docs | upstream docs | supports local guard intent | low | n/a | unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Keep guard; watch upstream Kanban/runtime-profile work. Conflict likely in hermes_cli/kanban_db.py and profiles.py if upstream formalizes the same contract.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open kanban profile invocation guard`
- `repo:NousResearch/hermes-agent is:open Kanban agent guard gateway`
- `repo:NousResearch/hermes-agent is:open Managed Agent Runtime contracts Kanban profiles`

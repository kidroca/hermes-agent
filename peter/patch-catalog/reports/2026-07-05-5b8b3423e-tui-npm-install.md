# Avoid unnecessary TUI npm install on launch

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `5b8b3423e` (reviewed) → `61945e806` (pre-2026-08-09 active) → `c12201be16` (pre-2026-08-14 active) → `ed69cf5942` (pre-refresh active) → `39640471bb` (pre-2026-08-23 active) → `6e19adaeef` (pre-final-refresh active) → `ecb85ddccd` (pre-2026-08-27 active) → `0eefbc09fd` (pre-final-refresh active) → `13e8a3231b` (pre-final-refresh-2 active) → `78a6899c5a` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: hermes_cli/main.py, tests/hermes_cli/test_tui_npm_install.py
- Tests / verification: commit contains focused tests: TUI npm install launch tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Skips redundant npm install work when launching the TUI if dependencies/bundle state are already acceptable, reducing startup latency and avoiding avoidable network/package-manager work.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #51417 | Fix/tui spurious npm install | created 2026-06-23; updated 2026-06-30 | `dok2014` | 2 comments; `tonydwb` review `APPROVED` | 1 file, +17/-79 | High: direct `hermes_cli/main.py` startup/install overlap | Medium-high: direct, small, and approved, though mergeability is `UNKNOWN` |
| PR | #52245 | fix(tui): prevent spurious npm install on every launch | created/updated 2026-06-25 | `qazasdsdqaza` | 1 comment, no reviews | 1 file, +47/-7 | High: direct symptom overlap | Unknown |
| PR | #57469 | fix(tui): skip full lockfile check in monorepo to avoid spurious npm installs | created/updated 2026-07-03 | `bonut88` | no comments/reviews | 1 file, +7/-0 | High: direct install-check overlap | Medium-low/unknown: tiny and fresh, but no maintainer signal |
| PR | #54613 | fix(tui): skip redundant TUI dep reinstall on every launch | created/updated 2026-06-29 | `digital-grease` | no comments/reviews | 2 files, +136/-0 | High: direct startup/install overlap plus tests | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Very high overlap; expect upstream to change `hermes_cli/main.py` in the same area. #51417 now has the strongest merge signal because authenticated PR metadata shows an approving review. Keep local behavior, but be ready to drop or reconcile once one upstream npm-install PR lands.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open TUI npm install launch`
- `repo:NousResearch/hermes-agent is:open spurious npm install every launch`
- `repo:NousResearch/hermes-agent is:open skip redundant TUI dep reinstall`

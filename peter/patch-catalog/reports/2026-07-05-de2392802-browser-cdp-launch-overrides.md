# Browser/CDP launch overrides and approval UI preservation

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `de2392802`, `a45790619`, `6a726be99` (reviewed) → `e4eed0b1a` + `41be3faa9` + `ed0c4edc8` (pre-2026-08-09 active) → `0c77b22982` + `42e16962a0` + `6fbd0ccd7a` (pre-2026-08-14 active) → `b7edc3f88e` + `61dc02f515` + `99d093ca4a` (pre-refresh active) → `e1f9e33e00` + `95c3446380` + `9f75ed9a26` (pre-2026-08-23 active) → `fdff3c5f95` + `4db2906daf` + `f292be73ea` (pre-final-refresh active) → `edb594933a` + `f4d5a6167c` + `f9981154c7` (active)
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: apps/desktop/electron/main.cjs, cli.py, hermes_cli/callbacks.py, hermes_cli/config.py, tests/cli/test_cli_approval_ui.py, tests/tools/test_browser_cdp_override.py, tests/tools/test_browser_cdp_lazy_launch.py, tests/tools/test_browser_cdp_tool.py, tools/approval.py, tools/browser_cdp_tool.py, tools/browser_tool.py
- Tests / verification: commit contains focused tests: CLI approval UI, browser CDP override/tool, and lazy-launch coverage tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Preserves local browser launch controls around CDP auto-launch/launch-command behavior, approval callback handling, and desktop/CLI entrypoints. Later commits isolate lazy-launch tests and add explicit auto_launch/launch_command coverage without changing production code in the final test-only commit.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #40276 | perf: reduce tool-loading cold-start overhead | created 2026-06-06; updated 2026-06-07 | `Xue-1997`; author association not exposed by `gh pr view` | 2 comments; one `COMMENTED` review by `alpindiay`; no approval seen | 40 files, +1076/-169; broad tool-loading changes match browser tool paths | Medium: broad tool-loading refactors can touch browser tool imports/lazy loading | Unknown: large and no visible approval |
| PR | #22280 | [security] fix(gateway): harden callbacks, CDP, and health diagnostics | created 2026-05-09; updated 2026-05-23 | `Hinotoi-agent` | no comments/reviews via PR API | 6 files, +213/-20; callback/CDP hardening | Medium-high: CDP/callback surfaces overlap local launch overrides and approval UI preservation | Low/unknown: API reports `CONFLICTING`, stale, no maintainer signal |
| Issue | #12130 | TUI v2 feature-parity audit vs v1 CLI | created 2026-04-18; updated 2026-06-18 | `teknium1` | 4 comments; audit/feature-parity discussion, not a direct CDP fix | n/a | Low-medium: approval UI preservation is adjacent to feature parity | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Keep local patch and watch any upstream CDP/callback hardening work before rebasing; conflict risk is concentrated in browser_tool.py/browser_cdp_tool.py and callback surfaces. Re-run browser CDP tests after upstream changes.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open browser CDP auto_launch launch_command`
- `repo:NousResearch/hermes-agent is:open browser_cdp_tool browser_tool CDP`
- `repo:NousResearch/hermes-agent is:open approval prompt browser CDP`

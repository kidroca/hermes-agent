# Ring TUI bell on approval prompts

- Date: 2026-07-05
- Repo: /opt/hermes-agent
- Patch ref: `199641e5f`
- Branch: peter/hermes-patches
- Local status: clean at dispatch; catalogue docs generated without modifying Hermes source code
- Motivation: keep Peter's local Hermes fork behavior stable while upstream evolves.
- Changed files: ui-tui/src/__tests__/createGatewayEventHandler.test.ts, ui-tui/src/__tests__/useConfigSync.test.ts, ui-tui/src/app/createGatewayEventHandler.ts, ui-tui/src/app/interfaces.ts, ui-tui/src/app/useConfigSync.ts, ui-tui/src/app/useMainApp.ts, ui-tui/src/gatewayTypes.ts
- Tests / verification: commit contains focused tests: TUI gateway event/config sync tests; this catalogue run inspected `git show --stat` for included commits and updated docs only.

## Local patch summary

Adds a TUI-side audible/terminal bell path for approval prompts so the user notices when interaction is required, wiring the gateway event through config sync and main app interfaces.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | #58957 | feat(cli): unified input-needed alert (BEL + OSC 9) for all interactive prompts | created/updated 2026-07-05 | `glitchbunny0` | no comments/reviews via PR API | 5 files, +198/-1; mergeable=`MERGEABLE` | High: same input-needed/approval alert channel, broader scope | Medium: fresh, mergeable, focused, but no maintainer signal yet |
| PR | #25042 | feat: paplay audio bell + notify_on_interact for Wayland terminals | created/updated 2026-05-13 | `xxxigm` | no comments/reviews via PR API | 16 files, +582/-24 | Medium: broader attention/notification system | Low/unknown: older, larger, no maintainer signal |
| Issue | #46357 | RFC: configurable TUI attention hook for completed / waiting / blocked turns | created/updated 2026-06-15 | `tsagi2045` | 0 comments | n/a | Medium: policy/design overlap for attention hooks | Unknown |

## Notes on most relevant upstream items

Refresh coverage: authenticated `gh` CLI was available on 2026-07-05. Existing candidate issues/PRs were re-checked with `gh pr view` / `gh issue view` for created/updated dates, authors, comment/review counts, changed-file counts, additions/deletions, and mergeability where the PR API exposed it. No source code was modified.

Maintainer signal below means visible PR reviews/comments from the GitHub API; absence of a maintainer review/comment is recorded as unknown rather than negative evidence. GitHub search itself later returned a search-rate-limit response during a broad sweep, so the refresh emphasizes authenticated metadata for the already identified narrow candidates plus any successful targeted searches.

## Recommendation

Watch #58957 closely; if it merges, replace this narrow approval-bell patch with the unified upstream alert mechanism.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open TUI approval bell`
- `repo:NousResearch/hermes-agent is:open input-needed alert BEL OSC 9`
- `repo:NousResearch/hermes-agent is:open configurable TUI attention hook`

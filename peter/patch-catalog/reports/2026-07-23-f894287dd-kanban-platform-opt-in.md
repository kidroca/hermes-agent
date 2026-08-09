# Honor per-platform Kanban tool opt-in

- Date: 2026-07-23
- Repo: `/opt/hermes-agent`
- Patch ref: `f894287dd` (reviewed) → `93959cbbb` (pre-2026-08-09 active) → `47f6724134` (active)
- Branch: `peter/hermes-patches`
- Local status: source patch committed as `f894287dd`; catalogue update left uncommitted at dispatch
- Motivation: make an explicit `platform_toolsets.<platform>: [kanban, ...]` selection sufficient to expose native Kanban tools on that platform while keeping Kanban hidden from the normal picker, non-configurable there, default-off, and isolated from unselected platforms.
- Changed files: `hermes_cli/tools_config.py`, `tools/kanban_tools.py`, `tests/hermes_cli/test_tools_config.py`, `tests/test_tui_gateway_server.py`, `tests/tools/test_kanban_tools.py`
- Tests / verification: inspected the complete commit diff; ran `uv run pytest -q tests/hermes_cli/test_tools_config.py -k 'kanban' tests/test_tui_gateway_server.py -k 'enabled_toolsets' tests/tools/test_kanban_tools.py -k 'platform or visible_with_toolset_config'` — **61 passed, 581 deselected**.

## Local patch summary

The patch adds `kanban` to `_DEFAULT_OFF_TOOLSETS` without adding it to `CONFIGURABLE_TOOLSETS`. This preserves the hidden/non-interactive and default-off contract, but an explicit per-platform list can retain the non-configurable `kanban` entry through `_get_platform_tools()` and expose its native schemas only on the selected surface.

The runtime profile gate now accepts either the legacy top-level `toolsets: [kanban]` form or any list-valued `platform_toolsets` entry containing `kanban`; a null legacy key is handled safely. The existing `HERMES_KANBAN_TASK` dispatcher override is unchanged. Regression coverage exercises CLI/TUI exposure, null legacy config, cross-platform isolation, and schema/check-function cache isolation.

## Upstream overlap

| Kind | # | Title | Age / status at review | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| PR | [#64510](https://github.com/NousResearch/hermes-agent/pull/64510) | fix(tools): support explicit kanban profile opt-in | Open; created 2026-07-14, updated 2026-07-19 | `cypres0099`, `CONTRIBUTOR`; authenticated merged-PR search found no prior merged PRs | `teknium1` sweeper review: premise confirmed, `keep_open`, salvageability high; requested a multi-platform disable fix | 6 files, +165/-9; overlaps `hermes_cli/tools_config.py` directly | **Very high** mechanical and semantic overlap | **Medium**: problem and direction validated, but requested correction remains and no approval/merge signal is visible |
| Issue | [#64494](https://github.com/NousResearch/hermes-agent/issues/64494) | Kanban runtime gate cannot be enabled through hermes tools | Open; created/updated 2026-07-14 | `cypres0099`, `CONTRIBUTOR` | No comments; directly linked/fixed by #64510 | n/a | **Very high** semantic overlap | **Medium**, through #64510 rather than independently |
| PR | [#68047](https://github.com/NousResearch/hermes-agent/pull/68047) | fix(tools): let an explicit toolset list win over x_search auto-enable | Open; created/updated 2026-07-20 | `0xDevNinja`, `CONTRIBUTOR` | One non-maintainer review comment; no approval | 2 files, +68/-1; overlaps both `hermes_cli/tools_config.py` and its tests | Medium mechanical, low semantic | Low-to-medium |
| PR | [#35605](https://github.com/NousResearch/hermes-agent/pull/35605) | fix(tools): refresh cache when session env changes | Open; created 2026-05-31, updated 2026-07-19 | `kiranmagic7`, association `NONE` | Sweeper says premise holds but branch needs manual salvage against newer cache architecture | 2 files, +62/-3; touches `model_tools.py`, not local production files | Low mechanical; medium adjacency to `HERMES_KANBAN_TASK` and cache isolation | Low as-is |
| Merged PR | [#38918](https://github.com/NousResearch/hermes-agent/pull/38918) | fix(tools): stop hermes tools reporting kanban as removed | Merged 2026-06-04 | `teknium1`, `CONTRIBUTOR` | Merged upstream behavior establishes that Kanban is deliberately absent from the checklist and that non-configurable entries are preserved | 2 files, +101/-6; `hermes_cli/tools_config.py` plus tests | Medium contextual overlap | Landed; architectural precedent |

## Notes on most relevant upstream items

### #64510 / #64494 — exact competing contract

Authenticated GitHub search found an exact open issue/PR pair. Both identify the same split-brain behavior: platform configuration can say Kanban is enabled while `tools.kanban_tools._profile_has_kanban_toolset()` only accepts the legacy top-level gate, leaving native schemas absent.

The implementations differ materially:

- Upstream #64510 makes `hermes tools enable kanban` a supported non-interactive command and synchronizes a global top-level `toolsets` gate with per-platform selections. Kanban remains out of the interactive picker and `all`.
- Local `f894287dd` keeps Kanban non-configurable through the canonical picker/command universe and instead teaches the runtime gate to honor explicit per-platform configuration directly.
- #64510's sweeper review confirmed the premise and rated salvageability high, but found that disabling one platform wrongly removes the profile-global gate while another platform still selects Kanban. The local approach avoids that particular global-gate synchronization failure because the runtime checks all selected platform lists and `_get_platform_tools()` still scopes actual exposure to the active platform.

Because both patches modify `hermes_cli/tools_config.py` and define the same user-visible enablement contract in competing ways, conflict risk is very high. If #64510 lands, the local patch should not be dropped mechanically: first decide whether upstream's canonical enable/disable UX is preferred, then verify null legacy config, multi-platform disable behavior, TUI loading, and cross-platform/cache isolation.

### #38918 — merged precedent

Merged #38918 documents the intended hidden/non-configurable behavior: Kanban is not offered as a checklist item, while explicitly preserved non-configurable platform entries survive saves. This supports the local patch's narrow passthrough model, but does not itself fix the runtime gate.

### Adjacent resolver/cache work

#68047 shares the `_get_platform_tools()` explicit-list authority path and is likely to cause a small textual conflict in `hermes_cli/tools_config.py`, but concerns x_search rather than Kanban. #35605 is relevant only to cache/context isolation around environment-sensitive checks; it does not implement per-platform Kanban selection and currently requires architectural rework.

## Recommendation

**Keep `f894287dd` locally for now, with very high upstream-conflict watch on #64510/#64494.** The local contract is narrower and already covers per-platform and cache isolation. Do not replace it merely because #64510 merges: compare the final upstream behavior first. Prefer upstream if it preserves Kanban's explicit/default-off nature and passes equivalent null-legacy, multi-platform disable, TUI, platform-isolation, and cache-isolation tests. Otherwise retain or rebase the local behavior around upstream's command UX.

Merge likelihood for #64510 is **medium**, not high: authenticated evidence confirms an accepted problem and a high-salvageability `keep_open` review, but the review requested a substantive correctness fix and there is no visible approval or maintainer merge commitment.

## Raw search queries used

Authenticated REST searches via `gh api -X GET search/issues`:

- `repo:NousResearch/hermes-agent is:open kanban platform_toolsets`
- `repo:NousResearch/hermes-agent is:open kanban toolsets cli`
- `repo:NousResearch/hermes-agent is:open "HERMES_KANBAN_TASK"`
- `repo:NousResearch/hermes-agent is:open "default-off" toolset`
- `repo:NousResearch/hermes-agent is:open "non-configurable" toolset`
- `repo:NousResearch/hermes-agent is:open "platform toolsets" kanban`
- `repo:NousResearch/hermes-agent is:open tools_config kanban`
- `repo:NousResearch/hermes-agent is:pr is:merged kanban "profile opt-in"`
- `repo:NousResearch/hermes-agent is:pr is:merged kanban platform_toolsets`
- `repo:NousResearch/hermes-agent is:pr is:closed kanban platform_toolsets`
- `repo:NousResearch/hermes-agent is:pr is:merged author:cypres0099`

Direct authenticated API views were also retrieved for #64510, #64494, #68047, #35605, #38918, and #56660, including PR files, reviews, issue comments, author association, and size metadata where applicable.

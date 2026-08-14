# Route Hindsight banks by Git project identity

- Date: 2026-08-04
- Repo: `NousResearch/hermes-agent`
- Patch ref: `7ab0293e4` (`7ab0293e4498fce7218e4e0935a80e4fd3b47a6e`); integrated as `dd42bea32f` (pre-2026-08-09 active) → `d6271418fd` (pre-2026-08-14 active) → `d352c1028b` (pre-refresh active) → `cfcff7efb8` (active)
- Branch: `peter/hermes-patches` (authored on `peter/hindsight-git-project`)
- Local status: retained as `d6271418fd` in the 2026-08-09 rebased candidate; catalogue lineage reconciled.
- Motivation:
  - Replace the custom Hindsight project-routing plugin with stock Hermes automatic lifecycle retention.
  - Route `project::{gitProject}` from the local Git common-repository identity, with workspace-basename fallback for host-invisible remote paths and an explicit `git_project` override.
  - Preserve a safe static fallback (`project::unresolved` in the deployed profile configuration) when project identity is unavailable.
  - Keep automatic recall disabled; the official Hindsight MCP remains responsible for deliberate multi-bank recall, reflect, retain, and bank listing.
- Changed files: `agent/agent_init.py`; `agent/runtime_cwd.py`; `plugins/memory/hindsight/README.md`; `plugins/memory/hindsight/__init__.py`; `plugins/memory/hindsight/config_schema.py`; `tests/agent/test_runtime_cwd.py`; `tests/plugins/memory/test_hindsight_config_schema.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: **101 focused tests passed** across the Hindsight provider, config schema, and runtime-cwd suites. Ruff and `git diff --check` passed. Independent review found no blockers; executable-bit noise was found and corrected, leaving all touched files mode `100644`. A real-profile dry run resolved `default`/`clerk` to `project::shkaf`, `coding`/`designer` to `project::kidroca`, `lad`/`lawyer` to `project::lad-hermes`, and `incept` to `project::incept-agent`, all in context mode with `auto_recall=false`, `auto_retain=true`, and zero stock provider tools.

## Local patch summary

The patch replaces the hardcoded `agent_workspace="hermes"` initialization value with `resolve_agent_workspace()`. The resolver preserves session and `TERMINAL_CWD` overrides, explicit configured paths (including remote paths that do not exist on the Hermes host), and finally the process cwd.

Hindsight gains the `{gitProject}` bank-template placeholder and optional `git_project` override. For a visible local directory, `_resolve_git_project()` asks Git for `--git-common-dir`, so nested paths and linked worktrees collapse to the canonical common repository name. When the path is remote or otherwise not a visible Git checkout, its final POSIX or Windows path segment is used. Values are sanitized through the existing bank-segment rules. If a template explicitly requires `{gitProject}` but no identity can be resolved, provider initialization uses the configured static `bank_id` rather than producing a misleading partial bank name.

The patch also corrects Hindsight's system-prompt description when `auto_recall=false`; it no longer claims that memories are automatically injected. It does not enable provider-local recall tools or automatic recall, and it does not implement multi-bank orchestration.

## Upstream overlap

Authenticated GitHub CLI/API inspection was performed on 2026-08-04.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#62687](https://github.com/NousResearch/hermes-agent/pull/62687) | fix(memory/hindsight): per-project banks, extra recall banks, and recall the current turn | 24 days | `gcunharodrigues`, `NONE`; no prior merged PRs found | `teknium1` COMMENTED via sweeper; keep-open, salvageability medium; author responded to review | 4 files, +407/-56 | **Very high** in Hindsight README/provider/tests; also overlaps `agent_workspace` semantics | **Unknown/medium-low**: open and non-draft, but currently `mergeable=false`, `mergeable_state=dirty`, and broader than this patch |
| PR | [#37563](https://github.com/NousResearch/hermes-agent/pull/37563) | feat(memory): per-project Hindsight bank (.hindsight/config.toml walk-up + --hindsight-bank) | 63 days | `iRonin`, `CONTRIBUTOR`; no prior merged PRs found | `teknium1` COMMENTED via sweeper; keep-open, salvageability medium | 5 files, +210/-2 | **High** in Hindsight initialization/tests, but its TOML walk-up and CLI override are a different routing mechanism | **Low/unknown**: still draft and currently dirty |
| PR | [#77554](https://github.com/NousResearch/hermes-agent/pull/77554) | fix(memory): fill agent_workspace from HERMES_KANBAN_BOARD for kanban workers | 1 day | `Bazyl2101`, `NONE`; no prior merged PRs found | No reviews or comments | 2 files, +158/-1 | **High mechanically** in `agent/agent_init.py`; only partial semantic overlap because it maps Kanban board identity, not Git identity | **Unknown**: open, non-draft and mergeable, but merge state is blocked and there is no maintainer signal |
| PR | [#52987](https://github.com/NousResearch/hermes-agent/pull/52987) | feat(memory): add Hindsight multi-bank auto routing | 39 days | `morozsm`, `NONE` | `teknium1` COMMENTED via sweeper; keep-open, salvageability high, with security/correctness findings | 6 files, +1801/-93 | **Very high mechanically** in `agent_init.py`, Hindsight provider/README/tests; broader multi-bank policy model | **Unknown/medium**: strong salvageability signal but very large scope and unresolved review work; API mergeability was unknown at inspection time |

## Notes on most relevant upstream items

### #62687 — closest semantic overlap

This is the nearest implementation match. It adds `{project}` using the basename of `git rev-parse --git-common-dir`, falls back to a plain directory basename, and fixes the same hardcoded `agent_workspace="hermes"` limitation. It additionally adds recall-only extra banks and current-turn synchronous recall, both intentionally outside the local patch's contract. Its Hindsight provider, README, and test edits overlap directly and would require a semantic reconciliation rather than a blind cherry-pick. The local patch remains narrower in lifecycle policy: automatic retain stays on, automatic recall stays off, and deliberate multi-bank operations remain with the official MCP.

### #37563 — alternate explicit-routing design

This PR discovers the nearest `.hindsight/config.toml` by walking up the process cwd and adds a `--hindsight-bank` CLI override. It provides per-project isolation but does not derive a stable Git common-repository identity, does not preserve host-invisible remote workspace paths, and introduces CLI/parser and per-repository config-file behavior absent from the local design. Its draft/dirty state and medium salvageability signal make it a design reference rather than a likely near-term replacement.

### #77554 — core initialization collision

This PR changes the exact `agent_workspace` assignment in `agent/agent_init.py`, sourcing it from `HERMES_KANBAN_BOARD`. It would mechanically conflict with `resolve_agent_workspace()`. Its identity is a board slug pinned even for ordinary CLI boot, whereas this patch routes by actual session/configured workspace and then Git common repository. If it lands first, retain the local resolver and decide explicitly whether Kanban board should be an additional lower-priority input; do not silently replace Git project identity with board identity.

### #52987 — broader routing architecture

The focused follow-up search found one additional close match: a comprehensive multi-bank route engine with workspace, repository-name, and normalized Git-remote predicates, plus fan-out recall and retain. It overlaps many of the same files but solves a broader policy/orchestration problem. Because Peter's intended setup delegates deliberate multi-bank operations to the official Hindsight MCP and keeps auto recall off, adopting this PR wholesale would add substantial unwanted behavior and configuration surface. Its portable Git predicates may be useful upstream precedent if the narrow `{gitProject}` placeholder is later generalized.

## Overlap and rebase risk

Overall conflict risk is **very high**. Three open PRs touch `plugins/memory/hindsight/__init__.py` and its tests, while #77554 and #52987 touch `agent/agent_init.py`. #62687 independently implements almost the same Git-common-directory project derivation. The local patch's differentiators are the explicit remote `git_project` override, preservation of configured remote workspace paths, safe static fallback when `{gitProject}` is unresolved, and intentionally disabled automatic recall.

No inspected PR is a clean substitute today. Merge likelihood is uncertain: #62687 and #37563 are dirty, #37563 remains draft, #77554 is blocked without review, and #52987 is broad despite a high-salvageability keep-open review. GitHub author searches found no prior merged Hermes PRs for the authors of #62687, #37563, or #77554; that is weak author signal, not evidence against their designs.

## Recommendation

Keep deployed commit `c67eb2798` (`7ab0293e4` in the development worktree) in `peter/hermes-patches`, then watch #62687 most closely. If #62687 lands, compare behavior rather than file shape and drop the local patch only if upstream preserves all required invariants: Git common-repository identity across nested paths/worktrees, remote workspace basename fallback, explicit remote override, safe unresolved fallback, accurate `auto_recall=false` prompting, and no forced automatic recall or provider-local multi-bank tool surface.

During rebases, expect direct conflicts in `agent/agent_init.py`, `plugins/memory/hindsight/__init__.py`, the Hindsight README, and provider tests. Re-run the focused 101-test set and the real-profile routing dry run after reconciliation. Treat #37563 as an alternate configuration model, #77554 as an initialization collision, and #52987 as broader architecture—not as replacements for the narrow local contract.

## Raw search queries used

Authenticated direct inspection:

```text
gh api repos/NousResearch/hermes-agent/pulls/62687
gh api repos/NousResearch/hermes-agent/pulls/62687/files --paginate
gh api repos/NousResearch/hermes-agent/pulls/62687/reviews --paginate
gh api repos/NousResearch/hermes-agent/issues/62687/comments --paginate
gh api repos/NousResearch/hermes-agent/pulls/37563
gh api repos/NousResearch/hermes-agent/pulls/37563/files --paginate
gh api repos/NousResearch/hermes-agent/pulls/37563/reviews --paginate
gh api repos/NousResearch/hermes-agent/pulls/77554
gh api repos/NousResearch/hermes-agent/pulls/77554/files --paginate
gh api repos/NousResearch/hermes-agent/pulls/52987
gh api repos/NousResearch/hermes-agent/pulls/52987/files --paginate
gh api repos/NousResearch/hermes-agent/pulls/52987/reviews --paginate
```

Focused authenticated searches (not a broad archaeology pass):

```text
repo:NousResearch/hermes-agent is:open hindsight "git project"
repo:NousResearch/hermes-agent is:open hindsight bank project workspace
repo:NousResearch/hermes-agent is:open gitProject
repo:NousResearch/hermes-agent is:pr is:merged author:gcunharodrigues
repo:NousResearch/hermes-agent is:pr is:merged author:iRonin
repo:NousResearch/hermes-agent is:pr is:merged author:Bazyl2101
```

# Preserve Kanban completion artifacts

- Date: 2026-07-05
- Repo: `/opt/hermes-agent` (`NousResearch/hermes-agent` upstream)
- Patch ref: `688174f58` (`fix: preserve kanban completion artifacts`)
- Branch: `peter/hermes-patches` (historical inspection state)
- Local status: clean tracked tree except branch ahead state; no source files modified by this catalogue task
- Rebase update (2026-07-13): superseded by upstream `e6c42b5d8` (`fix(kanban): preserve scratch completion artifacts`) and hardening follow-up `8030b01a2` (`fix(kanban): harden durable artifact handoff`). The local functional commit was intentionally dropped during rebase onto `main`.
- Motivation: Kanban workers can declare completion artifacts that live in managed scratch workspaces. `complete_task()` records those paths, then immediately runs scratch cleanup, so the gateway notifier and later humans can be handed dead artifact paths. Peter hit this with completed task `t_30197418`, whose referenced `open-design-hermes-fit.md` had to be recovered from logs after the scratch workspace was deleted.
- Changed files:
  - `hermes_cli/kanban_db.py` (+124): calls `_preserve_completion_artifacts()` before task completion transaction and scratch cleanup; copies declared `metadata["artifacts"]` into durable task attachments, records original paths, attachment ids, and preservation errors.
  - `tests/hermes_cli/test_kanban_db.py` (+65): regression coverage for artifact survival after scratch cleanup and basename collision handling.
- Tests / verification:
  - `python3 -m pytest tests/hermes_cli/test_kanban_db.py::test_completion_artifacts_survive_scratch_cleanup tests/hermes_cli/test_kanban_db.py::test_completion_artifact_name_collisions_are_preserved tests/hermes_cli/test_kanban_db.py::test_cleanup_workspace_removes_managed_scratch_dir -q -o 'addopts='` → 3 passed
  - `python3 -m pytest tests/hermes_cli/test_kanban_db.py -q -o 'addopts='` → 226 passed
  - `python3 -m pytest tests/tools/test_kanban_tools.py tests/plugins/test_kanban_attachments.py tests/gateway/test_kanban_notifier.py -q -o 'addopts='` → 117 passed

## Local patch summary

The patch is a narrowly scoped defensive copy step in `complete_task()`. Before `_end_run()`, the completed event payload, and `_cleanup_workspace()`, it inspects `metadata["artifacts"]`; for each readable file it creates the task attachments directory, sanitizes the basename, chooses a collision-free destination, copies with `shutil.copy2()`, registers the durable file via `add_attachment()`, and rewrites `metadata["artifacts"]` to the durable paths. It preserves `metadata["artifacts_original"]` and `metadata["artifact_attachment_ids"]`; missing/unreadable files are recorded under `artifact_preservation_errors` without blocking completion.

This is intentionally best-effort. It fixes the user-facing data-loss mode without changing the worker tool API or making artifact declaration a hard completion gate.

## Upstream overlap

Ages are relative to the 2026-07-05 patch date.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | [39747](https://github.com/NousResearch/hermes-agent/issues/39747) | kanban_complete artifacts silently lost on scratch workspaces — file deleted before gateway notifier delivers | 30d | `angelogalanti`, association `NONE` | No comments | n/a | Conceptual overlap: exact bug motivating local patch | Medium: precise bug report, but no maintainer activity |
| PR | [39777](https://github.com/NousResearch/hermes-agent/pull/39777) | fix(kanban): preserve scratch completion artifacts | 30d | `yinkev`, association `NONE` | No comments/reviews | 2 files, +241/-29 (`hermes_cli/kanban_db.py`, `tests/hermes_cli/test_kanban_db.py`) | High: same function/test file, same preservation strategy; local patch may be a smaller variant | Medium-low: directly relevant but stale/open for a month and from non-member |
| Issue | [41820](https://github.com/NousResearch/hermes-agent/issues/41820) | Feature request: Make Kanban Done results obvious and durable | 27d | `elhusseinyIbrahim`, association `NONE` | Contributor `iborazzi` offered a UI/API fallback plan; no maintainer decision | n/a | Low-medium: adjacent visibility/durability; not specifically scratch artifact copying | Low-medium: feature-shaped, no maintainer sign-off |
| PR | [55903](https://github.com/NousResearch/hermes-agent/pull/55903) | fix: archive kanban completion artifacts | 5d | `alexwill87`, association `NONE` | No comments/reviews | 2 files, +161/-0 (`hermes_cli/kanban_db.py`, `tests/hermes_cli/test_kanban_db.py`) | Very high: same file/function and best-effort archive semantics | Medium: recent, focused, close to local design; no maintainer signal yet |
| Issue | [53699](https://github.com/NousResearch/hermes-agent/issues/53699) | [Bug]: kanban_complete accepts completion referencing a nonexistent durable artifact | 8d | `richfeather-cpu`, association `NONE` | Referenced by collaborator triage in #56685 | n/a | Medium: hard validation of claimed artifacts; local patch records errors instead of rejecting | Medium: has sibling PRs and collaborator triage, but policy choice unresolved |
| PR | [53723](https://github.com/NousResearch/hermes-agent/pull/53723) | fix(kanban): validate artifact file existence before accepting completion | 8d | `liuhao1024`, association `CONTRIBUTOR` | No comments/reviews found | 3 files, +65/-21 (`tools/kanban_tools.py`, `tests/tools/test_kanban_tools.py`, notifier test) | Medium: tool-layer validation may compose with local DB-layer preservation, but semantics differ | Medium-low: contributor author, focused, but no maintainer signal and does not solve scratch deletion by itself |
| PR | [56685](https://github.com/NousResearch/hermes-agent/pull/56685) | fix(kanban): require durable artifact readback on completion | 3d | `felipegermano17`, association `NONE` | Collaborator `alt-glitch` triaged: relates #53699/#55903 and contrasts hard gate vs best-effort archive | 3 files, +204/-19 (`hermes_cli/kanban_db.py`, `tests/hermes_cli/test_kanban_core_functionality.py`, `tests/tools/test_kanban_tools.py`) | Very high: same core file plus incompatible completion semantics (`CompletionArtifactError` vs best-effort) | Unknown-medium: explicit collaborator triage but design fork unresolved |
| PR | [58286](https://github.com/NousResearch/hermes-agent/pull/58286) | fix(kanban): persist completion artifacts before cleanup | 1d | `cedricworldwide`, association `NONE` | No comments/reviews | 2 files, +270/-2 (`tools/kanban_tools.py`, `tests/tools/test_kanban_tools.py`) | Medium-high: tool-layer persistence may duplicate DB-layer preservation and alter event metadata | Low-medium: very recent but PR template incomplete and no maintainer signal |
| PR | [37537](https://github.com/NousResearch/hermes-agent/pull/37537) | feat(kanban): first-class task artifact registry | 33d | `thedavidmurray`, association `CONTRIBUTOR` | No comments/reviews found | 2 files, +218/-0 (`hermes_cli/kanban_db.py`, new `tests/hermes_cli/test_kanban_artifacts.py`) | High if revived: schema/model-level artifact registry may supersede metadata-list preservation | Low-medium: broader design and stale, but contributor association helps |
| Issue | [36046](https://github.com/NousResearch/hermes-agent/issues/36046) | [Bug]: kanban artificat issue [not created or deleted] | 35d | `nirolfa`, association `NONE` | Collaborator `alt-glitch` first linked to #33774/#33916, then re-triaged on 2026-06-28 that leaf-task scratch artifacts still get deleted and merged cleanup guards do not cover it | n/a | High conceptually: same symptom class, shows prior fixes incomplete | Medium: maintainer/collaborator acknowledged current gap, but issue is noisy/older |

## Notes on most relevant upstream items

- **#39747 / #39777** are the earliest exact upstream articulation of the local problem: `kanban_complete(artifacts=[...])` records paths in a scratch workspace and completion cleanup deletes them before the gateway notifier can upload. #39777 appears to implement the same conceptual fix as the local patch, but is larger (+241/-29) and older. If upstream adopts it, expect direct conflicts in `complete_task()` and tests around scratch cleanup.

- **#55903** is the closest current sibling to Peter's patch. Its PR body says it archives explicit `kanban_complete(artifacts=[...])` deliverables into durable per-task storage before scratch cleanup, keeps completion best-effort, and records missing/bad paths in metadata. That matches Peter's local policy choice. Conflict risk is very high because it touches the same function and regression-test area, but it is also the most likely upstream vehicle to make this patch obsolete.

- **#56685** is the main design alternative. The collaborator triage comment explicitly names #53699 and #55903 and frames the policy split: #56685 refuses completion when declared artifacts are missing/empty/not-files and records sha256/size/readback metadata, whereas #55903 is best-effort. Peter's local patch aligns more with #55903 than #56685. If maintainers prefer the hard-gate contract, Peter's patch may need adaptation or a local policy override.

- **#53723 / #53699** cover a related but distinct correctness contract: declared durable artifacts should exist before `kanban_complete` accepts them. These do not fully solve scratch-workspace deletion unless combined with copying/archiving before cleanup. They could still be merged alongside Peter's patch if validation occurs in `tools/kanban_tools.py` and preservation occurs in `hermes_cli/kanban_db.py`, but missing-artifact semantics must be reconciled.

- **#36046** is an older user symptom report. The key maintainer/collaborator signal is the 2026-06-28 re-triage: existing scratch cleanup fixes for parent/child handoff and data-loss containment do not cover a leaf task that produces a user-facing deliverable inside its own scratch subfolder. That is exactly the gap this patch closes.

- **Prior merged/closed context:** #33774 (`Kanban parent-child handoff: scratch workspace GC destroys artifacts before child can read them`) and #33916 (`fix: defer scratch workspace cleanup when task has active children`) addressed active-child handoff. #28818 addressed cleanup deleting real source directories. Those fixes are already represented near the local tests (`test_cleanup_workspace_refuses_path_outside_scratch_root`, deferred cleanup tests), but they do not preserve leaf completion artifacts for humans/gateway uploads.

## Recommendation

The local artifact-preservation patch is now obsolete: upstream `e6c42b5d8` implemented the durable scratch-artifact flow, and `8030b01a2` subsequently hardened the handoff across the DB, tool, gateway, dashboard, and tests. It was intentionally dropped during the 2026-07-13 rebase. Retain this report as historical context only; future work should build on the upstream implementation.

## Raw search queries used

- Git/local inspection:
  - `git status --short --branch`
  - `git log --oneline --decorate -n 12`
  - `git show --stat --oneline --decorate --find-renames 688174f58`
  - `git show --name-only --format=fuller 688174f58`
  - `git diff --stat 688174f58^ 688174f58`
  - `git show --unified=80 --find-renames 688174f58 -- hermes_cli/kanban_db.py tests/hermes_cli/test_kanban_db.py`
- GitHub REST issue/PR lookups:
  - `GET /repos/NousResearch/hermes-agent/issues/{39747,41820,55903,39777,56685,58286,53723,37537,53699,36046}`
  - `GET /repos/NousResearch/hermes-agent/pulls/{55903,39777,56685,58286,53723,37537}`
  - `GET /repos/NousResearch/hermes-agent/pulls/{n}/files`
  - `GET /repos/NousResearch/hermes-agent/pulls/{n}/reviews`
  - `GET /repos/NousResearch/hermes-agent/issues/{n}/comments`
- GitHub issue search:
  - `repo:NousResearch/hermes-agent is:open kanban completion artifacts scratch cleanup`
  - `repo:NousResearch/hermes-agent is:open kanban_complete artifacts attachments`
  - `repo:NousResearch/hermes-agent is:open "scratch workspace" artifacts`
  - `repo:NousResearch/hermes-agent is:open "completion artifacts" kanban`
  - `repo:NousResearch/hermes-agent is:open "artifact" "kanban_complete"`

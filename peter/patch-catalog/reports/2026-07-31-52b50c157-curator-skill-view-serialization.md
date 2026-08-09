# Serialize guarded curator skill reads

- Date: 2026-07-31
- Repo: `NousResearch/hermes-agent`
- Patch ref: `52b50c157fee72ced745378e5de0a762f6d6cafb` → `652b895c7` (pre-2026-08-09 active) → `e8071ce7e3` (active)
- Branch: `peter/hermes-patches` (originally authored on `peter/curator-parallel-skill-view`)
- Local status: committed local patch and committed catalogue entry
- Motivation: `hermes curator run --consolidate` could execute background-review `skill_view` calls in copied parallel worker contexts. The read-before-write marks written to a `ContextVar` did not flow back to the parent context, so later `skill_manage` patches were falsely rejected and repeated failures could trigger `same_tool_failure_halt`.
- Changed files: `agent/tool_dispatch_helpers.py`; `tests/run_agent/test_tool_batch_segmentation.py`
- Tests / verification: regression failed before the fix and passed afterward; focused canonical suite reported 66 passed, 1 skipped; `tests/run_agent/test_run_agent.py` reported 220 passed with one unrelated existing warning; full canonical suite reached 2479 collected files with four unrelated environment/timing failures and one flaky TUI gateway test passing on retry; independent review reported no blockers.

## Local patch summary

The patch makes `skill_view` a sequential barrier only when `is_background_review()` is true. This keeps its read-before-write authorization update in the parent execution context while retaining parallel `skill_view` calls for foreground work. Two segmentation tests cover background serialization and unchanged foreground parallelism. TUI behavior is explicitly out of scope.

## Upstream overlap

Age is measured at 2026-07-31. Search and item metadata were fetched with authenticated `gh`.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#73975](https://github.com/NousResearch/hermes-agent/pull/73975) | fix(skills): preserve review read marks across tool contexts | 2 days; opened 2026-07-29, updated 2026-07-30 | `zyz619963502zyz`; association `NONE` | Automated sweeper comment by `teknium1` (`CONTRIBUTOR`) says “No substantive correctness issues,” marks it keep-open/high-salvageability, and identifies it as the direct fix; no submitted human review or approval | 1 commit; 2 files; +86/-9: `tools/skill_manager_tool.py`, `tests/tools/test_skill_manager_tool.py` | **Low mechanical, very high semantic.** It does not touch either local file, but solves the same copied-context defect at the authorization-store layer and would likely make local serialization unnecessary. | **Medium-high**, not certain: exact regression, focused tests, direct issue link, P2 labels, and positive automated triage are strong signals; it remains open with no formal review/approval. |
| Issue | [#73965](https://github.com/NousResearch/hermes-agent/issues/73965) | bg-review: read-before-write guard uses turn-scoped ContextVar, preventing multi-turn view→patch workflow | 2 days; opened/updated 2026-07-29 | `cult3010`; association `NONE`; reports 13 observed failures across four skills | Automated triage identifies #73975 as the sole/best direct fix and recommends merging it; no maintainer decision is recorded | N/A | **Very high semantic, low mechanical.** It names the same ContextVar/copied-context authorization loss and explicitly notes curator consolidation may be affected. | N/A for an issue; resolution likelihood is tied to #73975 and therefore **medium-high but unconfirmed**. |
| PR | [#59175](https://github.com/NousResearch/hermes-agent/pull/59175) | [codex] Fix background review skill read-before-write | 26 days; opened 2026-07-05, updated 2026-07-15 | `doncazper`; association `CONTRIBUTOR` | No comments, reviews, or approval | 2 commits; 5 files; +180/-14, including `agent/background_review.py` and skill-manager tests | **Low mechanical, medium semantic.** It strengthens prompts/guard coverage but does not address parallel copied-context mark propagation or touch the local files. | **Low-medium**: relevant and tested, but older, broader, inactive since 2026-07-15, and no maintainer signal; #73975 is the more exact implementation. |
| Issue | [#63964](https://github.com/NousResearch/hermes-agent/issues/63964) | blocker-report: background curator loops on skill_manage patch errors | 18 days; opened 2026-07-13, updated 2026-07-24 | `calltelemetry-jason`; association `NONE`; repeated operational evidence | Automated triage says proposed #63991 is only partial and should not merge yet; no maintainer resolution | N/A | **Medium semantic, low mechanical.** It corroborates repeated read-before-write failures and retry-loop impact, including background curator, but combines unrelated schema/security refusal cases. | N/A; exact issue closure is **unknown** because its scope is broader than this local fix or #73975. |
| Issue | [#63388](https://github.com/NousResearch/hermes-agent/issues/63388) | Curator/skill_manage fails in background: “SKILL.md content has not been loaded in this review turn” | 19 days; opened/updated 2026-07-12 | `Larsonga1`; association `NONE` | `alt-glitch` (`COLLABORATOR`) marked it duplicate of #62397 and pointed to prompt-level fixes; this is triage, not endorsement of the local implementation | N/A | **Medium semantic, low mechanical.** It independently confirms the curator-visible symptom, but its reproduction emphasizes a missing prior read rather than a read mark lost after parallel execution. | N/A; retained as symptom evidence, not an exact implementation candidate. |

## Notes on most relevant upstream items

### #73975 is exact semantic overlap and a broader architectural fix

The PR body describes the same execution-model mismatch: each tool call runs in a copied `Context`, while `skill_view()` replaced an immutable `frozenset` only inside that copy. Its solution changes the mark store to a fresh per-review mutable, lock-protected object shared by copied contexts, with tests for cross-context authorization and review isolation.

That differs from the local patch (`52b50c157`, now active as `652b895c7`): it avoids the defect by serializing background-review `skill_view` dispatch, whereas #73975 makes the authorization state itself compatible with copied/concurrent contexts. Because #73975 preserves concurrency and fixes later-turn/copied-context cases beyond one batch planner, it is the stronger upstream-shaped solution if its isolation and locking tests remain valid. The rebase adapted the local patch to upstream's reader/writer-aware batch planner without changing this contract. The risk remains semantic redundancy after merge.

The strongest positive signal is the repository sweeper comment from `teknium1`, which calls the fix focused, finds no substantive correctness issue, and rates salvageability high. This is automated triage and the account's API association is only `CONTRIBUTOR`; it must not be represented as formal maintainer approval. No submitted review exists.

### #59175 and the older curator reports are adjacent, not substitutes

#59175 improves review prompts and expands guard behavior. #63388 and #63964 show that the false-refusal symptom and retry loops affect real background curator runs. None of these older items directly repairs the copied-context propagation defect in the tool executor. They support the motivation but do not supersede the local patch by themselves.

### `same_tool_failure_halt` overlap is consequence-level only

Authenticated search found #53959 about fallback strategies for `same_tool_failure_halt`, but it is a generic guardrail feature request with no curator/read-before-write implementation overlap. The local patch prevents a false repeated failure at its source; it does not modify halt thresholds or retry policy, so #53959 was not promoted into the overlap table.

## Recommendation

Keep active patch `652b895c7` temporarily because it is narrow and tested. Watch #73975 closely. If #73975 merges, verify curator consolidation with parallel `skill_view` calls and the background-review read-before-write tests on the merged implementation; then drop the local serialization patch if the shared mark store preserves authorization across copied contexts without cross-review leakage. If both are retained during a transition, expect little textual conflict but unnecessary loss of background-review read parallelism.

## Raw search queries used

```text
repo:NousResearch/hermes-agent is:open curator consolidate skill_view
repo:NousResearch/hermes-agent is:open "background review"
repo:NousResearch/hermes-agent is:open "skill_view" parallel
repo:NousResearch/hermes-agent is:open ContextVar executor
repo:NousResearch/hermes-agent is:open "read-before-write"
repo:NousResearch/hermes-agent is:open same_tool_failure_halt
repo:NousResearch/hermes-agent is:open curator skill
repo:NousResearch/hermes-agent is:open tool parallel context
```

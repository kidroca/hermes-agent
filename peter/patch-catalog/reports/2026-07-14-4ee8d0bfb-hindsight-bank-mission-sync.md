# Sync configured Hindsight bank missions

- Date: 2026-07-14
- Repo: `/opt/hermes-agent`
- Patch ref: `4ee8d0bfb` (reviewed) → `40b1bb407` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch inspected; this catalogue pass changes only `peter/patch-catalog/` documentation.
- Motivation: Hermes parsed `bank_mission` and `bank_retain_mission` from profile configuration but never transmitted them to Hindsight, leaving the live bank's `reflect_mission` and `retain_mission` null.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`.
- Tests / verification: focused `TestBankMissionSync` class — **5 passed**; relevant suite — **147 passed in 11.96s**; `git diff --check` and `py_compile` passed; a live end-to-end sync and recheck against `peter-personal-memory` succeeded. Pre-commit review was approved after its early-success-flag blocker was corrected.

## Local patch summary

On each real Hindsight operation, the provider now lazily synchronizes configured, nonempty mission values before retain/recall/reflect work:

- reads the existing bank config with `client.banks.get_bank_config()`;
- PATCHes only drifted `reflect_mission` and/or `retain_mission` through `BankConfigUpdate`;
- marks synchronization complete only after the GET and any required PATCH succeed;
- leaves blank local values deliberately unmanaged rather than clearing a remote mission;
- treats configuration API failures as nonfatal to the real memory operation, retries on a later real request, and emits one warning until a successful synchronization resets the latch.

Tests cover dict and model-shaped config responses, selective no-op behavior, blank-config API avoidance, and nonblocking failure behavior. This is intentionally request-driven: no startup-only sync, background retry queue, polling, or idle traffic is introduced.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | [#18774](https://github.com/NousResearch/hermes-agent/issues/18774) | Hindsight plugin reads `bank_mission`/`bank_retain_mission` but does not sync them to Hindsight Banks API | created 2026-05-02; unchanged since 2026-05-02 | `Qwinty`, `CONTRIBUTOR`; authenticated search found no merged upstream PRs by this author | No comments or maintainer response | N/A | **High semantic overlap** — this is the exact defect | Unknown: valid report, but no maintainer activity |
| PR | [#42320](https://github.com/NousResearch/hermes-agent/pull/42320) | fix(memory): sync Hindsight bank missions | created 2026-06-08; updated 2026-07-14 | `Qwinty`, `CONTRIBUTOR`; no prior merged upstream PRs found | `teknium1` says the premise is valid and marks it `keep_open`/high salvageability, but identifies an incompatible `SimpleNamespace` fallback and missing compatibility regression; no approval | 3 files, +383/-3; same provider and provider-test files plus README | **High** — same fields, Banks GET/PATCH flow, and test file | Medium: directly addresses the bug but has an unresolved correctness review |
| PR | [#44264](https://github.com/NousResearch/hermes-agent/pull/44264) | hindsight: send configured bank missions via `acreate_bank` and close stale client before retry replacement | created 2026-06-11; updated 2026-07-14 | `drphil2691`, `NONE`; authenticated search found no merged upstream PRs by this author | `teknium1` says both identified gaps are real but marks `keep_open`/medium salvageability; requests wrapper-level client-close handling and schema/docs for extra keys | 2 files, +139/-0; same provider and provider-test files | **Medium-high** physical overlap; mission transport uses `acreate_bank` rather than the bank-config GET/PATCH API | Low-medium: broader mixed-purpose PR with unresolved review |

## Notes on most relevant upstream items

- **#18774 is the original exact bug report.** Its reproduced state and manual workaround match the local patch: the configuration values are loaded in Hermes but the Banks API reports null `reflect_mission`/`retain_mission`; direct bank-config PATCH succeeds. The local live `peter-personal-memory` verification confirms the same contract on the deployed path.
- **#42320 is the closest upstream implementation candidate.** It uses the public generated `client.banks.get_bank_config`/`update_bank_config` APIs, but syncs during initialization and after embedded-daemon startup, maintains a process cache, and treats explicit blank/null config as a request to clear remote overrides. The local patch is deliberately narrower and more resilient for ongoing operations: it defers work to a real request, leaves blank config unmanaged, allows the requested operation through if config sync fails, and deduplicates warning logs. Both patches touch the same method neighborhood and tests, so a rebase will require semantic reconciliation rather than a mechanical keep-both merge.
- **#42320 has not cleared review.** The only recorded review specifically rejects its `SimpleNamespace` fallback as incompatible with the generated, validated `BankConfigUpdate` endpoint and asks for a missing-model compatibility test. The local patch imports and supplies `BankConfigUpdate` on the actual update path; retain that real-client validation point if adopting upstream code.
- **#44264 confirms the same user-visible gap but is not a replacement.** It calls `acreate_bank()` once before operations and combines that change with stale-client cleanup and two additional undocumented config settings. Its reviewer requested changes are unrelated to the local patch's narrow GET/PATCH mission sync, but its edits make this file a likely rebase-conflict location.

## Recommendation

Keep `4ee8d0bfb` locally. It is verified against the real bank and has a narrowly bounded, demand-driven failure policy. Track **#42320** as the likely upstream successor, but do not drop this patch unless its merged form is checked against all local contract details: only-drifted PATCH, nonempty-only ownership, no failure blockage of retain/recall/reflect, retry on a later real operation, and warning deduplication. Watch **#44264** only for file-level conflicts and its separate retry-cleanup work. Overall upstream conflict risk is **high** because #42320 changes the exact provider/test surfaces; merge likelihood for the local semantics is **medium/unknown**, pending a maintainer response or a corrected #42320.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open hindsight bank mission`
- `repo:NousResearch/hermes-agent is:open bank_mission`
- `repo:NousResearch/hermes-agent is:open reflect_mission retain_mission`
- `repo:NousResearch/hermes-agent is:pr is:open hindsight config`
- `repo:NousResearch/hermes-agent is:issue is:open hindsight config`
- `repo:NousResearch/hermes-agent is:pr is:merged author:Qwinty`
- `repo:NousResearch/hermes-agent is:pr is:merged author:drphil2691`

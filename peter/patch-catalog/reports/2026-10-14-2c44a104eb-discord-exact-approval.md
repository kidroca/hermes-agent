# Bind Discord approval buttons to exact queue requests

- Date: 2026-10-14 (Europe/Sofia); authenticated upstream snapshot taken just after local midnight.
- Repo: `/home/kidroca/.hermes/cache/scratch/hermes-discord-exact-id`
- Patch ref: `2c44a104ebf618d8b9fb9fb865945a482a2cfd33`
- Branch: `peter/discord-exact-approval`
- Local status: committed functional candidate on parent `255404440a02c73127b0e2f909a620d3c9cccc50`; catalogue pending parent review/commit. Not pushed or activated. `/opt/hermes-agent` is outside this task's write scope. Root `DISCORD-EXACT-ID-RESULT.md` is an existing private, untracked handoff, not catalogue content.
- Motivation: an authorized operator clicking card B must not answer FIFO-oldest A; a stale A card must not answer later B. This is request-association integrity, not a newly claimed authorization bypass.
- Changed files: `gateway/run_turn_runner.py`, `plugins/platforms/discord/adapter.py`, new `tests/gateway/test_discord_exec_approval_exact_id.py`, `tests/gateway/test_exec_approval_timeout_notice.py`. Actual commit: 4 files, 168 additions, 12 deletions.
- Tests / verification: independent Codex review **APPROVE** in `/home/kidroca/.hermes/cache/scratch/proactive-discord-review-result.txt`. Parent canonical per-file runner receipt `/home/kidroca/.hermes/cache/scratch/proactive-discord-parent-check/renewed-final.log`: **337 passed, 14 files, 0 failed**, including 40 exact-ID tests and adjacent Telegram/Slack/Matrix/Feishu coverage. `parent-verification.json` records stable reviewed-source hashes, Ruff pass, health 0 blocking/0 advisory and diff-check pass. This catalogue pass inspected actual committed diff and independently ran `git diff --check`; it did not rerun tests. Python 3.11 used a documented typing/bootstrap compatibility launcher; preferred-interpreter validation and live Discord validation remain unperformed.

## Local patch summary

The queue-generated `request_id` is carried by the existing notifier through a copied metadata dict under `approval_request_id`. The authoritative value overrides any inherited metadata key, even when absent, without mutating shared thread metadata. Discord snapshots that value into a keyword-only view argument and calls the existing resolver with that exact ID. Missing/empty IDs return zero without invoking FIFO; stale/unknown IDs use the resolver's exact-miss path and display the existing expired state.

All four choices (once/session/always/deny), existing user/admin admission gates, first-answer behavior and typed `/approve` FIFO remain intact. No resolver redesign, new adapter ABI, retry, telemetry, lifetime redesign or proactive invalidation was added. Regression tests compose real queue entries, notifier, base prompt, Discord renderer and resolver with mocked transport, covering overlapping requests, expired/settled cards, missing/unknown IDs, duplicate clicks and admission gates. Reviewer advisories about malformed-ID tests and valid-A-to-valid-B metadata mutation are nonblocking coverage opportunities, not implemented changes.

## Upstream overlap

All rows below were refreshed with authenticated `gh`; ages are elapsed whole days at the snapshot, not estimates from titles. Merged-author counts mean repository merged PRs visible to search, not endorsement of this implementation. Search dates are UTC.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| Issue | [104915](https://github.com/NousResearch/hermes-agent/issues/104915) | Discord approval buttons resolve the oldest request instead of the displayed request | 36d | sake303; NONE; 0 merged PRs found | One corroborating comment by Enough1122 (NONE); no maintainer comment in fetched thread | Exact symptom and acceptance contract; no implementation | Exact semantic overlap | N/A (issue); implementation landing unknown |
| PR | [104960](https://github.com/NousResearch/hermes-agent/pull/104960) | fix(gateway): bind Discord exec-approval cards to their own request (#104915) | 36d | liuhao1024; NONE; 29 merged PRs | Reviews by andrexibiza, NONE, COMMENTED; no maintainer approval fetched | 22 files, +1074/-209; both local production files; new Discord `exec_approval.py` owner | High: exact identity fix plus owner extraction and broader adapter ABI | Unknown: substantive review/response, but extraction follow-up lacks fetched approval; API mergeability unknown |
| PR | [125039](https://github.com/NousResearch/hermes-agent/pull/125039) | fix(approval): resolve button taps against their own request (#124974) | 16d | dskwe; NONE; 10 merged PRs | Two COMMENTED reviews by andrexibiza (NONE); author reports fixes; no maintainer approval fetched | 20 files, +863/-65; shared base/runner and Discord plus other adapters | High: first-class prompt/request-ID transport replaces local metadata carrier | Unknown: active technical iteration is not maintainer backing; API mergeability unknown |
| PR | [87554](https://github.com/NousResearch/hermes-agent/pull/87554) | fix: bind gateway approval buttons to request ids | 58d | teknium1; COLLABORATOR; 10868 merged PRs visible | Collaborator authored; no reviews; bot/non-maintainer comments only | 8 files, +115/-25; older `gateway/run.py` and Discord callback | High semantic overlap; older locations require adaptation | Medium, cautiously: collaborator authorship is real signal, but no approval, old update and unknown mergeability prevent high confidence |
| PR | [6105](https://github.com/NousResearch/hermes-agent/pull/6105) | fix(approval): bind interactive approvals to exact requests | 188d | mrshu; NONE; 0 merged PRs found | teknium1 COLLABORATOR automated sweeper comment: keep_open / medium salvageability; author later rebuilt | 18 files, +263/-71; older gateway notifier, Discord and other adapters | High semantic overlap; missing-ID Discord fallback still FIFO in fetched diff | Unknown: salvage guidance is not merge approval; current diff retains weaker unbound-card behavior |
| PR | [56487](https://github.com/NousResearch/hermes-agent/pull/56487) | fix: acknowledge Discord approval buttons | 104d | aaronallan63-afk; NONE; 0 merged PRs found | teknium1 COLLABORATOR COMMENTED automated sweeper review; requests rescope/removal of telemetry | 2 files, +299/-16; Discord adapter and component-auth tests | Medium-high callback hunk conflict; not an exact-ID replacement | Low as currently submitted: review asks material rescope; no approval; unknown mergeability |

## Notes on most relevant upstream items

- **#104915:** open, created `2026-09-07T09:27:17Z`, updated `2026-09-27T07:11:11Z`. The reported stale-A/live-B and reverse-card selection contracts match this patch exactly. Corroboration is from a non-maintainer; no upstream acceptance is implied.
- **#104960:** open, created `2026-09-07T09:44:30Z`, updated `2026-09-07T16:25:41Z`. Latest fetched diff broadens nine adapters and extracts Discord approval ownership. Reviews recount repaired ABI/fail-closed/lifetime problems, then require owner extraction; author says extraction is done. Those are external review/author claims, not this catalogue's independent test execution. Expect both notifier reconciliation and movement of the view out of `adapter.py` if this lands.
- **#125039:** open, created `2026-09-27T09:15:17Z`, updated `2026-09-30T14:22:59Z`. It adds `ExecApprovalPrompt.request_id`; Discord passes `prompt.request_id` directly to the resolver. Its fetched Discord callback does not locally guard missing IDs; do not drop this patch merely because an ID field exists upstream. Preserve the zero-resolution contract for unbound cards and check actual producer/consumer behavior after integration. Reviews discuss Teams/QQ/Matrix settlement defects; authors report subsequent repairs. Neither review is maintainer approval.
- **#87554:** open, created `2026-08-16T08:31:18Z`, updated `2026-08-16T10:09:54Z`. Strongest maintainer-adjacent author signal, but its fetched Discord callback explicitly falls back to session FIFO when the ID is absent. Its constructor inserts an optional positional ID before the allowlist; local keyword-only addition avoids that API ambiguity. This is not yet an equivalent fail-closed replacement.
- **#6105:** open, created `2026-04-08T09:58:28Z`, updated `2026-07-12T18:08:58Z`. Metadata-carrier approach overlaps closely, but its Discord missing-ID branch explicitly invokes FIFO. The collaborator sweeper guidance is automated and should not be represented as approval of the latest rebuilt diff.
- **#56487:** open, created `2026-07-01T15:48:04Z`, updated `2026-07-15T13:10:50Z`. Fetched callback still resolves by session alone. Collaborator review requests a minimal current-main defer fix, a demonstrated delayed/expired edit-response regression, removal of outbound webhook telemetry without generic opt-in, and retention of the shared timeout helper. Acknowledgement is separate from request identity.
- Additional exact lineage was discovered through #125039 reviews and directly refreshed: [#124398](https://github.com/NousResearch/hermes-agent/pull/124398), keeltrace/NONE, 7 visible merged PRs, created `2026-09-26T20:34:43Z`, updated `2026-10-02T18:03:03Z`, **closed unmerged**, 19 files +334/-55; first-class shared prompt transport and native consumers, including fail-closed guards. [#124987](https://github.com/NousResearch/hermes-agent/pull/124987), happy5318/NONE, 1 visible merged PR, created `2026-09-27T08:51:40Z`, updated `2026-10-06T14:30:29Z`, **closed unmerged**, 21 files +971/-53; metadata forwarding and other adapters but no Discord/Slack files. Its closing author comment preserves a separate Discord/Slack companion branch. Neither is evidence of a landed fix. Historical review descriptions calling these narrow/open are superseded by this direct snapshot.
- Narrow request-ID search also surfaced open issues [#124974](https://github.com/NousResearch/hermes-agent/issues/124974) and [#135905](https://github.com/NousResearch/hermes-agent/issues/135905), class-wide corroboration from search only. Owner-auth, timeout and durable-receipt changes were not expanded into unrelated archaeology.

## Recommendation

Retain this small, independently reviewed Discord-only candidate locally, pending the parent's catalogue review. Do not push, restart or activate as part of cataloguing. Upstream conflict risk is **high**, because several exact implementations touch the same runner/view contract, especially #104960 and #125039. Keep metadata and any future typed request-ID representation consistent; never leave a stale inherited ID or missing-ID FIFO fallback in a native button path.

At the next explicitly approved upstream update, inspect the actual landed implementation and rerun composed stale-A/live-B, reverse click order, all choices, duplicate/missing-ID and authorization regressions. Drop/supersede this local commit only after equivalent behavior is demonstrated. Track #104960/#125039/#87554 first; #56487 is acknowledgement work, not replacement evidence. No exhaustive repository-wide inventory, upstream mergeability simulation, full-suite result or live transport validation is claimed.

## Raw search queries used

Authenticated `gh auth status -h github.com` succeeded. Known issue/PR refreshed before discovery. Direct REST reads used `gh api repos/NousResearch/hermes-agent/issues/104915` and `/comments`; `gh api repos/NousResearch/hermes-agent/pulls/<N>`, `/files`, `/reviews`, plus `issues/<N>/comments` for N = 56487, 104960, 125039, 87554, 6105, 124398, 124987. #56487 inline `/pulls/56487/comments` also inspected. Direct pulls for closed #124398/#124987 confirmed `merged=false` and `merged_at=null`.

Search via `gh api -X GET search/issues -f 'q=<query>' -f per_page=20`:

```text
repo:NousResearch/hermes-agent is:open discord approval request_id
repo:NousResearch/hermes-agent is:pr is:open discord approval
repo:NousResearch/hermes-agent is:open "ExecApprovalView"
repo:NousResearch/hermes-agent is:pr is:merged author:aaronallan63-afk
repo:NousResearch/hermes-agent is:pr is:merged author:sake303
repo:NousResearch/hermes-agent is:pr is:merged author:liuhao1024
repo:NousResearch/hermes-agent is:pr is:merged author:dskwe
repo:NousResearch/hermes-agent is:pr is:merged author:teknium1
repo:NousResearch/hermes-agent is:pr is:merged author:mrshu
repo:NousResearch/hermes-agent is:pr is:merged author:keeltrace
repo:NousResearch/hermes-agent is:pr is:merged author:happy5318
```

The broad Discord-approval query returned 340 total matches with only the first 20 fetched; it was a bounded discovery aid, not exhaustive evidence. The focused request-ID query returned 11 matches and the view-name query 12, both fully enumerated with `incomplete_results=false`. No authentication/network blocker occurred.

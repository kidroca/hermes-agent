# Approval display context and exact Discord peer settlement

- Date: 2026-10-15 (Europe/Sofia); clock-tool snapshot: 2026-10-15 04:53:28 UTC. Upstream reads followed within this session.
- Exact sourceSHA: `977d4a420c44fb8bd97679c1004c769be93d9387`; detached checkout HEAD independently verified equal. No ref substitution or branch-tip inference.
- Commit: `fix(approvals): 🛠️ Bind exact display context and retire settled Discord peers`; author/committer recorded by Git as `🤖 hermes / gpt-6.1-sol <ubuntu@kidroca.com>`. Parent reports source-patch author names/emails verified; no authorship rewrite performed.
- Status: committed, approved local patch; this report is a docs-only side channel for parent review/copy and separate commit. It is not an upstream submission, activation receipt or live-ready claim.

## Contract verified from the committed diff

The motivation is exact entry-bound owner/session/profile public approval display without routing-key or FIFO guessing, plus retiring the exact Discord peer view when the host settles so a later local view timer cannot claim nothing happened.

`tools/approval_display.py` captures optional public durable session ID, profile and session title. Matching task-local approval/session/routing bindings are required; profile/title lookup additionally requires the explicitly bound runtime home and the owning worker’s exact-ID public title getter. Identity fields fail closed; fields are bounded, reasoning-tag guarded and force-redacted. No conversation, provider messages, system prompt or cwd is projected. `_ApprovalEntry` discards caller-supplied display context, captures its own snapshot and copies it for notification. Display context grants no authority and is not a routing key. This commit supplies the snapshot contract; it does not establish that every consuming UI displays it. Separate public-response source work is outside this report.

Discord owns a `(session_key, request_id)` view map. The host’s existing single settlement callback retires the exact view; controls are disabled, stopped and detached before message editing. Missing registration and local view timeout mean unknown outcome, never inferred command execution. A committed choice wins the deadline race unless interrupted. Late ambiguous-send acknowledgement preserves owner scope, retires stale cards and does not resend. Failed sends and disconnect clean up controls. Locally accepted labels survive later timer callbacks. Generic Discord prompts retain their existing lifecycle.

The inspected commit changes 17 files (+700/-74), including implementation, locale text, documentation and regression tests. This catalog task changes none of those originals.

## Tests and limits

Parent-provided evidence, not rerun or independently re-certified by this documentation task:

- Parent core177 tests **PASS**.
- Independent source review **APPROVE**, identified by parent as `core-takeover-01/REVIEW-FINAL.md`; that artifact was not located/read in this checkout during the bounded pass.
- Coupled project commit `c5e8e0e`: Windows publish/domain191 **PASS**. This is a separate coupled-project receipt, not the Hermes sourceSHA or proof of live activation.
- Fresh GUI verification was blocked before launch; **no activation** occurred.

Committed tests inspected include display-context isolation/redaction and exact peer retirement, send/settlement races, edit failure, failed-send cleanup and accepted-choice/timer behavior. Their presence is source evidence, not a fresh passing test run. No full-suite, live Discord, fresh GUI, runtime/account or deployment verification is claimed. This task verified only the docs delta with `git diff --check` and scope/status checks.

## Bounded upstream intelligence

Four authenticated read-only `gh search` queries, each limited to 12 results, against `NousResearch/hermes-agent`:

```text
issues: "approval" "Discord"
prs:    "approval" "Discord"
prs:    "approval" "session"
issues: "approval" "timeout"
```

The initial sandbox network attempt failed; the same searches succeeded with network permission and existing gh authentication. No auth/login/install or credential read was performed. Three material direct followups: PR #104960, PR #137574, issue #8896. The #104960 read was retried after removing an unsupported JSON field. These are bounded relevance searches, not an exhaustive inventory or proof of absence of a replacement. No upstream diff execution or independent upstream test run was performed.

| Item / author | Snapshot date/state | Maintainer signal | Overlap / conflict | Merge likelihood |
|---|---|---|---|---|
| [PR #104960](https://github.com/NousResearch/hermes-agent/pull/104960), liuhao1024 | Created 2026-09-07; updated 2026-09-07 16:25:41Z; OPEN, mergedAt null | Fetched reviews by andrexibiza are COMMENTED with association NONE; no fetched maintainer approval. Author describes extraction followup; review discusses a bounded Discord owner and earlier green hosted checks, which are dated claims for earlier heads. | High conflict with runner/Discord request transport and owner extraction. Exact-ID lineage overlaps the prerequisite patch; does not establish public display snapshots or all-outcome host retirement equivalence. | Unknown. Open state and technical review are not a merge commitment; no fresh CI validation here. |
| [PR #137574](https://github.com/NousResearch/hermes-agent/pull/137574), liuhao1024 | Created 2026-10-13; updated 2026-10-13 04:05:23Z; OPEN, mergedAt null; mergeable UNKNOWN | No reviews; only fetched author comment, association NONE. No maintainer endorsement fetched. | Approval-hook session identity is adjacent, with conceptual conflict: contextvar → session environment fallback differs from this display path’s stricter matching bound identities. Files include `tools/approval_context.py`, plugin hook docs and tests; not a Discord lifecycle replacement. | Unknown; author-reported tests are not independent landing evidence. |
| [Issue #8896](https://github.com/NousResearch/hermes-agent/issues/8896), Dille68 (Oskari Koskinen) | Created 2026-04-13; updated 2026-09-12 02:09:40Z; OPEN | Corroborating report by liuchuangqi, association NONE; no fetched maintainer signal | Strong lifecycle-family overlap: stale actionable cards and timeout notification plumbing, focused on Feishu/Telegram. Its suggested expired/not-executed text must not be applied to an unknown Discord peer outcome. No implementation supplied by the issue. | N/A for issue; implementation/merge prospects unknown. |

Search-only signals, not directly reviewed: [#104915](https://github.com/NousResearch/hermes-agent/issues/104915) (sake303, open, updated 2026-09-27) corroborates the exact-request prerequisite; [#138511](https://github.com/NousResearch/hermes-agent/pull/138511) (HopeValentine, open, updated 2026-10-14) concerns approval reason truncation, so may touch rendering but is not replacement evidence; [#137641](https://github.com/NousResearch/hermes-agent/pull/137641) (ytahml, open, updated 2026-10-13) concerns desktop replay/rebind and could affect the coupled consumer. [#130272](https://github.com/NousResearch/hermes-agent/issues/130272) (schuerstedt, open, updated 2026-10-01) and [#136595](https://github.com/NousResearch/hermes-agent/issues/136595) (lingxinsuixing, open, updated 2026-10-11) concern denial-versus-timeout reporting. Maintainer signals and merge likelihood for these search-only items are unknown; titles alone do not establish behavior.

The [October 14 exact-request report](2026-10-14-2c44a104eb-discord-exact-approval.md) is historical context for #125039/#87554 and prior conflict/mergeability readings. Those items were not directly refreshed here; do not promote yesterday’s state into a current claim.

## Patch family and clean replacement conditions

The explicit local prerequisite is exact Discord request binding `21fbc45964e99d86f6dac9bef0efc56124b2cd5e` (original reviewed lineage `2c44a104ebf618d8b9fb9fb865945a482a2cfd33`). This commit extends that carrier; it must not restore missing-ID FIFO fallback. It also relies on the existing authoritative approval queue, host settlement registration, task-local session/profile binding, redaction and worker ownership. The coupled project `c5e8e0e` consumes related behavior separately; it is not bundled into the Hermes commit. The neighboring CLI memory-cwd and Hindsight checkout-hygiene patches are not demonstrated semantic dependencies.

Keep the local family until an actually landed upstream implementation replaces all relevant contracts:

1. Entry-created, immutable public display snapshots tied to the exact durable session and owning profile/title getter; bounded/redacted omission on missing or inconsistent ownership, with no ambient fallback or routing/FIFO inference.
2. Exact request identity through producer, native renderer and resolver; stale/missing IDs resolve zero, while typed text retains its intentional semantics and admission/admin gates remain intact.
3. Host-owned all-outcome retirement of the exact Discord peer, closing controls before I/O, preserving accepted labels, cleaning failed/disconnected sends and handling late ambiguous acknowledgements without duplicate sends or lost profile scope.
4. Honest distinction between authoritative timeout, settlement elsewhere and unknown outcome; neither a local timer nor missing registration asserts execution or nonexecution.
5. Composed behavior regressions on the integrated upstream replacement, plus validation of the coupled consumer’s snapshot/rebind contract. Reconcile module moves and request-ID ABI before removing local hunks.

An upstream request-ID field, timeout footer, hook identity fallback or owner extraction alone is insufficient. Conflict risk is high in runner/Discord ownership; merge likelihood remains unknown. Dropping this patch and its prerequisite should follow demonstrated contract equivalence, not PR titles or publication/GUI assumptions.

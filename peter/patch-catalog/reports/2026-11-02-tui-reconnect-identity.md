# Preserve the mounted TUI conversation across transport replacement

- Date: 2026-11-02
- Repo: `/opt/hermes-agent`; isolated candidate `/tmp/hermes-tui-reconnect`
- Patch ref: `95a6b63c9804630501d96642d304279c4a11dd0c`
- Base: `bfd0cf7b9831f8f9703b73add59d70fc7f7f307d`
- Branch: `peter/tui-reconnect-candidate`
- Local status: reviewed and committed candidate only. Not integrated into
  `peter/hermes-patches`, deployed, restarted, pushed, or submitted upstream.
- Motivation: several open TUIs blanked together after heartbeat stalls. A poll
  could replace a closing socket before its close callback notified recovery;
  readiness then allocated a fresh conversation instead of reopening the mounted one.
- Changed files: `ui-tui/src/gatewayClient.ts` and
  `ui-tui/src/app/createGatewayEventHandler.ts` (19 production additions,
  10 deletions); new 242-line `ui-tui/src/__tests__/gatewayReconnectSession.test.ts`;
  startup-image fixture correction in `ui-tui/src/__tests__/canonicalStartupImage.test.ts`.

## Local patch summary

Heartbeat failure and RPC replacement of a closing/closed socket now retire the
transport through the existing exit/reconnect path before replacement. Socket
identity is cleared before close, so a delayed close cannot report a second exit
or discard the replacement socket. On ready, recovery falls back to the mounted
durable conversation ID when no exit notification populated the recovery ref.
Recovery does not resend the startup prompt or create a replacement conversation.

The startup-image fixture now begins without a session and establishes its ID
through explicit startup resume; its previous pre-seeded ID described a reconnect
rather than first launch. No backend, database, wire-contract or dependency change.
The candidate depends on the existing durable `storedSid` tracking, socket identity
guards and attachment lifecycle already present at its base, including the older
upstream reconnect correction.

## Tests / verification

Parent-executed receipts on the isolated candidate:

- Original two production files restored for deterministic A/B: 14 failures and
  4 passes among the 18 new integration cases; candidate restored: 18/18 passed.
- Both legacy and canonical protocols: delayed/missing/synchronous close,
  concurrent polls, already-closing transport, ordinary close, missed exit,
  disconnect during resume, and delayed/missing close with no polling. Assertions
  preserve conversation ID and transcript, prohibit session creation and prompt
  replay, and check exactly-once exit/replacement behavior.
- Full TUI Vitest suite: 241 files; 1,898 passed, 2 skipped. Suite exited 0;
  stderr included a Python `ruamel` import warning on an optional subprocess
  fallback. The copied stale Ink bundle was rebuilt before the final run, and
  subprocess checks were rerun with sandbox escalation after an initial EPERM.
- Typecheck, lint for touched files, production TUI build, and all 12
  `scripts/check --base bfd0cf7b9831f8f9703b73add59d70fc7f7f307d` gates passed;
  no code-health findings.
- Independent pre-commit source review approved the final snapshot; committed
  source/test bytes match that reviewed snapshot. Reviewer did not independently
  rerun the parent's test commands.
- Parent-built entry: `/tmp/hermes-tui-reconnect/ui-tui/dist/entry.js`, 4,105,741
  bytes; SHA-256
  `5905bcbce4652ad0acbd0886c559458f6c1744259313372bce62a7e825e57d85`.

The new tests combine the real gateway client, ready handler and mounted session
lifecycle hook with fake sockets and a substitute exit subscriber. They verify
transcript state, not terminal paint or a live end-to-end gateway interruption.
No active user connection was disconnected for verification.

## Upstream overlap

Known-item metadata and discussion were read through authenticated GitHub API on
2026-11-02. Parent inspected exact upstream source at
`d9397d7b559f75e60395af4e5f1a1f593ee8358c` (commit time
2026-11-02T15:31:32Z): old heartbeat-close, CLOSING replacement and ready-recovery
logic remain there.

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| Issue | [111594](https://github.com/NousResearch/hermes-agent/issues/111594) | Attached TUI loses recovery events and resumes with the wrong session ID after WebSocket reconnect | Opened 2026-09-15; closed 2026-09-16 | `gustavosmendes` (parent-read issue) | Closed by merged #112227 | n/a | Related earlier lifecycle defect | Already addressed by #112227; residual race remains |
| Merged PR | [112227](https://github.com/NousResearch/hermes-agent/pull/112227) | Attached TUI reconnects and reopens the same session after a socket drop | Opened 2026-09-15, 48 days before check | `teknium1`, `COLLABORATOR` | Merged 2026-09-16T01:53:06Z; no formal reviews returned | 12 files, +273/-39 | Same hot paths; older correction already in candidate base | Merged |
| Open PR | [114188](https://github.com/NousResearch/hermes-agent/pull/114188) | Run transport exit path directly on heartbeat silent drop | Opened 2026-09-17, 46 days before check; last update 2026-09-17T15:44:08Z | `Melnislav`, association `NONE`; prior merged PR history not checked | No formal reviews returned; one supportive non-maintainer comment | 2 files, +81/-3 | High semantic/direct heartbeat overlap | Unknown; no verified maintainer endorsement |

## Notes on most relevant upstream items

#112227 merged as `5a4c3b32d0cb32be851df01c374399b90df801d7`, salvaging
#111599 and closing #111594. Its body explicitly retained RPC-triggered immediate
reconnect rather than refusing requests during backoff. The installed/base code
already has its event delivery and durable-ID improvements, so that merged fix
alone does not remove this race.

#114188 is relevant prior art: it invalidates the heartbeat-failed socket and calls
`handleTransportExit` directly, testing a close event that never arrives. The local
candidate adapts that principle to existing `closeGatewaySocket`, also retires
RPC-discovered closing/closed sockets, and protects ready-time session identity.
The PR is open and `merged_at` is null. Its only issue comment returned by the API
is a supportive Hermes-generated review from `okyssta` (association `NONE`), not a
maintainer approval. Empty formal-review results do not explain why it remains open.

## Recommendation

Keep this as a candidate until Peter approves live source integration and activation.
Review the tested candidate before deployment; publication is a separate permission.
This is a TUI-only change: integration and rebuilding live `ui-tui/dist` require
separate approval. Already-running Node TUIs retain old code and must be reopened
and resumed to load the fix. A gateway restart is not inherently required.
When adopting upstream changes, compare behavior rather than titles: drop local
hunks only after upstream preserves the same mounted identity under delayed/missing
close, concurrent polling, and interrupted resume without prompt replay. Expect
manual reconciliation if #114188 or another gateway-client lifecycle rewrite lands.

The cause of the initial simultaneous heartbeat stalls remains unproven. Footer
count semantics and historical empty-session cleanup are separate deferred work;
this patch does not alter them or delete history. An inherited limitation remains:
`resumeById` catches some resume failures and resolves, so the existing nonempty-ID
check can clear the recovery ref without successful resume. The new current-state
fallback preserves the target on a later ready; broader resume-result semantics
were not changed.

## Raw search queries used

Parent's bounded upstream discovery, before implementation:

- `repo:NousResearch/hermes-agent is:pr reconnect tui`
- `repo:NousResearch/hermes-agent heartbeat blank`
- `repo:NousResearch/hermes-agent "CLOSING"`
- `repo:NousResearch/hermes-agent "blank" "session" is:open`

Catalogue follow-up read only known #112227/#114188 PR metadata and formal reviews,
plus #114188 issue comments. No broad follow-up searches or public writes.

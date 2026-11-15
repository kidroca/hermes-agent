# November 15 upstream reconciliation

- Date: 2026-11-15
- Candidate branch: `update/hermes-patches-20261115`
- Reviewed source snapshot: `80f822bf97e2021e15d5bd250eaa9e055812fe90`
- Old live tip: `8bac3a7fde9378a009bc72c4a307b37c95f91fb4`
- Fetched fork source / publication lease: `5e367d534b88d2463c8d961c36893af132c9aca1`
- Recovery ref: `recovery/hermes-update-20261115` at the fetched fork source.
- Old upstream base: `8ad89d45ac6a5da0c6b2cc641bcc12aa41ceb89b`
- New frozen upstream base: `ce4de3cdc2a99276affd2ec12b3adde8f39636ab`
- Active retained patch refs: `acdb2b3e3b` + `f045e667b8` + `113e40dad4` + `40a814d7ff` + `43b68dd82a` + `3749b84b53` + `67eb1d7661` + `d52f4fa711` + `e20ebd57ff` + `fe809a042c` + `078fdce7ba` + `0ccb499852` + `ddabcdc8ef` + `a9dda1b8ff` + `a83f849157` + `fc22c3d4e5` + `de330b0b18` + `21b83877a5` + `7c232e9303` + `d6d1ec1717` + `9f3bed3977` + `9e3b76c32e` + `f6febd69a7` + `68974a1d79` + `331a6741dc` + `bee6161b04` + `db437d79b4`.
- Scope: isolated candidate, verification and authorized guarded fork publication. Live checkout, venv, configuration, gateway and TUI activation remain untouched.
- Publication contract: authorized fork publication with explicit lease against the fetched source above, after all gates; the remote receipt belongs to the final handoff. This document alone is not proof of live activation.

## Impact review

The fork was three commits ahead of the live checkout; the candidate starts from that fetched tip and includes the other machine's early Slack selection patch. No unpublished local work was found.

Upstream changes 5,200 files (+240,038/-21,070); 1,396 catalogue and 662 contributor paths are counted separately from runtime changes. Raw counts did not trigger an approval requirement under skill 1.0.5. Unified ScopeState, durable delegation, approval actor ownership, browser profile isolation, SSH socket hardening and Slack workspace provenance received focused inspection. No removed configured provider, irreversible migration or contract retirement was found. Installed default/clerk/coding/designer/lad-studio/lawyer profiles use openai-codex and an external Hindsight plugin; the memory initialization helper is unchanged. No live config migration is required for the retained contracts inspected.

## Retained and adapted lineage

| Family | Previous refs → active refs | Decision |
|---|---|---|
| Portable file-only SSH uploads | `1555676d42` + `4fbb938355` + `029248e5e5` + `f536742a3e` + `fd80617053` → `acdb2b3e3b` + `f045e667b8` + `113e40dad4` + `40a814d7ff` + `43b68dd82a` | Retain |
| On-demand configured CDP launch | `bb1ab2ed2b` + `8b96c493a8` + `50e2d41660` → `3749b84b53` + `67eb1d7661` + `d52f4fa711` | Retain |
| TUI missing database handle recovery | `7eeca3e0ec` → `e20ebd57ff` | Retain |
| External-CDP activity leases | `c632658063` + `837340e9be` + `996bbd5d09` + `266cdb4f9e` → `fe809a042c` + `078fdce7ba` + `0ccb499852` + `ddabcdc8ef` | Adapt; preserve upstream scope/authorization |
| Canonical ancestry advisory | `ad345d8639` → `a9dda1b8ff` | Retain |
| External-memory structured notice bridge | `deec5144f1` + `f26abe24ec` → `a83f849157` + `fc22c3d4e5` | Retain |
| Doctor retirement documentation | `8318e5a98b` → `de330b0b18` | Retain |
| Hindsight checkout hygiene | `1d0b48f427` + `f07904a942` → `21b83877a5` + `7c232e9303` | Retain |
| Implicit CLI memory workspace | `680d8ffb8e` → `d6d1ec1717` | Retain |
| Exact approval public display context | `f62342fac0` → `9f3bed3977` | Adapt; preserve upstream scope/authorization |
| Linux ownership across clock steps | `0a6c1731b7` → `9e3b76c32e` | Retain |
| Acknowledged SSH sync progress | `f8c5506019` → `f6febd69a7` | Retain |
| ACP explicit editor close | `8c61935a29` → `68974a1d79` | Retain |
| Gated cron ghost-session lifecycle | `d3ef5ff94b` → `331a6741dc` | Retain |
| Mounted TUI conversation on reconnect | `3ca6298238` → `bee6161b04` | Retain |
| Profile-bound early Slack plugin selection | `9c43814849` → `db437d79b4` | Adapt; preserve upstream scope/authorization |

All 59 source-stack commits were replayed; no dropped entries or unexplained new patches. Range-diff has six changed mappings: portable SSH imports, POSIX SSH helper placement, browser lease wrapper, approval display context, Linux session-identity import context, and Slack early selection. Other mappings preserve patch identity.

## Conflict resolution and behavioral evidence

- SSH: union the remote POSIX archive helper with upstream owned/short ControlMaster directory handling. Retain portable file-only archives, pre-write path validation and acknowledged sync checkpoints.
- Browser: keep upstream hosted-tool refusal and a single URL verdict before activity leases. Profile-bound daemon/routing/redaction behavior stays inside the lease wrapper.
- Approvals: retain upstream owner, command identity, deny-only cards and mixed-sender actor handling. The public bound-value getter uses upstream `_bound_session_value`; it never falls back to process environment.
- Slack: combine admission, socket lifecycle and vault mixins. Move authenticated install resolution and foreign-DM refusal ahead of strict selection; retain upstream forwarded content, sender bot provenance and MPIM session flags. Trusted reaction bypass stays a caller keyword, not raw event metadata.
- Adapt upstream Slack test fixtures to the four-value prefilter result and trusted reaction keyword, preserving their actual authorization/dedup assertions.
- Verification exposed cold plugin discovery on the event loop. A deterministic Event-based regression was red before correction; offload `_delivery_manager` with `asyncio.to_thread`, carrying copied profile context. Keep callbacks and their timeout semantics in the selection task. The new regression, early-selection, Connect and unchanged watermark timing tests pass together (69 tests). No timing threshold was weakened.
- Linux identity, memory notice/cwd, cron ghost rows, ACP close and reconnect patches remain retained without contract retirement.

## Verification

Final canonical affected-area run on immutable source: **113 files, 2,077 passed, 0 failed, 25 skipped** (72.2 seconds, four workers). It covers all selected Slack, approval, SSH, browser, Linux ownership, memory, cron, ACP and database-recovery paths. Initial 12-file pass: 280 passed / 22 skipped. Initial broad pass exposed the corrected Slack fixture drift, missing optional ACP dependency (provisioned through PM in a separate test environment) and the discovery stall above. Those failed receipts are not claimed green.

TUI: 259 files / 2,011 tests passed in the first run; two cold-pending renderer tests were denied child-process creation by the sandbox and both passed outside it. Combined coverage: 260 files, 2,013 passed / 2 skipped. TUI typecheck/build/lint pass (lint has 13 existing warnings, zero errors). Shared TypeScript transport: 23 files / 222 tests pass, typecheck and lint pass (13 existing warnings).

Initial canonical `scripts/check --base ce4de3cdc2`: all 19 checks passed. Independent exact-source review of `80f822bf97e2021e15d5bd250eaa9e055812fe90` found no blockers, including the discovery fix and inherited risky mappings. Final canonical repository checks: **19/19 pass**, zero blocking/advisory code-health findings; plugin-boundary lint and whitespace checks pass. Independent catalogue review found no blockers and verified all 27 active refs and all 59 mappings. No repository-wide Python suite, live messaging canary, live update or doctor execution is claimed.

## What's new for Peter

- Durable resumable subagents and follow-ups; automatic resume is opt-in.
- Discord long replies become Markdown attachments; live allowlist reload and browser-vault code modal.
- Slack workspace/Connect and bot-provenance fixes, intentional-silence behavior and off-loop storage work.
- Desktop remote/profile routing and bot-creation reliability fixes; TUI setup routing fixes.
- Cron per-job wrapper control, timezone reporting and opt-in fresh Telegram topics per run.
- MCP result deduplication/OAuth callback fixes, profile-bound browser/terminal isolation and stronger skill scanning.
- Claude subscription access is a separate official experimental plugin; remind Peter to install `claude-subscription-directsdk` after updating, log into Claude CLI and select it with `hermes model`. No plugin was installed here.

## Source lineage appendix

| Previous commit | Replayed commit |
|---|---|
| `1555676d42` | `acdb2b3e3b` |
| `bb1ab2ed2b` | `3749b84b53` |
| `7eeca3e0ec` | `e20ebd57ff` |
| `bd78db4411` | `23ca366215` |
| `2f800af067` | `26329fe614` |
| `8b96c493a8` | `67eb1d7661` |
| `24ea100e53` | `3778313fa1` |
| `50e2d41660` | `d52f4fa711` |
| `ef90e2fbf9` | `21f0cab127` |
| `b6ea4bfc3b` | `01c0d3f1c0` |
| `4fbb938355` | `f045e667b8` |
| `ee2fdfa88f` | `b53dbced05` |
| `029248e5e5` | `113e40dad4` |
| `f536742a3e` | `40a814d7ff` |
| `fd80617053` | `43b68dd82a` |
| `389f847125` | `60bc5b91b9` |
| `b51a512f8b` | `2b426a755f` |
| `826b91a4aa` | `3237584238` |
| `c632658063` | `fe809a042c` |
| `837340e9be` | `078fdce7ba` |
| `996bbd5d09` | `0ccb499852` |
| `266cdb4f9e` | `ddabcdc8ef` |
| `471555cda7` | `e270eeb12c` |
| `ad345d8639` | `a9dda1b8ff` |
| `deec5144f1` | `a83f849157` |
| `8318e5a98b` | `de330b0b18` |
| `d8ea71b699` | `1dd4fc6bdc` |
| `f26abe24ec` | `fc22c3d4e5` |
| `319ae830c4` | `214af8966a` |
| `5168add12b` | `175c9e3ae5` |
| `1d0b48f427` | `21b83877a5` |
| `ceae45b2c1` | `8d6c8ee8f7` |
| `f07904a942` | `7c232e9303` |
| `fec0a4baf6` | `5f2e68ec0b` |
| `680d8ffb8e` | `d6d1ec1717` |
| `436ed4da0d` | `2725b1127d` |
| `f62342fac0` | `9f3bed3977` |
| `9080c85c6d` | `440a44edc2` |
| `f42d15074f` | `6646fa3f7a` |
| `0a6c1731b7` | `9e3b76c32e` |
| `75f6b72f15` | `213d39170b` |
| `72191ec0c8` | `a2bb66db45` |
| `1b89469cec` | `bceeda3a62` |
| `f8c5506019` | `f6febd69a7` |
| `3bc37fd049` | `1dd8d40c13` |
| `8c61935a29` | `68974a1d79` |
| `3b62576745` | `27a42fce49` |
| `369ebdb409` | `a6899ac737` |
| `4c18f5b52b` | `028d2fa41e` |
| `d3ef5ff94b` | `331a6741dc` |
| `cb705ed651` | `601b005e65` |
| `929aa6461a` | `df1adce27b` |
| `3ca6298238` | `bee6161b04` |
| `5539eb7d55` | `f89b93dae1` |
| `370cf2cc67` | `f9207e89c9` |
| `8bac3a7fde` | `bfa5df5cdc` |
| `9c43814849` | `db437d79b4` |
| `e32c08a919` | `5f56287fc9` |
| `5e367d534b` | `80f822bf97` |

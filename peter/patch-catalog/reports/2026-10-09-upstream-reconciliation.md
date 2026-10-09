# 2026-10-09 upstream reconciliation

- Date: 2026-10-09
- Frozen functional candidate: `d0b83817789a4e94b492226da9c9adea9b305bbc`
- Upstream base: `8bff64d6ed3414a66976bfa8ab72c14b6bca2a6f`
- Old base: `09581cacaa8db3b3241dbbabe76a351a2ce14f60`
- Old fork tip / explicit publication lease: `ff2a9e0feae1d0223da92c1498c108d1832318eb`
- Recovery: `recovery/hermes-update-remote-pre-rebase-20261009T083851Z`
- Candidate branch: `update/hermes-patches-20261009T083851Z`
- Active core refs: `09569c8c85`, `a1203b14d2`, `73a84f541c`, `8560536e20`, `5bf03f258b`, `3b3a308c24`, `9bfa349f24`, `fc63477679`, `91a85444cf`, `1a89ad0e21`, `d0b8381778`, `bec721897b`, `8fa25cabad`, `c1d013b116`, `cb13b13673`, `dfe271189a`, `d5b03ba057`, `0b42ce86dd`, `47b433357f`, `6fa1948ec7`, `13eda3a05e`, `19e407ef29`, `5e3107cbca`, `4d70117e69`, `3ec89c64a8`
- Scope: isolated preparation and guarded fork publication; this receipt does not claim live installation, restart, config migration or live provider verification.

## Decisions and behavioral preservation

All 34 previous commits remain; five review-approved small verification fixups were folded into their owning patches. One explicit new ACP resource-lifecycle correction is retained separately. No functional family was dropped or policy-retired in this update. Previously retired Doctor, workspace-routing, recall/provenance/display policies stay retired. Historical catalogue tables and reports are not replay instructions.

- **SSH retained:** pre-write validation, literal NUL file manifests, POSIX remote paths, Windows staging containment and portable file-only extraction remain local. Upstream optional `sync_files=False` construction stays intact.
- **ACP retained/adapted:** modern upstream typing and disconnect recovery compose with explicit close/history preservation, worker drain and runtime retirement. Independent review found three reproducible gaps: close could tombstone a successful concurrent reload; detached background children survived close; model replacement lost process-owner IDs. All three new behavioral regressions failed before correction. `d0b8381778` serializes final close publication with the existing restore gate, signals detached children for stable/original/final session IDs after drain, and transfers process owners before replacement publication. Persisted jobs and sibling sessions remain excluded from cleanup.
- **CDP retained/adapted:** bounded configured launch, endpoint-canonical locking, stale-discovery invalidation and external-browser activity leases remain. Upstream harness cleanup and retargeting stay intact. All stale resolver test doubles accept the new keyword arguments without changing assertions. The mode-specific status fixture now acknowledges upstream `browser_use`; it retains forbidden-I/O checks. Optional lease-config failures now log debug diagnostics rather than swallowing exceptions invisibly.
- **Memory retained notice-only:** `_memory_provider_init_kwargs` and the pure `_aux` config factory move into sibling modules to satisfy upstream facade-size ratchets. Late owner reads preserve existing profile and monkeypatch seams. No new memory workspace/routing semantics, config key, default or model switch was added. Upstream mandatory secret scrubbing before external-memory egress remains intact. The separately versioned Hindsight deployment and source pin are unchanged.
- **Canonical ancestry retained:** advisory banner and environment/full-status rendering stay separate from installable fork update selection. Upstream's new summary status intentionally omits environment details: use `hermes status --full` to see Source ancestry. No extra network/fetch or update-cache ownership was introduced.
- **TUI DB recovery retained:** missing agent session handles are attached after final synchronization while preserving upstream admission leases, close boundaries, profile scoping and turn settlement.
- **Historical receipts:** old scratch-path references receive explicit provenance annotations to satisfy upstream no-scratch-path lint; original historical evidence is preserved, not rewritten into current instructions.

## Verification and review

Canonical verification uses the disposable candidate environment, isolated HOME, and `scripts/run_tests.sh` with fresh per-file subprocesses. No install/test/dependency operation targeted the live checkout or user state.

- Initial affected-area gate: **70 files, 938 passed, 0 failed, 21 skipped**.
- After ACP corrections: **34 files, 234 passed, 0 failed, 1 Windows skip**; all three new regressions were proven RED before the fix and GREEN afterward.
- Duplicate/shadowed test-definition guard: **5 passed**.
- TUI: **178 test files, 1,623 passed, 2 skipped**; shared typecheck and TUI Ink/build/typecheck passed. Direct ESLint: **0 errors, 2 upstream warnings**.
- Upstream pinned `scripts/check`: **11 checks passed**, including code-health/facade ratchets. No thresholds or waiver policy weakened.
- Independent reviews: old/rebased range mapping verified all 34 patches; full production packet review found no additional blockers; exact helper/fixture tree `ace962119b` approved; exact ACP corrective tree `e7a11057f4` approved after reproductions.
- Refresh from `5f045f842a` to `8bff64d6ed`: 13 upstream commits, 38 changed paths. Mechanical comparison proves the final functional tree differs from reviewed `e7a11057f4` only in those upstream paths; the later refresh includes upstream memory-spill policy/default changes, applies without new conflicts, and preserves the reviewed notice-only bridge and extracted helpers.

Final refreshed receipts: **71 files, 946 passed, 0 failed, 21 skipped** on `c830865b0a` (functional head `d0b8381778` plus the rebased documentation receipt); the eight refresh/guard files separately pass **93 tests, 0 failed, 2 skipped**. Shared/TUI typechecks and the Desktop pet-SDK file also passed (**11 tests**). Earlier intermediate receipt `7a7a074d87` had 941 passes; it is not the final source candidate. Mechanical catalogue validation: **8 active rows, 25 distinct active ancestor refs, 137 resolving local links**, complete **34 previous → 35 functional** commit coverage with no mapping gaps. These receipts are separate, not a claimed unique-test sum. This is bounded changed-area verification, not a repository-wide suite or native Windows/macOS live validation. Native Sol compaction was source/test inspected, not live provider exercised. npm's upstream lockfile audit reported **43 vulnerabilities (9 low, 11 moderate, 19 high, 4 critical)**; no `npm audit fix` or unrelated dependency rewrite was attempted.

## Important upstream changes

Source-backed radar is against the actual delta, not merely commit titles.

- Sol 900K picker (`5bb6127c5b`): opt-in large local context budget, preserves actual provider slug. Does **not** enable native compaction; live catalog caps and replay costs still apply.
- TUI/Desktop model-switch confirmations (`20cb63df9e`, `9927e3cd06`) happen before deferred switching; saved browser-login and verification-code dialogs repaired (`a8d7bc3ea1`, `5c975b9ed8`). Browser-use switching reaches these surfaces (`5654863ccd`).
- Desktop local profile backends no longer idle-reaped (`167e9fdb84`), keeping unattended bot/cron work alive under existing slot caps.
- Discord rechecks revoked users on approval buttons and preserves actor role grants (`502df01d54`, `39f0da8b2f`); Slack slash commands obey channel restrictions and acknowledge blocked channels honestly (`b376591778`, `0089fca37d`).
- Cron uses progress/silence rather than total runtime for stale reclamation (`ed2dd0b35c`), and visibly degrades/reprobes unwritable stores (`759b1c34ad`, `81b12a3bab`, `91fc7badaf`). Restarting during an outage loses the exceptional late-one-shot recovery window. Restart-safe scope enforcement is an independent opt-in.
- MCP image results deliver native vision pixels (`6da034a60d`); OAuth stops inventing unsupported registration endpoints (`7dab93b06e`). Explicit empty cron toolsets fail closed (`b4969d8e2d`).
- Memory-provider egress always scrubs secrets (`88704223d2`) even with local-output redaction disabled. Credential-upload/invisible Unicode approval detection and unattended-sudo handling improve (`68dd992769`, `33c9b1d779`). Bundled Tirith is removed (`911da42e9e`); built-in approval checks remain, no external scanner is automatically enabled.
- External mounted skills are honestly marked external and protected from learned-skill curator ownership (`c13232e90c`), not made read-only for foreground edits.
- Voice: opt-in `stt.streaming: true` (`00adf69d92`) on supported cloud providers, with recorded fallback; independent `auxiliary.voice_chat.*` model (`6cc1efd8f9`), voice reasoning defaults off/lowest accepted. Local Whisper keeps the file path.
- Final refresh: browser captured dispatch is fenced and late replies retained (`aad11beae0`); indefinite captured waits end when supervisor closes (`66e0cee526`); failed TTS does not delete an existing output (`7085fbf775`); memory provider discovery scans beyond 8KB and failed auto-installs stop repeating (`a114e7a344`, `6a2909c6b1`); process scans ignore other Unix users' gateways (`99b57a42c7`).
- Final two upstream commits (`2327290b0d`, `8bff64d6ed`) make external-memory prefetch spilling opt-in (`memory.prefetch_spill_enabled: false`) while preserving a runaway-recall ceiling. Provider-ranked recall stays whole within that ceiling; this does not enable automatic recall. Configuration is snapshotted at provider registration.

## Native Codex compaction for Sol

**Not eligible in the normal Hermes `openai-codex` loop.** `agent/native_compaction.py` gates native Responses `context_management` to the gpt-5.6 family, or Astra on an official Codex OAuth endpoint. Sol and its 900K alias remain excluded even with `compression.codex_responses_native: true` or trusted-proxy capability. Default opt-in is false. No standalone `/responses/compact` client call is implemented. The feature and Astra eligibility predate this update.

Sol continues using Hermes tool pruning/auxiliary summary compression. The separate opt-in `model.openai_runtime: codex_app_server` has `thread/compact/start`, with `compression.codex_app_server_auto: native|hermes|off`; this changes tools/sandbox/execution ownership and is not a compression-only toggle. Sol-specific live backend success was not tested and no runtime/config change was made.

Evidence: `agent/native_compaction.py`, `agent/chat_completion_helpers.py`, `agent/transports/codex_app_server_session.py`, `tests/agent/test_native_compaction.py`, `tests/agent/test_astra_oauth_native_compaction.py`, `tests/agent/test_codex_app_server_compaction.py`, and [context-compression documentation](../../../website/docs/developer-guide/context-compression-and-caching.md).

## Exact retained ledger

| Previous fork ref | Final active ref | Subject |
|---|---|---|
| `8a95378f3d` | `09569c8c85` | fix(ssh): 🐛 Preserve portable file-only bulk uploads |
| `de0cffd125` | `cb13b13673` | feat(browser): 🚀 Launch configured CDP endpoints on demand |
| `68e5fe88ad` | `0b42ce86dd` | fix(tui): 🐛 Recover missing session database handles |
| `e2768e778b` | `4d70117e69` | docs(patches): 📝 Document diagnostics and CDP launch |
| `27724944be` | `42fab389cc` | docs(patches): 📝 Reconcile the post-monster patch stack |
| `57c5226407` | `dfe271189a` | fix(browser): 🐛 Scope CDP launch locks by endpoint |
| `7b008056f5` | `f50462c192` | docs(patches): 📝 Record independent review corrections |
| `5d83c0571a` | `d5b03ba057` | fix(browser): 🐛 Canonicalize CDP launch lock identities |
| `e5fcf43eb8` | `57f3224e22` | docs(patches): 📝 Record second review corrections |
| `0b0ca22a0b` | `cc8dc5c908` | docs(patches): 📝 Record clean final review |
| `523ac0608f` | `a1203b14d2` | fix(ssh): 🐛 Use POSIX paths for remote archives |
| `fbeeccb468` | `b95853aa6b` | docs(patches): 📝 Catalogue portability follow-ups |
| `1858f6ae23` | `73a84f541c` | fix(ssh): 🐛 Contain Windows archive staging paths |
| `8cd0a657b0` | `8560536e20` | fix(ssh): 🐛 Reject unrepresentable Windows archive names |
| `35a450380c` | `5bf03f258b` | fix(ssh): 🐛 Validate upload paths before remote writes |
| `93c6e2bf89` | `33a3bb10f0` | docs(patches): 📝 Record final portability review |
| `2a18d75ff1` | `3307f81160` | docs(patches): 📝 Reconcile September 22 active catalogue lineage |
| `f03dd3eed0` | `bb274bae12` | docs(patches): 📝 Record verified update candidate |
| `0849b72862` | `47b433357f` | feat(browser/cdp): 🕰️ Publish external browser activity leases |
| `a108959e75` | `6fa1948ec7` | fix(browser/cdp): 🐛 Keep active leases fresh and leak-free |
| `4cff3aaab5` | `13eda3a05e` | fix(browser/cdp): 🐛 Wait for lease heartbeat shutdown |
| `0b1a7b5521` | `19e407ef29` | fix(browser/cdp): 🐛 Clean up partial lease publication |
| `25b3bd0bd9` | `5e3107cbca` | docs(patches): 📝 Catalogue external CDP activity leases |
| `38eaa82cc4` | `bec721897b` | fix(status): 🐛 Separate canonical ancestry from fork updates |
| `8d53c1b168` | `3b3a308c24` | feat(acp): ✨ Preserve explicit session close for OpenDesign |
| `6ae64b3b6f` | `9bfa349f24` | fix(acp): 🐛 Drain close-time session workers safely |
| `d3b3f4b088` | `fc63477679` | fix(acp): 🐛 Retire replaced runtimes safely |
| `434eb6f3b8` | `91a85444cf` | test(acp): 🧪 Verify upstream command admission and runtime retirement |
| `6df3677cc3` | `1a89ad0e21` | fix(acp): 🐛 Compose disconnect recovery with explicit close boundaries |
| `27d84716a3` | `8fa25cabad` | fix(memory): 🐛 Bridge logical workspace and operation notices |
| `8bb68426c1` | `3ec89c64a8` | docs(doctor): 📝 Retire unused local deep diagnostics |
| `e89068fe4b` | `d69e82860c` | docs(patches): 📝 Reconcile September 29 patch lineage |
| `07c1171063` | `c1d013b116` | refactor(memory): ♻️ Keep only the structured notice bridge |
| `ff2a9e0fea` | `77bdbf77ad` | docs(patches): 📝 Record pinned plugin deployment handoff |
| — | `d0b8381778` | fix(acp): 🐛 Preserve cleanup ownership across close and runtime handoffs |

Reproduce identity review with `git range-diff 09581cacaa..recovery/hermes-update-remote-pre-rebase-20261009T083851Z 8bff64d6ed..d0b8381778`. All 34 previous subjects map uniquely; there are no unexplained drops. The final docs receipt is intentionally additional to this frozen functional ledger.

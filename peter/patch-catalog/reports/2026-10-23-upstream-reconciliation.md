# 2026-10-23 upstream reconciliation

- Date: 2026-10-23
- Prepared by: Claude Code (Opus 5.5), first Claude-run fork update
- Upstream base: `f3b5b980d6158794beb3d1044fd7b8ca4b8f0b23`
- Old base: `8bff64d6ed3414a66976bfa8ab72c14b6bca2a6f`
- Fork tip at preflight (lease baseline for a later publish): `b0f57c4e714589a522d34f6c6217a9dd75be4595`
- Seed: local `peter/hermes-patches` `97cbaa5a9a` (strict fast-forward of the fork, 9 unpublished catalogued commits, included by Peter's decision)
- Recovery: `recovery/hermes-update-remote-pre-rebase-20261023T185053Z` (fork tip), `recovery/hermes-update-local-pre-rebase-20261023T185053Z` (local tip)
- Candidate branch: `update/hermes-patches-20261023T185053Z`
- Scope: isolated preparation, then publication to `origin/peter/hermes-patches` only with `--force-with-lease` against `b0f57c4e71` (Peter-approved). Not installed; no live config migrated.

## Upstream blast-radius gate

Tripped by #106742 "Unified gateway runtime" (`eb75627faf`, merged 2026-10-14): 1,968 files, +184k/-48k, 2,031 newly reachable commits; worst 72 h window ≈3.4k files. Peter chose intentional inclusion after a briefing (post-merge runtime fix rate fell from ~125/day to 3-19/day by Oct 21-23). The same range also carries #143146 (browser_exec-only, Camofox to plugin, merged 2026-10-23).

## Decisions and behavioral preservation

- **ACP family dropped, replaced (Peter-approved):** `3b3a308c24`, `9bfa349f24`, `fc63477679`, `91a85444cf`, `1a89ad0e21`, `d0b8381778` patched the in-process `HermesACPAgent`/`SessionManager` path; production now constructs `GatewayACPAgent` (ACP is a gateway viewer), so that code no longer runs. Upstream now owns history preservation (`gateway/session_acp_lifecycle.py`: idle ACP row ends `acp_disconnect` when its last viewer leaves), reopen (`session/load` + prompt) and worker/runtime ownership (the owner runs turns). The only lost contract was explicit `session/close`; the new local patch `feat(acp): ✨ Detach one editor session on explicit close` restores it on `GatewayACPAgent` (cancel and drain this editor's prompt, then `session.detach`; refuse and stay attached if it cannot drain in 30 s). `AIAgent.close(preserve_session=...)` had no other consumer and dropped with the family.
- **CDP launch adapted:** `tools/browser_tool_cdp.py` was deleted upstream; bounded on-demand launch, endpoint-canonical per-process locks and the `cdp_endpoint` alias are ported into `tools/browser_session_cdp.get_cdp_override`/`get_cdp_override_raw`. The `BROWSER_CDP_AUTO_LAUNCH`/`BROWSER_CDP_LAUNCH_COMMAND` env overrides are intentionally retired: `os.environ` holds the launch profile's values in a multi-profile process, and no profile `.env` set them. Config keys are unchanged. Camofox-specific alias reads went with upstream's Camofox removal.
- **CDP activity leases retained:** `browser_exec` keeps the lease wrapper; the split now carries upstream's pre-routing `local_sidecar`/`route_key` (a post-rebase `UnboundLocalError` was found by the gate and folded into the owning commit).
- **Discord approvals retained:** upstream `resolve_gateway_approval` accepts `request_id` but its Discord view never passes one, and upstream has no settled-card retirement. Display-context capture moved to upstream's new coalescing construction site.
- **Memory notice bridge retained:** composed with upstream `initialize_for_agent(say=...)`; the extracted `agent/agent_init_memory.py` body equals upstream's plus notice callbacks; `_aux` extraction is byte-identical.
- **SSH sync progress adapted:** local bounded batches and acknowledged-progress checkpoints are kept; the local per-sync content hash in `_plan_sync` is superseded by upstream's racy-mtime key plus pushed-hash confirmation. Hash-confirmed (not re-uploaded) keys are committed before transfers.
- **Unchanged (`=`):** SSH portability, TUI DB-handle recovery (path still live: `_prepare_turn_input`), canonical ancestry status, Hindsight hygiene, CLI memory cwd, Linux session clock identity, Doctor retirement docs.

## Deployment-visible upstream changes for Peter's profiles

- `browser.backend` is removed by config migration v52. Profiles on `browser-use` keep `browser_exec`; `clerk` and `coding` (`local_cdp`) lose the built-in `browser_navigate`/`click`/... tools and use `browser_exec` against the same Edge CDP endpoint. `cdp_url`/`cdp_endpoint`/`cdp_auto_launch`/`cdp_launch_command` stay effective. Hermes-launched Chromium (not used with `cdp_url`) is now launched lazily and stopped by the inactivity janitor.
- ACP editors (OpenDesign) attach to the profile gateway; `hermes gateway ensure` starts it.

## Verification and review

Disposable candidate worktree outside `HERMES_HOME` (`~/src/hermes-worktrees/`), isolated scratch `HERMES_HOME`/`HERMES_RUNTIME_DIR`, `scripts/run_tests.sh` per-file subprocesses. No operation touched the live checkout, venv or user state.

- Changed-area gate (every stack-touched area: browser, SSH/file sync, approvals, Discord, memory/agent init, status/banner/active sessions, all `tests/acp_adapter/`, all `tests/tui_gateway/`): **624 files, 5,159 passed, 7 failed, 29 skipped**. Six failures (`tests/tui_gateway/test_profiles_list_*`) reproduce identically on pristine upstream `f3b5b980d6` and are recorded as baseline. The seventh (`test_approval_gateway_wait_coalesce_race.py`) was a stale upstream test double for `_ApprovalEntry`; fixed in the owning approval commit.
- Post-fixup reruns: ACP **88 files, 448 passed, 1 skip**; SSH/file sync **9 files, 94 passed, 21 platform skips**; browser/lease/approval/memory/TUI fixup files **131 passed**.
- New regressions proven RED on the pre-fix tree and GREEN after: ACP close (4 + 3 race tests), live `/browser connect` lease scoping (1).
- `python scripts/check --base upstream/main`: **12 checks ok**, code health **0 blocking** (the default `origin/main` base is Peter's stale fork main and must not be used).
- Independent read-only review of the frozen risky delta: **no blockers**; its concerns were fixed (lease endpoint read from `os.environ` → profile-scoped `get_cdp_override_raw`; ACP close reconnect/slash/recovery/card races). Follow-up review of the revised commits: **no blockers**.
- Upstream refreshed once during preparation (`e04614af7b` → `f3b5b980d6`, 11 landings, no overlap with stack paths); frozen afterwards.

## Known limitations

- ACP: a prompt sent concurrently with the same editor's `session/close` (protocol misuse) can still leave an admitted turn with no viewer.
- TUI DB recovery: with a `profile_home` the reopen fails closed via upstream's turn recovery, so the "storage unavailable" warning only fires for non-profile sessions.
- SSH sync-back skips remote files with no confirmed push when the host path exists (intentional local contract, differs from upstream).
- With `cdp_auto_launch`, an endpoint alive but slower than 1 s triggers the (idempotent) helper.

## What's new for Peter (curated)

- **Unified gateway runtime (#106742):** one gateway per profile owns every session; CLI, TUI, Desktop, ACP, bots and cron attach as viewers. Closing a terminal detaches instead of killing the turn; approvals/clarifications settle in every open window; session policy (model, cwd, toolsets) freezes at creation. Automatic after update; `hermes gateway ensure` starts the owner.
- **Browser (#143146):** `browser_exec` is the only browser tool; built-in `browser_*` tools and agent-browser are gone; Camofox moved to a plugin. Hermes-launched Chromium starts lazily and the inactivity janitor stops it. Your Edge CDP route is unchanged (local patches retained); `clerk`/`coding` switch from built-in tools to `browser_exec`.
- **TUI:** busy queue-mode input enters the durable FIFO immediately; `/save` writes the owner's export; standing `/loop` row with countdown; `/connectors` manages named connector accounts; `/usage` shows shared-gateway session totals.
- **Desktop:** redesigned Capabilities catalog (Skills, Plugins, Connectors, Tools); delegation routing settings; drag-to-pin sessions; `browser_vault` can ask for codes/logins in Desktop chats (#142924).
- **MCP:** per-tool costs and a per-chat spend limit; `notifications/progress` forwarded as live tool progress; experimental webhook-mode MCP events client (#140121, opt-in).
- **Cron:** many unified-runtime reliability fixes (admission-based run lookup, stale-run reclaim on the judged snapshot, failed fires kept); no new opt-in feature.
- **Slack:** slash commands keep arrival order, honour channel skill bindings and routed-profile auth. **Discord:** durable role grants re-authorized through the ingress gate resolver. No new Discord feature.
- **Skills:** cache/lock correctness and "every turn announces skill changes once on every surface"; no new user-facing feature.
- **Other:** usage-window plan support in the model picker (#142308); shared-metrics consent now asks a two-choice question (#142350).

## Exact ledger

| Previous ref | Mark | Active ref | Subject |
|---|---|---|---|
| `09569c8c85` | adapted (!) | `ab77b1b0fe` | fix(ssh): 🐛 Preserve portable file-only bulk uploads |
| `cb13b13673` | adapted (!) | `3debae964c` | feat(browser): 🚀 Launch configured CDP endpoints on demand |
| `0b42ce86dd` | adapted (!) | `0988d57974` | fix(tui): 🐛 Recover missing session database handles |
| `4d70117e69` | adapted (!) | `c309dd572a` | docs(patches): 📝 Document diagnostics and CDP launch |
| `42fab389cc` | retained (=) | `6e7942facd` | docs(patches): 📝 Reconcile the post-monster patch stack |
| `dfe271189a` | adapted (!) | `1155511c27` | fix(browser): 🐛 Scope CDP launch locks by endpoint |
| `f50462c192` | adapted (!) | `1f70691c83` | docs(patches): 📝 Record independent review corrections |
| `d5b03ba057` | adapted (!) | `ada56f5856` | fix(browser): 🐛 Canonicalize CDP launch lock identities |
| `57f3224e22` | retained (=) | `a7077b0e1e` | docs(patches): 📝 Record second review corrections |
| `cc8dc5c908` | retained (=) | `94d8d311ef` | docs(patches): 📝 Record clean final review |
| `a1203b14d2` | retained (=) | `6bef9fec10` | fix(ssh): 🐛 Use POSIX paths for remote archives |
| `b95853aa6b` | retained (=) | `faa18027b7` | docs(patches): 📝 Catalogue portability follow-ups |
| `73a84f541c` | retained (=) | `625eedc9b1` | fix(ssh): 🐛 Contain Windows archive staging paths |
| `8560536e20` | retained (=) | `872c5efd90` | fix(ssh): 🐛 Reject unrepresentable Windows archive names |
| `5bf03f258b` | retained (=) | `7ee1e480b7` | fix(ssh): 🐛 Validate upload paths before remote writes |
| `33a3bb10f0` | retained (=) | `3986f6f91f` | docs(patches): 📝 Record final portability review |
| `3307f81160` | retained (=) | `de55240a44` | docs(patches): 📝 Reconcile September 22 active catalogue lineage |
| `bb274bae12` | retained (=) | `a88c1c0d22` | docs(patches): 📝 Record verified update candidate |
| `47b433357f` | adapted (!) | `559160ee29` | feat(browser/cdp): 🕰️ Publish external browser activity leases |
| `6fa1948ec7` | retained (=) | `1b64304918` | fix(browser/cdp): 🐛 Keep active leases fresh and leak-free |
| `13eda3a05e` | retained (=) | `838e2a0de8` | fix(browser/cdp): 🐛 Wait for lease heartbeat shutdown |
| `19e407ef29` | retained (=) | `f7044c220b` | fix(browser/cdp): 🐛 Clean up partial lease publication |
| `5e3107cbca` | retained (=) | `4b2b4275ee` | docs(patches): 📝 Catalogue external CDP activity leases |
| `bec721897b` | retained (=) | `1ce79b79cb` | fix(status): 🐛 Separate canonical ancestry from fork updates |
| `3b3a308c24` | dropped | — | feat(acp): ✨ Preserve explicit session close for OpenDesign |
| `9bfa349f24` | dropped | — | fix(acp): 🐛 Drain close-time session workers safely |
| `fc63477679` | dropped | — | fix(acp): 🐛 Retire replaced runtimes safely |
| `91a85444cf` | dropped | — | test(acp): 🧪 Verify upstream command admission and runtime retirement |
| `1a89ad0e21` | dropped | — | fix(acp): 🐛 Compose disconnect recovery with explicit close boundaries |
| `8fa25cabad` | adapted (!) | `b656e03cfb` | fix(memory): 🐛 Bridge logical workspace and operation notices |
| `3ec89c64a8` | retained (=) | `eb94493bc5` | docs(doctor): 📝 Retire unused local deep diagnostics |
| `d69e82860c` | retained (=) | `7d33e874ed` | docs(patches): 📝 Reconcile September 29 patch lineage |
| `c1d013b116` | adapted (!) | `3f31c1730d` | refactor(memory): ♻️ Keep only the structured notice bridge |
| `77bdbf77ad` | retained (=) | `812cc0142b` | docs(patches): 📝 Record pinned plugin deployment handoff |
| `d0b8381778` | dropped | — | fix(acp): 🐛 Preserve cleanup ownership across close and runtime handoffs |
| `ef3c7e1baa` | retained (=) | `3df98d2729` | docs(patches): 📝 Reconcile October 9 upstream refresh and verification |
| `255404440a` | retained (=) | `e6c99cea50` | chore(hindsight): ⚙️ Preserve the project memory bank identity |
| `21fbc45964` | adapted (!) | `6ed0e4bbcd` | fix(discord/approvals): 🛠️ Bind approval buttons to exact queue requests |
| `8826f698ad` | retained (=) | `1581f4fa53` | docs(patches): 📝 Catalogue Discord exact-request approval fix |
| `94998ef764` | retained (=) | `509b3ae339` | fix(hindsight): 🛠️ Keep personal bank routing local and ignored |
| `24c663bf2a` | retained (=) | `bf91645e11` | docs(patches): 📝 Reconcile Discord publication and personal Hindsight hygiene |
| `378d6c2106` | retained (=) | `bd1700f5db` | fix(memory/cwd): 🛠️ Pass implicit CLI workspaces to memory providers |
| `b0f57c4e71` | retained (=) | `c8e3477e6a` | docs(patches): 📝 Catalogue implicit CLI memory workspace fix |
| `977d4a420c` | adapted (!) | `8ac370a23e` | fix(approvals): 🛠️ Bind exact display context and retire settled Discord peers |
| `a0e3f7f0b8` | retained (=) | `a872082bf9` | docs(patches): 📝 Catalogue approval identity and peer settlement contracts |
| `410c7114c2` | retained (=) | `8f2f1649f1` | docs(patches): 📝 Record local approval patch integration and restart boundary |
| `72cfc15381` | retained (=) | `8be151aa45` | fix(sessions): 🛠️ Keep Linux ownership stable across clock steps |
| `7743a9af63` | retained (=) | `3c5eb3dc7f` | docs(patches): 📝 Catalogue Linux session identity candidate |
| `31a38b165b` | retained (=) | `71ea78281b` | docs(patches): 📝 Record ownership patch integration into personal stack |
| `4bc06ec2b0` | retained (=) | `e77b1098e1` | docs(patches): 📝 Record isolated upstream ownership draft publication |
| `7afc5e3adb` | adapted (!) | `b7bef45e35` | fix(ssh/sync): 🛠️ Retain acknowledged upload progress across retries |
| `97cbaa5a9a` | retained (=) | `2ff19f742b` | docs(patches): 📝 Catalogue verified SSH sync progress recovery |
| — | new | `dd2f9a04c7` | feat(acp): ✨ Detach one editor session on explicit close |

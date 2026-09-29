# 2026-09-29 upstream reconciliation

- Date: 2026-09-29
- Candidate worktree: `/home/kidroca/.hermes/worktrees/hermes-update-20260929T103018Z`
- Original frozen code: `8bb68426c165ace735f7ff4d75c13a05d4133481`
- Current scope: notice-only reduction following `e89068fe4b`; original ledger below remains historical.
- Upstream base: `09581cacaa8db3b3241dbbabe76a351a2ce14f60`
- Old base: `92dd3321929a915479ade608591d40de93965c7b`
- Recovery: `recovery/hermes-update-local-20260929T103018Z` at `e0d58f3e30313646247df4fb2dc9f96127461e64`
- Active core refs: `8a95378f3d`, `523ac0608f`, `1858f6ae23`, `8cd0a657b0`, `35a450380c`, `8d53c1b168`, `6ae64b3b6f`, `d3b3f4b088`, `434eb6f3b8`, `6df3677cc3`, `38eaa82cc4`, `27d84716a3`, `de0cffd125`, `57c5226407`, `5d83c0571a`, `68e5fe88ad`, `0849b72862`, `a108959e75`, `4cff3aaab5`, `0b1a7b5521`, `25b3bd0bd9`, `e2768e778b`, `8bb68426c1`
- Status: isolated candidate reduction and focused verification; no installation, live configuration change, deployment or publication.

## Decisions and evidence

Every old commit is accounted for in the exact range-diff ledger below. Equal
patches still receive new active refs. Prior active tables and receipts remain
historical, not instructions to replay retired behavior.

- **SSH retained:** `be991680f9` → `8a95378f3d` changes only the regression marker
  from `linux_only` to upstream `platforms("linux")`. The four portability and
  pre-write validation follow-ups are patch-identical.
- **ACP adapted, not retired:** `c0933dc147` and `388e15403d` move around upstream
  shutdown/model-switch additions. Upstream `9fb2dd4c39` stamps `acp_disconnect`
  and cold-restores sessions. Follow-up `6df3677cc3` composes this with the local
  contract: ordinary lookup reopens disconnects, explicit `acp_close` requires
  load/resume, compression/reset structural markers stay ended, and failed runtime
  reconstruction rolls back reopening. Worker ownership/drain and old-runtime
  retirement remain. Evidence: `acp_adapter/session.py`,
  `tests/acp_adapter/test_restore_end_reasons.py`,
  `tests/agent/test_close_preserve_session.py`; upstream command admission is
  exercised by `434eb6f3b8`, not replaced by a second lock.
- **Doctor policy retirement:** `70b79d6498`, `727d0f8e92`, `ac070ab30e` have no
  replacement implementation. Peter explicitly chose upstream Doctor instead of
  maintaining local bounded shallow/deep diagnostics. This is NOT equivalent
  upstream supersession. `8bb68426c1` removes stale deep-Doctor CLI documentation;
  the CDP part of `121fabf410` → `e2768e778b` remains.
- **Fork status adapted:** old `dfbf559653` checker is architecturally obsolete.
  Upstream `cfebdfd466` owns passive source checking and `0cfd42e562` splits its
  cache/check flow. Replacement `38eaa82cc4` changes only banner/status and their
  regression tests: discover canonical GitHub remote from local configuration,
  compare available refs, report behind/carried counts only for provable nonshallow
  ancestry, and label unknown ancestry. It adds no fetch/network request and does
  not redirect installable fork updates or take over upstream update-cache policy.
- **Hindsight externally adapted:** upstream `4cbf862abe` removed the bundled
  provider. Old `b3551b9ce0` splits into generic core bridge `27d84716a3` and the
  external port below. The follow-up removes the unnecessary workspace portion
  of `27d84716a3`: cwd/config/backend handling and `agent_workspace` match upstream
  `09581cacaa` exactly, including the existing `"hermes"` workspace label rather
  than substituting a path into provider `{workspace}` templates. Only optional
  `notice_callback` / `notice_clear_callback` plumbing remains for structured
  retention alerts. The external plugin resolves routing through stock scoped
  APIs, with no dependency on a core workspace bridge. Do not restore deleted
  vendor code in Hermes core. Git-common project routing, explicit remote
  overrides/safe unresolved fallback, mission synchronization, and demand-driven
  retain failure/recovery notices remain. Async acceptance is not completion;
  recovery requires confirmed success. Automatic recall remains independently
  opt-out; previously retired recall/provenance/display policy stays retired.
- **Browser/TUI retained:** launch and DB-recovery patches are identical. Lease
  introduction `c57259c0e6` → `0849b72862` has only upstream harness import/preflight
  context changes in range-diff; its heartbeat, shutdown and partial-publication
  follow-ups are identical. All five formerly unpublished CDP commits are covered,
  including documentation `e0d58f3e30` → `25b3bd0bd9`. No browser configuration or
  external watchdog deployment was changed.

## External Hindsight repository (not a core ancestor)

- Repository/worktree: `/home/kidroca/.hermes/worktrees/hindsight-plugin-20260929`
- Baseline: `85333e16578bcc6d66c552be73ddf7df9aaf99d3` (`85333e1`)
- Port: `10c543b3a4d7cf020fd0efbf955f710dff101126`
- Deployment-preparation follow-up supplied by the plugin worker: `d13074c2`
  in `kidroca/hindsight`, branch `peter/hermes-hindsight`. This is a separate
  repository commit, not evidence of live deployment or publication.
- PR #4940 stays narrow and stock-compatible: project routing uses existing
  scoped APIs; the personal core notice bridge is optional, not a routing prerequisite.
- Catalog source: `https://github.com/vectorize-io/hindsight`, subdirectory
  `hindsight-integrations/hermes`, pinned source
  `176f8c2de1369f569c489b831d143b78128b5535`.
- Evidence: frozen core `plugin-catalog/hindsight.yaml`; external commit message,
  `LOCAL_PORT.md`, `project.py`, `settings.py`, `__init__.py`,
  `integration/test_hindsight_routing_missions.py`, and
  `integration/test_hindsight_retain_notices.py`.
- This external commit is intentionally absent from the core-ancestor table. Its
  baseline ancestry is checked in its own repository. The core catalog continues
  to name the upstream source pin; this reconciliation does not deploy or switch
  that pin to the local port. Deployment must preserve the external port explicitly.
- Catalog caveat remains: embedded mode at the pinned provider uses a retired
  lazy-install path on PM-managed Hermes; prefer supported cloud/local-external
  modes. No mode or live profile was changed here.

## Notice-only reduction verification

The reduction modifies `agent/agent_init.py`, `agent/memory_provider.py` and
`agent/runtime_cwd.py`, replaces `test_memory_workspace_notice_bridge.py` with
`tests/agent/test_memory_notice_bridge.py`, and updates this report and index.
Against upstream `09581cacaa`, the three production files now differ only by
five lines of optional callback wiring and three documentation lines;
`runtime_cwd.py` is byte-identical. Unrelated ACP and other patch families are untouched.

Canonical isolated run (candidate Python 3.14.4; no installs):

```sh
HOME=$PWD/.venv/test-home HERMES_PYTHON=$PWD/.venv/bin/python scripts/run_tests.sh \
  tests/agent/test_memory_notice_bridge.py tests/agent/test_memory_provider_init.py \
  tests/agent/test_memory_provider.py tests/agent/test_memory_agent_context.py \
  tests/agent/test_memory_user_id.py tests/agent/test_memory_recall_indicator.py \
  tests/agent/test_runtime_cwd.py
```

Result: **7 files, 89 passed, 0 failed**. The six new parametrized cases exercise
actual external plugin loading, `MemoryManager`, `StatusOutputMixin`, structured
notice identity, failure/recovery clear delivery, absent/broken driver sinks,
CLI-only status behavior and optional non-callable method omission. They do not
claim end-to-end rendering by every driver. With only the callback wiring removed,
the new file produces **4 failed, 2 passed** (`KeyError: notice_callback`); restoring
it returns the focused run to green. `git diff --check` passes.

Independent review of this changed delta remains for the coordinating agent;
prior review and the prior 330-test receipt below predate this reduction.

## Exact commit ledger

Reproduce with:

```sh
git range-diff 92dd3321929a915479ade608591d40de93965c7b..recovery/hermes-update-local-20260929T103018Z 09581cacaa8db3b3241dbbabe76a351a2ce14f60..8bb68426c165ace735f7ff4d75c13a05d4133481
```

`=` means retained identical patch, `!` retained/adapted patch, `<` absent from
core replay (explicit disposition supplied), `>` intentional new adaptation.
Documentation mappings preserve historical records, not obsolete active claims.

| Old ref | Marker | Candidate ref / disposition | Subject |
|---|---|---|---|
| `be991680f9` | `!` | `8a95378f3d` | fix(ssh): 🐛 Preserve portable file-only bulk uploads |
| `054d15fd5c` | `=` | `de0cffd125` | feat(browser): 🚀 Launch configured CDP endpoints on demand |
| `43dcbf1513` | `=` | `68e5fe88ad` | fix(tui): 🐛 Recover missing session database handles |
| `121fabf410` | `=` | `e2768e778b` | docs(patches): 📝 Document diagnostics and CDP launch |
| `b18c5529db` | `=` | `27724944be` | docs(patches): 📝 Reconcile the post-monster patch stack |
| `c7e21c1950` | `=` | `57c5226407` | fix(browser): 🐛 Scope CDP launch locks by endpoint |
| `69483a0cb0` | `=` | `7b008056f5` | docs(patches): 📝 Record independent review corrections |
| `1ec78b8d67` | `=` | `5d83c0571a` | fix(browser): 🐛 Canonicalize CDP launch lock identities |
| `e710f508dd` | `=` | `e5fcf43eb8` | docs(patches): 📝 Record second review corrections |
| `ed3cb90e64` | `=` | `0b0ca22a0b` | docs(patches): 📝 Record clean final review |
| `4af0015a74` | `=` | `523ac0608f` | fix(ssh): 🐛 Use POSIX paths for remote archives |
| `e083839c15` | `=` | `fbeeccb468` | docs(patches): 📝 Catalogue portability follow-ups |
| `9435889c90` | `=` | `1858f6ae23` | fix(ssh): 🐛 Contain Windows archive staging paths |
| `9d8adff651` | `=` | `8cd0a657b0` | fix(ssh): 🐛 Reject unrepresentable Windows archive names |
| `426c0f9258` | `=` | `35a450380c` | fix(ssh): 🐛 Validate upload paths before remote writes |
| `0769f3455b` | `=` | `93c6e2bf89` | docs(patches): 📝 Record final portability review |
| `dc2850b10a` | `=` | `2a18d75ff1` | docs(patches): 📝 Reconcile September 22 active catalogue lineage |
| `0592565e2b` | `=` | `f03dd3eed0` | docs(patches): 📝 Record verified update candidate |
| `c57259c0e6` | `!` | `0849b72862` | feat(browser/cdp): 🕰️ Publish external browser activity leases |
| `78b3c08653` | `=` | `a108959e75` | fix(browser/cdp): 🐛 Keep active leases fresh and leak-free |
| `3872af22de` | `=` | `4cff3aaab5` | fix(browser/cdp): 🐛 Wait for lease heartbeat shutdown |
| `ed0a742fa9` | `=` | `0b1a7b5521` | fix(browser/cdp): 🐛 Clean up partial lease publication |
| `e0d58f3e30` | `=` | `25b3bd0bd9` | docs(patches): 📝 Catalogue external CDP activity leases |
| — | `>` | `38eaa82cc4` | fix(status): 🐛 Separate canonical ancestry from fork updates |
| `c0933dc147` | `!` | `8d53c1b168` | feat(acp): ✨ Preserve explicit session close for OpenDesign |
| `ce7b571fe6` | `=` | `6ae64b3b6f` | fix(acp): 🐛 Drain close-time session workers safely |
| `70b79d6498` | `<` | Policy-retired Doctor; docs `8bb68426c1` | feat(doctor): 🩺 Add bounded deep database diagnostics |
| `dfbf559653` | `<` | Adapted as `38eaa82cc4` | fix(update): 🐛 Resolve fork status against canonical upstream |
| `b3551b9ce0` | `<` | Adapted as core `27d84716a3` + external `10c543b3a4d7cf020fd0efbf955f710dff101126` | fix(memory): 🐛 Route project banks and retain notices reliably |
| `388e15403d` | `!` | `d3b3f4b088` | fix(acp): 🐛 Retire replaced runtimes safely |
| `727d0f8e92` | `<` | Policy-retired Doctor; docs `8bb68426c1` | fix(doctor): 🐛 Bound deep SQLite integrity walks |
| `d9a8d7495b` | `=` | `434eb6f3b8` | test(acp): 🧪 Verify upstream command admission and runtime retirement |
| `ac070ab30e` | `<` | Policy-retired Doctor; docs `8bb68426c1` | fix(doctor): 🐛 Preserve deadline interrupts through FTS probes |
| — | `>` | `6df3677cc3` | fix(acp): 🐛 Compose disconnect recovery with explicit close boundaries |
| — | `>` | `27d84716a3` | fix(memory): 🐛 Bridge logical workspace and operation notices |
| — | `>` | `8bb68426c1` | docs(doctor): 📝 Retire unused local deep diagnostics |

## Verification receipts and limits

Parent-provided execution receipts for frozen core `8bb68426c1` (not tests run by
this catalogue writer):

- Combined gate: **36 files, 330 passed, 0 failed, 1 Windows skip**, isolated HOME,
  Python **3.14.4**, frozen candidate environment; completed before catalogue edits.
- ACP child: **222 passed, 1 skipped**; status child: **58 passed**.
- Browser real-profile suite: **64 passed** with isolated HOME. The earlier three
  failures also reproduced on upstream baseline and came from the real-home test
  guard; they are not claimed as candidate regressions.
- External plugin: **26 unit + 53 integration passed**, verified against this
  frozen core candidate.
- Three independent static reviews reported no blockers for ACP/bridge/Doctor,
  SSH/CDP/TUI/status, and external Hindsight respectively.

This is bounded verification, not repository-wide or live-deployment certification.
Catalogue changes are Markdown only. Mechanical checks resolve every active core
ref as a frozen-candidate ancestor, check linked report/header coverage, enumerate
all old/new range entries, verify the external baseline ancestry, and run
`git diff --check`. No new upstream web research was performed; local Git objects,
provided policy decisions and explicitly attributed parent receipts are the evidence.
No push, install or live configuration changes are part of this reconciliation.

Mechanical verification result: **8 active rows, 23 distinct active core refs**, all
ancestors of the frozen candidate and present in this report header; **126 local
Markdown links** across the catalogue resolve. The ledger covers **all 32 old
commits and all 31 candidate commits**, with **no mapping gaps**. The previous
active section is preserved verbatim under its historical heading. External
baseline `85333e1` is an ancestor of port `10c543b3a4d7cf020fd0efbf955f710dff101126`.
`git diff --check` passed.

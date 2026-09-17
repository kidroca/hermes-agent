# 2026-09-17 post-monster patch-stack reduction

## Scope

Rebuilt `peter/hermes-patches` from upstream `691228447d` after the 4,000+ PR integration wave instead of replaying the old stack mechanically. The resulting candidate contains ten focused functional commits, one documentation commit, and this catalogue reconciliation.

## Active stack

| Commit(s) | Local behavior retained |
|---|---|
| `0addfd7e7a`, `321c18132a` | Portable, file-only SSH bulk uploads and no upload work for prompt metadata probes |
| `891b4f2e54`, `5fc24844ab` | Explicit ACP session close with bounded cancellation/drain, resource teardown, preserved history, and safe reopen behavior |
| `03adb5863d` | Fast TUI startup, workspace freshness, and WSL systemd PATH comparison normalization |
| `63eb7278a0` | Bounded read-only routine Doctor checks plus explicit snapshot-based `--deep` verification |
| `6a45562236` | Fork update status resolved against canonical upstream rather than the fork remote |
| `920aa29273` | Git-project Hindsight bank routing, mission sync, and reliable retain-failure notices |
| `5d97cd142a` | Configured CDP endpoint aliasing and bounded, serialized first-use helper launch |
| `5b7b5b2f23` | End-to-end configured TUI tool-preview budgets, session DB recovery, and finite context estimates |
| `feff9231e0` | User-facing Doctor and CDP launch documentation |

The seven later functional commits carry `Local-Patch: yes`. The three initial
salvage commits (`0addfd7e7a`, `891b4f2e54`, and `321c18132a`) predate that
trailer discipline and are tracked explicitly in the active catalogue instead
of rewriting the already-reviewed chain. The exact commit diff from
`691228447d` is authoritative; older report files remain as design and rebase
history.

## Deliberately not replayed

The reduction intentionally left out patches whose behavior is now upstream, whose old premise no longer fits the current architecture, or whose maintenance cost outweighed the local value:

- ACP lazy persistence, curator read serialization, per-platform Kanban opt-in, and approval-bell corrections now covered upstream.
- Kanban profile-denial/autoprefetch policy patches were parked rather than silently reconstructed against the rewritten worker architecture.
- Hindsight auto-recall heuristics, display/debug notices, recalled-memory provenance, retain previews, Slack-specific recall-query shaping, and custom prefetch-deadline behavior were retired from the reduced stack. The retained memory commit is limited to project routing, mission synchronization, and failure visibility.
- The historical WSLg/Desktop workaround was not carried forward.
- Historical patches already marked superseded or dropped remain historical only.

Absence is intentional: do not revive one of these patches solely because its old report still exists.

## Verification

Independent execution against the candidate produced:

- ACP: 178 passed.
- Runtime/prompt/gateway: 192 passed, 1 macOS-only skip after removing an unrelated empty `/tmp/.git` test contaminant and correcting a WSL test stub.
- Doctor: 151 passed.
- Fork update status: 35 passed.
- Hindsight/memory: 342 passed across the affected suites.
- Browser/CDP affected tests: 77 passed. The separate network-sensitive Camofox authentication file timed out after unaffected cases and was not used as evidence for the changed CDP path.
- TUI backend: 730 passed; one pre-existing pinned-mtime race failed once and passed in isolated rerun. The two recovered regression files then passed 9/9 independently with retries disabled.
- `ui-tui` workspace check: 170 files / 1,771 tests passed, including typecheck, build, and lint. Root `npm run check` remained blocked only by two unrelated Desktop `voice-prefs.test.ts` localStorage failures.
- Ruff over all changed Python files and `git diff --check`: passed.

A detached immutable review worktree was created at `feff9231e0` for final independent source review before publication.

## Publication guard

Replace the fork branch only after the independent review is clean, the catalogue commit is included, the remote lease still matches the preflight baseline, and the pushed remote is read back. The running TUI must then be updated from a separate shell with backup enabled.

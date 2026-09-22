# 2026-09-17 post-monster patch-stack reduction

> Historical report as of 2026-09-22. All refs, active labels, recommendations,
> and verification below describe the dated historical stack, not the current candidate.
> See [current reconciliation](2026-09-22-upstream-rebase.md) for active identities and decisions.

## Scope

Rebuilt `peter/hermes-patches` from upstream `691228447d` after the 4,000+ PR integration wave instead of replaying the old stack mechanically. The resulting candidate contains ten focused functional commits, eleven independent-review corrections, one documentation commit, and catalogue reconciliation commits.

## Active stack

| Commit(s) | Local behavior retained |
|---|---|
| `0addfd7e7a`, `321c18132a`, `208e2fcbb8`, `cdb2dfb828`, `6b1b034810`, `d9353e5ea3` | Portable, file-only SSH bulk uploads with pre-write path validation, POSIX remote archive paths, Windows-safe contained staging, and no upload work for prompt metadata probes |
| `891b4f2e54`, `5fc24844ab`, `686c6074cb`, `0d6a498c7a` | Explicit ACP session close with bounded cancellation/drain, serialized replacement-runtime cleanup, resource teardown, preserved history, and safe reopen behavior |
| `03adb5863d`, `aa12a7891d` | Fast TUI startup, workspace freshness, and WSL-only systemd PATH comparison normalization |
| `63eb7278a0`, `6b291310b2`, `885c83175d` | Bounded read-only routine Doctor checks plus explicit snapshot-based `--deep` verification with propagated SQLite VM deadlines |
| `6a45562236` | Fork update status resolved against canonical upstream rather than the fork remote |
| `920aa29273` | Git-project Hindsight bank routing, mission sync, and reliable retain-failure notices |
| `5d97cd142a`, `104bb14617`, `dc35eb4155` | Configured CDP endpoint aliasing and bounded, canonical endpoint-scoped first-use helper launch |
| `5b7b5b2f23` | End-to-end configured TUI tool-preview budgets, session DB recovery, and finite context estimates |
| `feff9231e0` | User-facing Doctor and CDP launch documentation |

The later functional and review-correction commits carry `Local-Patch: yes`. The three initial
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

A detached immutable review at `feff9231e0` found three blockers: an ACP
replacement-runtime leak, unbounded SQLite VM walks in deep Doctor, and a
cross-endpoint CDP launch lock. Commits `686c6074cb`, `6b291310b2`, and
`104bb14617` corrected those findings. A second detached review at `7be999d501`
then found concurrent ACP replacements were not serialized, FTS probes could
swallow Doctor deadline interrupts, and equivalent CDP discovery URLs used
different launch locks. Commits `0d6a498c7a`, `885c83175d`, and `dc35eb4155`
correct those findings.

The second corrections passed 182 ACP/close tests, 11 deep-Doctor tests, 152
other Doctor tests, and 61 focused browser/CDP tests. Ruff and `git diff
--check` passed. Three independent reviewers then inspected the immutable
`35e519688a` candidate: ACP runtime replacement, Doctor deadline propagation,
and CDP lock canonicalization all passed with no blocking findings. The two
recovered TUI regression files also passed 9/9 from that immutable worktree.

A delayed first-review result exposed two portability follow-ups. Commit
`aa12a7891d` restricts drive-shaped `/mnt/<letter>` PATH normalization to WSL,
so legitimate native-Linux mounts remain part of systemd staleness checks.
Upstream issue #73163 and open PR #73174 address the related root cause—WSL
unit generation scraping excessive `/mnt` entries—but current upstream does
not yet contain that fix. Commit `208e2fcbb8` uses POSIX semantics for SSH
remote archive members on every host OS and rejects the sync-base path itself
and all parent escapes. Independent review then found that Windows staging
could reinterpret a valid POSIX backslash as a host separator; `cdb2dfb828`
adds native-path containment. A second review found further Windows aliases,
including drive/ADS colons, reserved device names, trailing dots or spaces, and
invalid or control characters; `6b1b034810` rejects every remote component that
Windows cannot represent faithfully before staging it. Final review found that
an escaping destination could still trigger remote directory creation before
rejection; `d9353e5ea3` validates and canonicalizes the complete upload batch
before issuing any remote command. No matching upstream SSH fix was found. The
combined follow-ups passed 131 gateway/systemd tests and 40 SSH tests, with one
platform skip and 14 live-SSH skips respectively. The final combined focused
suite passed 171 tests with 15 platform/live-SSH skips; Ruff and `git
diff --check` passed. Independent review of the immutable `d9353e5ea3`
candidate found no remaining SSH portability or pre-write side-effect blocker.

## Publication guard

Replace the fork branch only after the independent review is clean, the catalogue commit is included, the remote lease still matches the preflight baseline, and the pushed remote is read back. The running TUI must then be updated from a separate shell with backup enabled.

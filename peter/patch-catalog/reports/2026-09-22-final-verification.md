# Final source verification — 2026-09-22

- Tested source: `0769f3455baea2773971a0f71ad9004012fc0f74`.
- Frozen upstream: `92dd332192`; no newer upstream is included or chased.
- Catalogue integrated from `b9ad556190096112362b3a367ec8c132f97b4b17`.
- This integration changes catalogue Markdown only. Source delta against the tested
  commit is zero; the receipts below are prior real executions, not new test runs.

## Bounded execution receipts

Logs reside in `/tmp/hermes-update-20260922-verification/` on the verification host.
They are local evidence, not committed portable artifacts.

| Check | Result | Log |
|---|---|---|
| ACP | 218 passed | `final-acp.log` |
| Changed areas | 134 passed, 9 skipped | `final-changed.log` |
| Config / ledger / profile | 224 passed, 4 skipped | `final-upstream-config-ledger-profile.log` |
| Gateway contract tests | 4 passed | `final-gateway-contract-tests.log` |
| TUI | 173 files, 1,781 passed, no skips | `final-tui-test.log` |
| Typecheck | Passed | `final-tui-typecheck.log` |
| Lint | Passed; 0 errors, 2 React hooks warnings | `final-tui-lint.log` |
| Ink and TUI builds | Passed; TUI bundle 3.6 MB warning | `final-tui-build-ink.log`, `final-tui-build.log` |
| Generated gateway contracts | Passed, exit 0 | `final-gateway-contract-check.log` |

Python total: **580 passed, 13 skipped**, no failures. This is bounded coverage,
not the full Python suite or cross-platform certification. The prior npm install
reported **2 moderate vulnerabilities** (`final-npm-ci.log`); no audit fix or
dependency change was made in this documentation pass. `final-state.log` records
the tested source SHA and ignored build/dependency artifacts.

## Independent review and limits

Independent reviewer `sa-2-f7be83ca` reported no blockers in a source-only review
of immutable `0769f3455b` (review receipt supplied by the coordinating agent).
Existing limitations remain: synchronous ACP `is_closed` database lookup and
delayed observation of asynchronous retain outcomes. These were not introduced
by this update.

Current gateway deployment is **not certified**. No live command, service change,
deployment, push, install or source-test rerun was performed in this integration.
Multiplex deployment still needs its separate topology and real profile-isolation
gates; browser retirement remains deferred.

## Documentation integration checks

The [catalogue verifier](2026-09-22-catalogue-verification.md) is executed against
the integrated tree, alongside a zero-source-delta check against `0769f3455b`,
Git whitespace checks, author/committer identity and clean-worktree checks.
Integration evidence: `final-docs-verification.log` and `final-docs-state.log`
in the same log directory. Commit author and committer names are `🤖 hermes`.
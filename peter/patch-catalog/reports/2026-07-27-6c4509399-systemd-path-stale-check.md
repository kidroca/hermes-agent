# Ignore volatile WSL drive paths in systemd stale checks

- **Date:** 2026-07-27
- **Repo:** `NousResearch/hermes-agent` (Peter's local patch stack)
- **Patch ref:** `6c4509399` → `0ee8c977f` → `035e797b0` → `b6d6f2e75` → `c4f46a0d9` (pre-2026-08-09 active) → `d301755ee7` (pre-2026-08-14 active) → `92eb8b0c4e` (pre-refresh active) → `236873dac6` (active)
- **Branch:** `peter/hermes-patches`
- **Local status:** retained in Peter's local patch stack
- **Motivation:** `hermes gateway status --system` falsely reported a current unit as outdated on WSL because generated systemd units capture an ambient shell PATH whose Android/Windows interop entries differ across login, sudo, and service-generation contexts.
- **Changed files:** `hermes_cli/gateway.py`; new `tests/hermes_cli/test_systemd_unit_comparison.py`
- **Tests / verification:** focused systemd/gateway run passed (27 tests); `uvx ruff check`, format, and diff checks passed; production-tree emulation against the installed unit passed; independent review of source-equivalent commit `6c4509399` found no blockers before integration as the then-active pre-rebase patch `0ee8c977f`.

## Local patch summary

The patch adds `_normalize_systemd_unit_for_comparison()` and routes both installed and generated unit text through it. It preserves existing optional-directive normalization, then removes only colon-delimited WSL Windows drive entries shaped like `/mnt/<ASCII-letter>` or `/mnt/<ASCII-letter>/...` from quoted `Environment="PATH=..."` payloads. Deterministic Linux PATH entries, arbitrary mounts such as `/mnt/tools`, missing or combined environment assignments, `HERMES_HOME`, `ExecStart`, restart policy, and every other unit difference remain comparable. Six regression tests cover the currentness boundary plus non-drive PATH, non-Windows `/mnt`, non-PATH environment, combined-assignment, and directive drift.

## Upstream overlap

| Kind | # | Title | Age (at 2026-07-27) | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#62210](https://github.com/NousResearch/hermes-agent/pull/62210) | fix(gateway): mask PATH in systemd unit staleness check (WSL Windows-interop churn) | 17 days; created 2026-07-10, updated 2026-07-16 | `derniesner`, association `NONE`; no prior merged PR found by authenticated search | Automated sweeper marked it `keep_open`, salvageability high, but objected to masking all PATH changes. No human approval/review is recorded. Labels were applied by repository actors; that is triage, not approval. | 2 files, +214/-8, 2 commits: `hermes_cli/gateway.py` and `tests/hermes_cli/test_systemd_optional_directives.py` | **Very high / direct.** It changes the same normalizer and adjacent tests. Its current revision removes every `/mnt/*` entry; the local patch further restricts this to Windows drive-mount syntax so `/mnt/tools` remains meaningful. | **Medium-low / uncertain.** It is open, non-draft and GitHub reports it mergeable, but `mergeStateStatus=BLOCKED`, no checks or formal reviews are shown, and it has not updated since 2026-07-16. The sweeper's favorable salvageability is not a merge promise. |
| Issue | [#46276](https://github.com/NousResearch/hermes-agent/issues/46276) | per-profile user gateway units stay outdated after restart/update due PATH mismatch | 43 days; created 2026-06-14, updated 2026-07-25 | `SergeNS-mne`, association `NONE`; a confirming commenter is a `CONTRIBUTOR` | No maintainer design decision or assignment is visible. It is labeled P2 across CLI, gateway, config, install/update, and profiles. | Issue; no patch | **High semantic overlap, low mechanical conflict by itself.** It documents non-WSL and WSL ambient-PATH variants that a `/mnt/*`-only fix does not fully cover. | **Unknown.** It is an open bug report, not an implementation. Recent activity and a contributor reproduction strengthen the problem evidence but do not establish scheduling. |
| Issue | [#61003](https://github.com/NousResearch/hermes-agent/issues/61003) | shutdown_forensics: false-positive “Stale systemd unit” warning when unit exists in system scope only | 19 days; created 2026-07-08, updated 2026-07-24 | `krisg-alias`, association `NONE`; confirming commenter also `NONE` | No maintainer design direction is visible; labeled P3 / gateway | Issue in `gateway/shutdown_forensics.py`; no patch in this item | **Low.** Similar operator-facing false-warning class, but a different check and root cause (scope probing and phantom defaults), so it should not conflict unless stale-warning handling is broadly refactored. | **Unknown.** Useful adjacent evidence only; it neither supersedes nor implements this patch. |

## Notes on most relevant upstream items

### PR #62210 — exact implementation overlap

The first PR commit masked the full systemd PATH payload. An automated sweeper review correctly argued that broad masking could hide meaningful service-PATH updates, so the author revised it to strip `/mnt/*` segments. The local patch incorporates that review but tightens the predicate again: only WSL drive mounts (`/mnt/c/...`, `/mnt/d/...`) are ignored; arbitrary Linux mounts under `/mnt` still trigger staleness.

The upstream revision still treats every `/mnt` entry as disposable, which can hide stable bind mounts, network mounts, or administrator-managed toolchains. Conversely, issue #46276 and a Fedora ostree report show broader non-WSL ambient-PATH drift that this local patch intentionally does not suppress. Those cases need deterministic PATH generation or separate required-entry validation; broad comparison masking is not a safe substitute.

The local patch is smaller than upstream and adds adversarial coverage for deterministic Node paths, `/mnt/tools`, combined assignments, and non-PATH directives. Nevertheless, exact line/file overlap means a future rebase should expect a conflict or the patch becoming redundant. Do not infer likely acceptance merely from `keep_open` or `MERGEABLE`; the PR remains blocked and has no formal review decision.

### Issue #46276 — broader symptom evidence

This issue's only unit diff is PATH, but the changing entry is not limited to Windows drive mounts: it includes base-home Node paths, named-profile context, and editable-checkout `node_modules/.bin`. The issue suggests deterministic target-service PATH generation or normalization paired with required-entry validation. The local patch intentionally leaves those broader cases visible rather than hiding potentially meaningful executable-resolution changes.

### Issue #61003 — adjacent warning, different subsystem

This report is worth watching because it demonstrates operational harm from false stale warnings, but its root cause is scope selection in shutdown forensics rather than unit-text comparison. Treat it as adjacent context, not an upstream replacement or direct conflict.

## Recommendation

**Keep active patch `c4f46a0d9` locally and watch #62210 closely.** Expect very high mechanical conflict if it lands. Drop or reconcile the local patch only after upstream preserves meaningful non-drive PATH drift, arbitrary `/mnt` mounts, missing/combined assignments, and all non-PATH directives. Track #46276 separately; do not broaden this comparison mask to solve its non-WSL cases without deterministic PATH generation or explicit required-entry validation.

## Raw search queries used

Authenticated GitHub REST issue search (`gh api -X GET search/issues`) was run with these exact qualifiers/terms:

```text
repo:NousResearch/hermes-agent is:open systemd unit stale
repo:NousResearch/hermes-agent is:open systemd unit outdated
repo:NousResearch/hermes-agent is:open gateway outdated warning
repo:NousResearch/hermes-agent is:open "Environment=\"PATH=" systemd
repo:NousResearch/hermes-agent is:open PATH comparison gateway
repo:NousResearch/hermes-agent is:open WSL systemd gateway
repo:NousResearch/hermes-agent is:pr is:open systemd PATH
repo:NousResearch/hermes-agent is:issue is:open systemd PATH
repo:NousResearch/hermes-agent is:open systemd PATH
repo:NousResearch/hermes-agent is:pr is:merged author:derniesner
```

Direct authenticated API/CLI views were then used for #62210, #46276, and #61003, including PR files, commits, comments, reviews, review comments, labels/events, merge state, and checks where available.

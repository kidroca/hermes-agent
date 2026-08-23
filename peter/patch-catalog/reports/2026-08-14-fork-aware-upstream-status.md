# Compare fork installs against canonical upstream

- Date: 2026-08-14
- Repo: `NousResearch/hermes-agent`
- Patch ref: `feb00ce956c71adea296375074edc5d0d5364a90` → `b74ce0fb60` → `7dd4f18b73` (pre-drop candidate) → `0a47c05930` (active)
- Branch: `peter/hermes-patches`
- Local status: integrated into the verified update candidate pending guarded publication to `origin/peter/hermes-patches`.
- Motivation: fork installations keep Peter's fork as `origin` and canonical NousResearch Hermes as `upstream`. The startup banner and asynchronous update check hardcoded `origin/main`, which reported `0 behind / 9407 local` instead of canonical upstream lag and suppressed the TUI update warning.
- Changed files: `hermes_cli/banner.py`; `tests/hermes_cli/test_banner_git_state.py`; `tests/hermes_cli/test_update_check.py`
- Tests / verification: canonical `scripts/run_tests.sh` targeted run passed 54 tests across five files; focused Ruff and `git diff --check` passed; a live worktree probe reported `781 behind / 72 carried` at the patch commit; provisional and exact-commit independent reviews found no blockers or security concerns.

## Local patch summary

The banner now discovers the configured remote whose fetch URL canonicalizes to `github.com/nousresearch/hermes-agent`. Official installations continue to use `origin`; fork installations with a canonical `upstream` remote use `upstream/main`; custom/self-hosted checkouts without a canonical remote retain the previous `origin` fallback.

The selected remote is used consistently for the scoped fetch, shallow-clone fallback ref, exact behind count, upstream hash, and carried-commit count. Existing official-SSH behavior remains on the non-counting HTTPS `ls-remote` path rather than triggering SSH/FIDO prompts. The update-cache schema was bumped so a fresh launch does not reuse an earlier false `0 behind` result.

## Upstream overlap

| Kind | # | Title | Dates | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| Issue | [#72789](https://github.com/NousResearch/hermes-agent/issues/72789) | Update banner is silently blind on fork-based deployments | Opened 2026-07-27; updated 2026-07-30 | `elchic00`, association `NONE` | Automated triage confirms the premise and requests canonical-upstream preference, exact-count/unknown semantics, and non-silent failures | Exact `hermes_cli/banner.py` symptom | Very high semantic overlap | N/A; exact open bug report |
| PR | [#38344](https://github.com/NousResearch/hermes-agent/pull/38344) | fix(banner): measure update-check distance against 'upstream' when present | Opened 2026-06-03; updated 2026-07-19 | `ssiweifnag`, `CONTRIBUTOR` | One approval, but `teknium1` says keep open and adapt to current shallow/official-SSH paths | 2 files, +140/-4 | Very high in `banner.py` | Medium-low while dirty and awaiting adaptation |
| PR | [#63912](https://github.com/NousResearch/hermes-agent/pull/63912) | Fix update checks to prefer official upstream | Opened 2026-07-13; updated 2026-08-05 | `matantsevs`, `CONTRIBUTOR` | `teknium1` keep-open review identifies branch-healing, hard-reset, and dashboard-consistency blockers | 9 files, +3038/-93 | Very high; same helper plus broader CLI/desktop paths | Medium-low in current broad form |
| PR | [#72812](https://github.com/NousResearch/hermes-agent/pull/72812) | fix: show update banner on fork-based deployments (#72789) | Opened 2026-07-27; updated 2026-08-03 | `webtecnica`, `CONTRIBUTOR` | `teknium1` keep-open review rejects SHA mismatch as an exact `1 behind`, synchronous startup network I/O, silent lookup failure, and unrelated docs | 4 files, +286/-145 | Very high in `banner.py` and update-check tests | Medium-low pending focused rework |

## Notes on the most relevant upstream work

This local patch implements the narrow configured-canonical-remote contract requested by #72789 and the reviews on #38344/#72812, while preserving the current shallow-clone and official-SSH safeguards. Unlike #72812, it keeps exact commit counts when local history is available instead of turning any SHA mismatch into a false `1 behind`. Unlike #38344, it validates the remote URL rather than trusting any remote merely named `upstream`. Unlike #63912, it does not expand into update application, branch healing, dashboard history, or Electron behavior.

The local patch does not solve every concern in #72789: failed lookups remain silent, and desktop/dashboard sibling paths remain upstream work. That boundary is deliberate for this patch—the requested TUI/banner status is corrected without widening update/install semantics.

## Recommendation

Keep `feb00ce956` as a narrow local patch until upstream merges an equivalent canonical-remote selector that preserves exact counts, shallow-clone behavior, official-SSH noninteractive behavior, and legacy-cache invalidation. Recheck #38344, #63912, and #72812 during every rebase. If one lands with equivalent banner behavior, drop this patch rather than carrying a competing implementation; retain only any still-missing cache or banner-state regression.

## Raw search queries used

- `repo:NousResearch/hermes-agent is:open banner update check fork origin upstream`
- `repo:NousResearch/hermes-agent is:open "origin/main" banner`
- `repo:NousResearch/hermes-agent fork install update status`
- `repo:NousResearch/hermes-agent canonical remote detection`
- `repo:NousResearch/hermes-agent fork banner`
- `repo:NousResearch/hermes-agent upstream remote`
- `repo:NousResearch/hermes-agent is:pr is:open banner origin`
- `repo:NousResearch/hermes-agent is:pr is:open update check fork`

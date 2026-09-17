# Recalled-memory provenance

- Date: 2026-07-18
- Repo: `/opt/hermes-agent`
- Patch ref: `e51bcd26c` (reviewed) → `a620386b2` (pre-2026-08-09 active) → `989ac31b25` (pre-2026-08-14 active) → `f6f5d4810d` (pre-refresh active) → `1c078e3e06` (pre-2026-08-23 active) → `cc336cac0b` (pre-final-refresh active) → `81ba50b980` (pre-2026-08-27 active) → `26f055d1d9` (pre-final-refresh active) → `4a46b91b03` (pre-final-refresh-2 active) → `3d2ac62347` (pre-2026-08-31 active) → `82a5516588` (pre-2026-09-05 active) → `5688b53c4d` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch; this catalogue pass modifies only `peter/patch-catalog/` (an unrelated pre-existing `package-lock.json` worktree modification remains untouched).
- Motivation:
  - Hindsight returns `mentioned_at`, but Hermes previously discarded it from automatic and explicit recall output.
  - Peter needs one consistently bracketed compact provenance format whenever timestamp, source, or session metadata exists, with session labels that remain traceable without unnecessary full-ID noise.
  - Recalled memory should be framed as dated historical context and only surface a conflict when it materially affects the answer and cannot be verified.
- Changed files: `plugins/memory/hindsight/__init__.py`; `tests/plugins/memory/test_hindsight_provider.py`; `tests/plugins/memory/test_hindsight_recall_format.py`.
- Tests / verification: focused Hindsight suite: 154 passed; live local API format probe passed; `py_compile` and `git diff --check` passed. Timestamp/provenance tests cover ISO `Z`, UTC-offset normalization, naïve-UTC fallback, malformed fallback, indexed explicit-recall output, collapsed source-only/profile/session bracket provenance, all unique session suffixes, deliberate colliding-suffix collapse, and duplicate suffix suppression. Full suite was blocked at collection by a missing ACP package; excluding ACP emitted existing unrelated logging failures and timed out.

## Local patch summary

The patch adds `_recall_timestamp_label()` to safely parse a result's optional `mentioned_at` ISO timestamp, normalize it to UTC, and format it as `YYYY-MM-DD HH:MMZ`. `_recall_session_labels()` emits each unique `session:` suffix in encounter order as `s:<suffix>`, deliberately collapsing colliding suffixes rather than expanding either to a full ID. The suffix is a compact locator, not a unique source key; profile/timestamp context and session lookup disambiguate rare collisions. `_format_recall_result()` uses one collapsed bracket format whenever any timestamp, source/profile, or session provenance exists, such as `[2026-07-17 21:48Z · profile:default · s:c2438c · s:otherid]`; it emits bare text only when no provenance exists. This shared formatter covers both automatic prefetch context and the explicit recall tool.

The default preamble now says the injected material is dated historical context, documents bracket fields as UTC timestamp, profile, and `s:<short-session-id>` when available, explains that the timestamp records when Hindsight encountered a statement rather than necessarily when a fact became true, directs the agent to prefer newer evidence and verify exact/current details, and limits conflict callouts to material, unverified conflicts.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---:|---|---|---|---|---|
| PR | [#60716](https://github.com/NousResearch/hermes-agent/pull/60716) | `feat(hindsight): preserve recall metadata with configurable output format` | created 2026-07-08; updated 2026-07-12 | `hejp001`; association `NONE`; authenticated merged-PR search found 0 prior merged PRs | `teknium1` automated review: keep open, salvageability **medium**; asks for optional-field guards, text-only/populated-result tests, and preserving/migrating the string contract | 2 files, +154/-13; directly changes `plugins/memory/hindsight/__init__.py` (plus unrelated QQ adapter) | **Very high**: same result serialization path and `mentioned_at`/metadata goal; direct hunk and semantic overlap | **Medium**: active but GitHub reports `mergeable=false`, `dirty`; reviewer identified concrete safety/compatibility gaps |
| PR | [#31743](https://github.com/NousResearch/hermes-agent/pull/31743) | `feat(hindsight): surface recall provenance metadata` | created 2026-05-25; updated 2026-07-13 | `davidrobertson`; association `CONTRIBUTOR`; authenticated merged-PR search found 0 prior merged PRs | `teknium1` automated review: keep open, salvageability **medium**; requests removal of new behavioral `.env` settings in favor of config and notes it is conflicting with main | 4 files, +317/-3; changes Hindsight provider, README, tests, and memory-provider docs | **Very high**: same Hindsight formatter/automatic+explicit recall paths and provenance concept | **Medium**: feature premise is supported, but the branch is conflicting and needs configuration-surface cleanup |
| PR | [#23933](https://github.com/NousResearch/hermes-agent/pull/23933) | `fix(hindsight): frame recalled memories as external evidence` | created 2026-05-11; updated 2026-07-13 | `EndeavorYen`; association `NONE`; authenticated merged-PR search found 0 prior merged PRs | `teknium1` automated comment: keep open, salvageability **medium**; asks for all user-facing docs to be updated and recommends replaying the small substitutions because the PR is not mergeable | 3 files, +41/-14; changes Hindsight provider, README, and provider tests | **Medium**: overlaps the default recall framing/preamble, not timestamp serialization | **Medium**: narrow premise remains relevant, but GitHub reports `mergeable=false` and documentation coverage is incomplete |

## Notes on most relevant upstream items

### #60716 — closest implementation overlap

This is the direct upstream analogue: it preserves Hindsight recall metadata and includes `mentioned_at` in the result formatting area. Its reviewer specifically found that direct optional-field reads can break existing text-only fixtures and that converting an established string result into a list changes the tool contract. The local patch already avoids those pitfalls by using `getattr`, returning only formatted strings, and adding timestamp-present plus legacy-fallback coverage. If #60716 lands after a salvage, compare its metadata options against this deliberately fixed compact format rather than replacing the local behavior wholesale.

### #31743 — broad provenance feature

#31743 also changes both automatic and explicit Hindsight recall output, but expands into configuration, README, website documentation, and a larger opt-in provenance surface. It is a direct mechanical conflict risk in the same plugin but is not an equivalent replacement until it preserves the local timestamp/preamble semantics without adding behavioral environment variables contrary to the reviewer guidance.

### #23933 — framing-only adjacent work

#23933 is relevant because it treats recalled memory as external evidence, which aligns with this patch's historical-context guidance. It does not supply the requested `mentioned_at` timestamp formatting. Its default-preamble edits will need a semantic merge if rebased or landed upstream.

## Recommendation

Keep `e51bcd26c` as the compact provider-local provenance patch. Watch #60716 and #31743 closely: both are open, same-file, high-conflict provenance work, but neither is currently cleanly mergeable and both have medium-salvageability reviewer feedback. On rebase or an upstream landing, preserve the local safe optional-field fallback, string output contract, UTC timestamp semantics, unified bracketed provenance when any data exists, all-unique-session suffix rendering with deliberate collision collapse, and material-conflict-only framing; merge #23933 only for compatible evidence-boundary wording.

## Raw search queries used

Authenticated as `kidroca` with `gh` on 2026-07-18:

- `repo:NousResearch/hermes-agent is:open "mentioned_at"`
- `repo:NousResearch/hermes-agent is:open "preserve recall metadata"`
- `repo:NousResearch/hermes-agent is:open "surface recall provenance metadata"`
- `repo:NousResearch/hermes-agent is:open hindsight recall metadata`
- `repo:NousResearch/hermes-agent is:open hindsight provenance`
- Targeted authenticated API views for PRs #60716, #31743, and #23933: issue/pull metadata, changed files, reviews, comments, and author merged-PR searches.

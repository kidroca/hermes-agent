# Preview explicit Hindsight retain content

- Date: 2026-07-18
- Repo: `/opt/hermes-agent`
- Patch ref: `e0284f334` (reviewed) → `f53b34553` (pre-2026-08-09 active) → `3cf6f6d9c1` (pre-2026-08-14 active) → `d7aa5bf32f` (pre-refresh active) → `df8b8f22bf` (pre-2026-08-23 active) → `57df878a9f` (pre-final-refresh active) → `0967068348` (pre-2026-08-27 active) → `50f0321b5c` (pre-final-refresh active) → `2b26809fba` (pre-final-refresh-2 active) → `8c16fb3406` (pre-2026-08-31 active) → `0c2db8b397` (active)
- Branch: `peter/hermes-patches`
- Local status: committed patch; this catalogue pass modifies only `peter/patch-catalog/` (an unrelated pre-existing `package-lock.json` worktree modification remains untouched).
- Motivation:
  - Explicit `hindsight_retain` calls already contain the generated memory text, but the compact tool row previously hid it.
  - Peter wanted that existing content visible without an extra summary/model call and without duplicating it in the final response.
  - Retain previews must force-redact recognized secrets before reaching display surfaces, analogous to `browser_type`.
- Changed files: `agent/display.py`; `tests/agent/test_display.py`.
- Tests / verification: `/opt/hermes-agent/.venv/bin/python -m pytest tests/agent/test_display.py -q -o 'addopts='` (`60 passed`); `py_compile` and `git diff --check` passed. The focused test was observed true-red before implementation and green afterward; independent review found no blockers, privacy regressions, or material test gaps.

## Local patch summary

The patch maps `hindsight_retain.content` into the existing `build_tool_preview()` primary-argument path, so `build_tool_label()` and the compact tool row expose the already-generated retain text through the normal one-line/truncation behavior. It does not invoke another model, create a separate summary, or alter the final response.

Before preview construction, `redact_tool_args_for_display()` copies explicit Hindsight retain arguments and applies forced secret-pattern redaction to `content`, matching the established `browser_type` display boundary. Tests cover ordinary retain content, recognized-secret redaction, and the final friendly tool label.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| PR | [#62344](https://github.com/NousResearch/hermes-agent/pull/62344) | `fix(memory): redact Hindsight retain payloads` | created 2026-07-10; updated 2026-07-12 | `2bf`; association `NONE`; authenticated search found 0 prior merged PRs | `teknium1` automated review: keep open, salvageability **high**; endorses forced redaction across retain paths | 2 files, +181/-6; Hindsight provider and provider tests, not display code | **Low mechanical / medium semantic**: same retain-content privacy boundary, but #62344 redacts outbound provider payloads while this patch redacts only displayed arguments | **Medium-high**: mergeable but blocked; reviewer strongly supports the hardening premise |
| PR | [#28719](https://github.com/NousResearch/hermes-agent/pull/28719) | `feat(display): declarative tool-preview schema to eliminate per-tool hardcoding (#28621)` | created 2026-05-19; updated 2026-07-13 | `xxxigm`; association `CONTRIBUTOR`; authenticated search found 42 prior merged PRs | `teknium1` automated review: keep open, salvageability **high**; design fit is good but formatter exception handling needs correction | 4 files, +468/-0; directly changes `agent/display.py` and `tests/agent/test_display.py` | **Very high mechanical**: refactors the same hardcoded preview map and tests; could absorb this retain mapping into declarative metadata | **Medium**: strong premise and author history, but currently conflicting/dirty and still needs requested fixes |
| Issue | [#28621](https://github.com/NousResearch/hermes-agent/issues/28621) | `feat(display): declarative tool preview schema to eliminate per-tool hardcoding` | created/updated 2026-05-19 | `zccyman`; association `CONTRIBUTOR` | No maintainer comment; implementation PR #28719 received a positive high-salvageability review | Design proposal; no changed files | **High architectural**: explicitly targets the structural hardcoding extended by this local patch | **Unknown**: open design issue with an active but conflicting implementation PR |
| PR | [#10661](https://github.com/NousResearch/hermes-agent/pull/10661) | `fix(display): hide browser_type text in tool previews` | created 2026-04-16; updated 2026-07-12 | `cloudyun888`; association `NONE`; authenticated search found 0 prior merged PRs | `teknium1` automated review: keep open, salvageability **low**; says normal text is intentionally readable and pattern-based redaction is the current contract | 2 files, +8/-0; directly changes `agent/display.py` and `tests/agent/test_display.py` | **Medium mechanical / high policy relevance**: same preview/redaction functions, but proposes hiding all text rather than preserving readable non-secrets | **Low** as written: mergeable but blocked, and reviewer requests a broader policy rework |

## Notes on most relevant upstream items

### #62344 — closest privacy overlap

This PR confirms that retain content can contain secrets and that forced redaction is appropriate, but its scope is materially different: it sanitizes content sent to Hindsight itself. The local patch must not adopt that outbound mutation accidentally; its contract is display-only redaction while retaining the original content for the provider. The files do not overlap, so conflict risk is primarily semantic rather than mechanical.

### #28719 / #28621 — closest display architecture overlap

The local patch necessarily adds one entry to the hardcoded primary-argument map. #28621 identifies that map as a recurring oversight source, and #28719 replaces it with declarative preview metadata. If that work lands, expect direct conflicts in both changed local files and migrate `hindsight_retain` to the upstream registration mechanism while preserving forced display redaction and the no-extra-model-call behavior.

### #10661 — useful redaction-policy analogue

The reviewer rejects blanket hiding of normal `browser_type` text and explicitly preserves pattern-based redaction as the current contract. That supports the local patch's choice to show ordinary retain text while force-redacting recognized credentials. #10661 is not an equivalent implementation and should not replace the local behavior.

No open issue or PR found by the narrow authenticated searches implements the exact product behavior: showing existing explicit `hindsight_retain.content` in the compact tool row without an additional summary/model call or duplicate final response.

## Recommendation

Keep `e0284f334` local. Watch #28719/#28621 closely because an upstream declarative-preview migration will conflict directly with the two local files; port the retain preview into that schema if it lands. Treat #62344 as supporting privacy evidence, not a replacement: preserve the distinction between outbound retain payloads and display-only argument redaction. Retain ordinary-text visibility, forced recognized-secret redaction, normal preview truncation, and the no-extra-call/no-duplicate-response contract.

## Raw search queries used

Authenticated as `kidroca` with `gh` on 2026-07-18:

- `repo:NousResearch/hermes-agent is:open hindsight retain preview`
- `repo:NousResearch/hermes-agent is:open "hindsight_retain" display`
- `repo:NousResearch/hermes-agent is:open "tool preview"`
- `repo:NousResearch/hermes-agent is:open build_tool_preview`
- `repo:NousResearch/hermes-agent is:open retain content compact tool row`
- Targeted authenticated API views for PRs #62344, #28719, and #10661 and issue #28621: issue/pull metadata, changed files, reviews, comments, merge state, and author merged-PR searches.

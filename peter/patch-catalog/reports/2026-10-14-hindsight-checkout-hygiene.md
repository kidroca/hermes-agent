# Keep personal Hindsight routing out of the shared tree

- Date: 2026-10-14 (Europe/Sofia)
- Repo: `kidroca/hermes-agent`
- Patch ref: `94998ef764236b7fb532d93f85b68e85916f142b`
- Branch: `peter/hermes-patches`
- Local status: approved fork-publication preparation; no service restart or memory-bank migration
- Motivation: a personal bank ID is account-local configuration. Collaborators may use different banks or backends; tracked configuration must not impose Peter's selection on them.
- Changed files: `.gitignore`, removal of tracked `.hindsight/config.toml`
- Tests / verification: `git check-ignore -v .hindsight/config.toml` matches root `/.hindsight/`; `git ls-files -- .hindsight` is empty. Local configuration is preserved byte-for-byte. Diff checks pass. Discord source is unchanged by this hygiene commit.

## Local patch summary

Commit `255404440a` accidentally tracked the personal override. The separate corrective commit removes it from the index while retaining the operator's local file and ignores the entire root `.hindsight/` directory. History is preserved rather than rewritten; the earlier personal bank identifier remains in history and is not a credential. There is no provider API/config migration or source change.

New repositories require a local `.hindsight/` plus the root ignore rule. Linked worktrees do not inherit ignored files: copy the project's local configuration explicitly, preserve its bank identity and never overwrite a destination configuration. Trust must cover the worktree's own location; trust in the main repository is not inherited.

## Upstream overlap

| Kind | # | Title | Age | Author signal | Maintainer signal | Files/size | Conflict risk | Merge likelihood |
|---|---:|---|---|---|---|---|---|---|
| Local checkout hygiene | — | Personal Hindsight bank routing | — | Peter's explicit policy | Not an upstream provider proposal | Root ignore rule and index removal only | Low; possible adjacent `.gitignore` edits | N/A |

## Notes on most relevant upstream items

No upstream implementation is needed to justify removing personal configuration from the shared repository. The separate proposed core cwd-plumbing patch is paused and is not part of this publication. No claim of exhaustive upstream search is made for this operator-only correction.

## Recommendation

Keep the local ignore policy. Never restore a tracked personal override for worktree convenience. Shared bank configuration requires explicit agreement, not a default repository setup action. Other projects identified in the audit are outside this cleanup's scope.

## Raw search queries used

Local `git show`, `git diff`, `git check-ignore` and `git ls-files` only; no additional upstream query needed for the local routing policy.

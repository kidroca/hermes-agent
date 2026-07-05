# Hermes Agent local patch catalogue

| Date | Patch ref | Title | Branch | Report | Upstream risk | Recommendation |
|---|---|---|---|---|---|---|
| 2026-07-05 | `688174f58` | fix: preserve kanban completion artifacts | `peter/hermes-patches` | [Preserve Kanban completion artifacts](reports/2026-07-05-688174f58-kanban-completion-artifacts.md) | High overlap with open Kanban artifact PRs #55903, #39777, #56685 | Watch #55903/#56685; drop/rebase local patch when upstream lands |
| 2026-07-05 | `06bd27472` | fix: disable kanban worker memory autoprefetch by default | `peter/hermes-patches` | [Disable Kanban worker memory autoprefetch](reports/2026-07-05-06bd27472-kanban-memory-autoprefetch.md) | Medium-high overlap with memory governance #45743 and worker env changes #55600 | Keep local patch; watch #45743/#55600 and port into upstream memory governance if it lands |

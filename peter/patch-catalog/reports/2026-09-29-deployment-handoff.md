# September 29 deployment handoff

Supersedes deployment-preparation status in the reconciliation report; historical code/test receipts remain valid.

- Hermes functional candidate: `07c1171063f931f84088ed8724a836ce4cce1089`, based on upstream `09581cacaa8db3b3241dbbabe76a351a2ce14f60`.
- External personal plugin: `kidroca/hindsight`, branch `peter/hermes-hindsight`, exact published pin `4899f188e2c7be1fb00b12cf0a3e7e2bf0283859`, subdirectory `hindsight-integrations/hermes`.
- Upstream routing PR: https://github.com/vectorize-io/hindsight/pull/4940; checked CI green at `188f451994740ec8a28d68a71d5e8f0e084d77bb`. Personal missions/notices remain outside that PR.
- Routing uses stock Hermes scoped context; only optional structured-notice callbacks remain as a local Hermes memory bridge. Independent review found no blockers in its reduction. Focused canonical tests: 89 passed.
- Personal plugin recovery fix explicitly requests synchronous manual retention. Parent inspected the one-line production correction and independently reran the full candidate integration suite: 48 passed. Earlier full plugin unit suite: 82 passed.
- Pinned plugin code and non-catalog install metadata pre-staged for default, clerk, coding, designer, incept-agent, lad-studio and lawyer. Parent independently verified all 22 files per home, exact pin metadata, provider discovery, and automatic catalog migration skip. No provider initialization/API writes were performed in verification.
- Staging script and instructions: `/home/kidroca/.hermes/update-handoff/`; metadata rollback journal retained there. The other machine must pre-stage before updating if still using the bundled provider.
- Live `/opt/hermes-agent`, its dependencies and profile configuration/data remain unchanged. Actual updater dependency admission, live memory operation and Doctor remain post-update gates, not completed verification.

Publication uses the frozen fork lease `0592565e2be2f1659b0844efe74e5569c6d69ef4`; the coordinator must verify exact remote readback before handing off the updater command.

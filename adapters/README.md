# Agent Adapters (Layer 4)

Adapters bind agents to the agent-independent Core and Workflows. They execute
Core; they never define a second copy of it (`VCPS-CORE-003`).

| Adapter | Scope | Status |
|---------|-------|--------|
| [claude-code](claude-code/README.md) | `/vcps-setup` (SETUP), `/vcps` (intent classification/escalation), and all seven non-SETUP workflows (`/vcps-audit`, `/vcps-review`, `/vcps-bug`, `/vcps-tiny`, `/vcps-feature`, `/vcps-hotfix`, `/vcps-release`) | Reference draft; SETUP, FEATURE, and REVIEW have bounded live evidence; router dispatch and the other five workflows lack live acceptance |
| [codex](codex/README.md) | `vcps-setup`, `vcps` router, and all seven non-SETUP workflows | Reference draft; all nine skills structurally tested, with bounded read-only fixture/handoff evidence; no full live skill-loading/workflow acceptance |

A general `/vcps` router exists as a reference draft (Claude Code only):
it classifies a request into one of the eight workflow intents and checks
it against mechanical risk-escalation signals
(`standard/risk-model.md` `VCPS-RISK-041/045`). As of roadmap Phase D's
completion, all seven non-`SETUP` workflow executors it can route to
exist — `/vcps-audit`, `/vcps-review`, `/vcps-bug`, `/vcps-tiny`,
`/vcps-feature`, `/vcps-hotfix`, and `/vcps-release`. See
[`../standard/VCPS.md` §4](../standard/VCPS.md#4-architecture-and-layering)
and `standard/open-questions.md` `OQ-011`.

A second agent (Codex) now has a reference skill for every workflow,
built from official OpenAI documentation rather than assumed parity
with Claude Code's mechanisms. The capability mapping discloses that
Codex's default sandbox may permit in-workspace mutation without a
per-file prompt. See `adapters/codex/references/capability-mapping.md`,
`evaluation/codex-adapter.md`, and `standard/open-questions.md` `OQ-012`.

All eighteen workflow skills in both adapters reference the shared
[`UNTRUSTED-CONTENT.md`](UNTRUSTED-CONTENT.md) policy before inspecting
target-controlled content. Copy-based installations must preserve the
relative layout documented in each adapter README.

## Installing an adapter

For direct installation from the public GitHub repository, use
[`QUICKSTART.md`](../QUICKSTART.md). Run its terminal command for the
animated agent and scope selector, or use `--adapter` for non-interactive
project/user installation.

`adapters/install.py` (Phase K, `evaluation/completion-roadmap.md`)
automates the manual symlink/copy procedure each adapter README
documents, for either adapter:

```
adapters/install.py --adapter claude-code --target <repo> [--mode copy|symlink] [--vendor-core]
adapters/install.py --adapter codex --target <repo>
adapters/install.py --adapter codex --global
adapters/install.py --adapter claude-code --global
```

It installs the chosen adapter's skill set (plus `vcps-audit`/
`vcps-review`/`vcps-bug`'s shared `lib/` sibling for Claude Code, and the
`adapters/claude-code/lib`+`vcps-setup/scripts` subtree Codex's own
skills hard-code a path to — a disclosed workaround, not a clean install;
see `adapters/codex/README.md`), verifies every installed file is
byte-identical to its source, and — for Claude Code with `--vendor-core`
— vendors a pinned `standard/`/`workflows`/`templates`/`VERSION` copy
into `<target>/.vcps-core/`, which `vcps-setup/references/core-discovery.md`'s
resolution order now checks before falling back to a dev-mode checkout.
It makes no Core judgment of any kind (no mode detection, no risk rating)
and performs no mutation beyond installing these known file sets —
see `adapters/tests/run_tests.py` for its own test coverage.

Codex can also be installed at user scope with `--global`: skills go to
`~/.agents/skills/`, and the matching Core/helper source tree goes to
`~/.agents/vcps-source/`. This makes the skills discoverable in any
project for that OS user; each workflow still acts on the current project
when invoked. The installer refuses to overwrite existing global paths.

Claude Code supports the same user scope: skills go to `~/.claude/skills/`
and the shared untrusted-content policy goes to `~/.claude/`. Project-specific
Core discovery still runs from the project where Claude Code is started.

The `0.1.0`→`0.2.0` project-schema migration `templates/contract.md`
describes in prose is mechanized as
`adapters/claude-code/vcps-setup/scripts/vcps_tool.py migrate-project-schema
--target <repo>`: it adds the three new `installation` fields, records a
`config_history` event, and never fabricates historical `stage_events` —
a subsequent real `/vcps-setup` `UPGRADE` run reconstructs stage
completion for real. This subcommand is mutating and is deliberately
never pre-approved in any skill's `allowed-tools`, the same discipline as
`atomic-write`.

Before changing the project, the migration saves the original bytes and
their digest under `.vcps/project.yaml.0.1.0.bak`. If the migrated file has
not changed since then, restore it with
`vcps_tool.py rollback-project-schema --target <repo>`. Rollback refuses to
overwrite edits made after migration and is also a mutating command that is
never pre-approved.

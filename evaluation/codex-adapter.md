# Evaluation record: Codex adapter

- Adapter version: `0.1.0-draft.2` (`adapters/codex/VERSION`)
- VCPS Core: `0.1.0-draft`; project schema `0.2.0`; layout `0.1.0`
- Date: 2026-10-06
- Roadmap Phase F, all nine components coded and structurally tested

## Scope and evidence

The Codex adapter contains the nine workflow skills: `vcps-setup`,
`vcps` (routing), `vcps-audit`, `vcps-review`, `vcps-bug`, `vcps-tiny`,
`vcps-feature`, `vcps-hotfix`, and `vcps-release`. Each has Codex skill
frontmatter and `agents/openai.yaml` disabling implicit invocation.
Their workflow semantics defer to the authoritative `workflows/*.md`
and Core gate documents. They reuse the agent-independent Python helpers
in `adapters/claude-code/` by direct path; no helper was copied or forked.

The capability mapping was refreshed against official OpenAI Codex skill
and subagent documentation on 2026-10-06. The official skill guide
documents repository discovery under `.agents/skills`, required
`SKILL.md` name/description fields, and `agents/openai.yaml` invocation
policy. The official subagent guide documents independent subagent
workflows in Codex CLI. Sources are recorded in
`adapters/codex/references/capability-mapping.md`.

Codex CLI 0.160.0 is installed. Attempts to inspect prompt input and
start an ephemeral read-only run failed before skill loading because the
in-process app-server could not write in this environment's read-only
filesystem. An escalated ephemeral `vcps-audit` run was rejected by
automatic review because it could transmit linked repository contents
to an external model service and write local state. That action was not
retried through another route. Separately, the Phase J record documents a
later live, read-only Codex CLI pass over the synthetic-commerce fixture;
that demonstrates fixture-state consumption, not general skill loading or
workflow execution. This adapter's skill suite remains `STRUCTURAL_TEST`
only, with no adapter-specific `SIMULATED_EXECUTION` and no evidence that
Codex executed a complete workflow. Sandbox/approval semantics remain
unverified for mutation in a running session. See
`evaluation/phase-j-acceptance.md` for the bounded live-read evidence.

## Structural test

Command: `python3 adapters/codex/tests/run_tests.py`

The suite covers the pilot setup skill and the full skill set:

| Checks | Coverage | Class |
|---|---|---|
| S1–S5 | Adapter docs exist, disclose informative/non-Core status, retain unresolved capability gaps and no-live evidence | STRUCTURAL_TEST |
| S6–S12 | Setup skill frontmatter, Codex-specific policy boundaries, helper paths and references | STRUCTURAL_TEST |
| S13–S18 | OpenAI metadata YAML, example rule semantics, version, official-source URLs | STRUCTURAL_TEST |
| S19–S24 | All nine skill directories, valid `name`/`description`, no Claude-only frontmatter, implicit invocation disabled, shared helper dependencies resolve, mutation boundary documented, README lists full scope | STRUCTURAL_TEST |
| S25 | All eight ported skills retain workflow-specific safety, escalation, and exit rules | STRUCTURAL_TEST |
| S26 | Helper-using skills distinguish the VCPS source root from the target repository and pass `--target` explicitly | STRUCTURAL_TEST |

The required result is 26/26 passing. This proves file shape and
references, not runtime loading, intent classification quality, command
approval behavior, or successful workflow execution in Codex.

## Capability gaps preserved in the adapter

- Codex skills cannot scope filesystem or command permissions per skill.
  The `agents/openai.yaml` policy disables implicit invocation; it does
  not enforce the sandbox or approval mode.
- Codex's default sandbox/approval combination may permit ordinary
  in-workspace writes without a per-write prompt. Mutating skill files
  require `approval_policy = "untrusted"` or a trusted rules policy for
  the intended command boundary before proceeding.
- The Codex helper paths depend on `adapters/claude-code/` remaining in
  the repository. A neutral shared-helper package and installer remain
  future work.
- A direct general-purpose checkpoint question mechanism was not
  established by the official material reviewed; skills must stop in
  conversation and wait for the user's reply when a checkpoint is due.

## Phase F outcome

All nine Codex-side workflow components now exist and have structural
coverage. Phase F is closed at `CODED` / `TESTED_STRUCTURALLY`.
Runtime behavior remains unverified until an actual Codex CLI session is
available. Cross-agent continuation evidence belongs to Phase G.

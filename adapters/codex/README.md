# Codex adapter

Reference/development-phase adapter binding OpenAI Codex CLI to VCPS,
distributed directly from the public GitHub repository by `install.sh`.
Roadmap Phase F: nine workflow skills covering setup, routing, and all
seven other intents. This is structurally tested. Bounded live Codex CLI
read-only fixture use and cross-agent handoff are recorded, but no full
live skill-loading/workflow acceptance is established. This is not a
package-manager distribution.

- Adapter version: `0.1.0-draft.2` (this file's directory, `VERSION`)
- VCPS Core: `1.0.0`; project schema `0.2.0`; layout `0.1.0`
- Built from current official OpenAI Codex documentation fetched
  2026-10-06 (`developers.openai.com/codex`, redirecting to
  `learn.chatgpt.com/docs/...` — see
  `references/capability-mapping.md` for every source cited). Codex CLI
0.160.0 was installed. Initial skill-loading attempts could not complete:
the in-process app-server initialization failed under that environment's
read-only filesystem, and an escalated smoke run was rejected because it
could transmit linked repository contents externally and write local state.
Later bounded read-only fixture and cross-agent handoff runs succeeded, but
they do not establish full skill loading or workflow execution. See
`evaluation/codex-adapter.md` and `evaluation/phase-j-acceptance.md`.

## Scope

The nine skills map directly to `workflows/setup.md`, `workflows/README.md`
intent routing, and `workflows/{audit,review,bug,tiny,feature,hotfix,release}.md`.
Each uses Codex `SKILL.md` frontmatter and an `agents/openai.yaml` policy
to disable implicit invocation. The underlying workflows remain the
authority; skills carry only the agent-specific operating instructions
and mechanical helper references.

## A deliberate cross-adapter sharing decision

Skills invoke agent-independent helpers from
`adapters/claude-code/vcps-setup/scripts/vcps_tool.py`,
`adapters/claude-code/vcps-router/scripts/vcps_router.py`, and
`adapters/claude-code/lib/vcps_evidence.py` directly, rather than
vendoring duplicates. These helpers implement shared VCPS mechanics and
return facts; they do not make workflow judgments. This keeps one
implementation of each algorithm, with the disclosed installation cost
that `adapters/claude-code/` must be present.
`adapters/install.py --adapter codex` (Phase K, closed 2026-10-07)
vendors that exact subtree into the target as a disclosed workaround for
this cost, not a fix to it; a neutral shared location remains follow-up
work.

## Known limitations

- **No full live skill/workflow acceptance.** A bounded read-only Codex CLI
  pass consumed the synthetic-commerce fixture, and a separate handoff
  evaluation demonstrated cross-agent record continuation. These do not
  establish general skill loading or complete workflow execution. The
  capability claims in `references/capability-mapping.md` remain
  `STATIC_INSPECTION` of documentation, with several rows explicitly
  `UNVERIFIED` where documentation was ambiguous or silent (exact
  manual-invocation-control file location/name; whether a general
  checkpoint-question primitive exists).
- **No per-skill mutation pre-approval scoping exists in Codex** the way
  Claude Code's `allowed-tools` provides it — see the capability mapping's
  "Capability gaps" section. This skill's own instructions tell the
  operator to configure `approval_policy = "untrusted"` or a
  `.codex/rules/*.rules` entry before relying on it for mutation; it does
  not claim Claude-adapter-equivalent safety under Codex's own defaults.
- Skill discovery, mutation approval, and complete Codex workflow behavior
  have not been live-tested. Evidence for those claims is documentation
  inspection and structural tests, plus the bounded read-only fixture and
  handoff evaluations described above.
- `adapters/install.py --adapter codex --target <repo>` (Phase K, closed
  2026-10-07) installs every skill under the target repository's
  `.agents/skills/<skill-name>/` directory per current Codex skill
  discovery documentation, also vendoring the
  `adapters/claude-code/{lib,vcps-setup/scripts}` subtree these skills
  hard-code a path to (see "A deliberate cross-adapter sharing decision"
  above — this is a disclosed workaround for that cost, not a fix to it)
  and copying `adapters/UNTRUSTED-CONTENT.md` to
  `.agents/UNTRUSTED-CONTENT.md`. It only ever copies known file sets and
  verifies the result byte-identical; see `adapters/tests/run_tests.py`.
- `adapters/install.py --adapter codex --global` installs the skills under
  `~/.agents/skills/` and a matching VCPS source tree under
  `~/.agents/vcps-source/`, making them available across projects for the
  current OS user. Global installation still requires the operator to
  configure Codex's sandbox/approval policy before running mutating stages.
- Each skill loads the shared trust-boundary policy before inspecting target
  content.
- Keep a complete VCPS source tree available to the session: workflow
  files and helper scripts are read/run from that tree, which may be
  separate from the target repository. Pass the target repository path
  to each helper's `--target`; do not assume the target repository is
  also the VCPS source root. The adapter currently depends on the
  `adapters/claude-code/` helper files being present in that source tree.

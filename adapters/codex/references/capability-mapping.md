# Capability mapping (Codex adapter — informative)

This document resolves `OQ-012` in `standard/open-questions.md`: how
VCPS's agent-independent orchestration concepts map onto OpenAI Codex
CLI's actual execution primitives, as a second data point alongside the
Claude Code adapter's existing mapping (`OQ-005`,
`adapters/claude-code/vcps-setup/references/orchestration.md`).

**This mapping is adapter-layer, not Core.** Per `standard/VCPS.md`
`VCPS-CORE-001`, nothing here creates a new Core requirement, and this
repository's own mission explicitly requires consulting *current
official* OpenAI documentation before assuming any Codex capability
rather than assuming Claude-specific primitives exist. Every claim below
is sourced; where the source was ambiguous or silent, that is stated
explicitly rather than filled in by assumption.

**Research method and its limits.** This mapping was refreshed from
official OpenAI Codex documentation on 2026-10-06, including current
skill discovery, metadata policy, and subagent guidance. Codex CLI
0.160.0 is installed here, but attempted runtime inspection failed
before skill loading because its in-process app-server could not write
under this environment's read-only filesystem. An escalated ephemeral
smoke run was rejected by automatic review because it could transmit
linked repository contents to an external model service and write local
state. No `LIVE_ADAPTER_EXECUTION` evidence was obtained. Claims below
are `STATIC_INSPECTION` only; where official documentation does not
establish behavior, the gap remains explicit.

## Mapping table

| VCPS orchestration need | Claude Code mechanism (for comparison) | Codex CLI mechanism | Status |
|---|---|---|---|
| Project-neutral instruction/memory file | `CLAUDE.md` (implicit) | `AGENTS.md`, concatenated path-order from repo root down to cwd; `AGENTS.override.md` takes precedence per directory level | `STATIC_INSPECTION`, sourced: [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md) |
| Reusable, invocable skill with instructions + scripts + references | Claude Code Skill (`SKILL.md` + `scripts/`/`references/`/`assets/`) | Codex skill: same structural shape — a directory with required `SKILL.md` (`name`, `description` frontmatter) plus optional `scripts/`, `references/`, `assets/` | `STATIC_INSPECTION`, sourced: [Build skills](https://learn.chatgpt.com/docs/build-skills) |
| Skill install location | `.claude/skills/<name>` (symlink or copy) | Four scope levels: repo (`.agents/skills`, searched upward from cwd to repo root), user (`$HOME/.agents/skills`), admin (`/etc/codex/skills`), system (bundled) | `STATIC_INSPECTION`, sourced: same as above |
| Manual-invocation-only skill (never auto-triggered) | `disable-model-invocation: true` in `SKILL.md` frontmatter | Skill metadata at `agents/openai.yaml` with `policy: { allow_implicit_invocation: false }`; explicit `$skill-name` invocation still works | `STATIC_INSPECTION`, sourced: [Build skills](https://developers.openai.com/codex/skills/). Runtime behavior not live-tested. |
| Per-skill command/tool pre-approval scope (Claude's `allowed-tools`) | `allowed-tools:` glob patterns in `SKILL.md` frontmatter, scoped to that one skill | **No per-skill equivalent found.** Codex's closest mechanism, `.codex/rules/*.rules` (Starlark `prefix_rule(pattern=[...], decision="allow"|"prompt"|"forbidden")`), is **repository/user/admin-scoped, not skill-scoped** — a rule applies to every invocation of a matching command prefix regardless of which skill (or no skill) issued it. Project-local rules under `<repo>/.codex/rules/` load only once the repository is marked "trusted" by the user. | `STATIC_INSPECTION`, sourced: [Rules](https://learn.chatgpt.com/docs/agent-configuration/rules). **This is a genuine capability gap, not filled by assumption** — see "Capability gaps" below. |
| Mutation never pre-approved; every write visible to a human by default | No `Write`/`Edit` in any skill's `allowed-tools`; every mutation hits Claude Code's own per-call permission prompt | **Materially different by default.** `sandbox_mode = "workspace-write"` (the default for a version-controlled folder) permits file reads/writes/command execution *within the workspace* with **no per-file prompt**; `approval_policy = "on-request"` (the default) only prompts to *escape* the sandbox (network, files outside the workspace, destructive app/MCP calls) — not for an ordinary in-workspace file write. | `STATIC_INSPECTION`, sourced: [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security). **This is the single most consequential capability gap** — see below. |
| Stricter, per-write visibility (closer to Claude's default) | N/A (already the default) | Available but not default: `approval_policy = "untrusted"` ("asks for anything not on a known-safe list"), or a `.codex/rules/*.rules` entry marking a specific command `decision = "prompt"` | `STATIC_INSPECTION`, sourced: same as above plus [Rules](https://learn.chatgpt.com/docs/agent-configuration/rules) |
| Read-only / audit-style execution | Skill's `allowed-tools` omits `Write`/`Edit` entirely | `sandbox_mode = "read-only"` — blocks all file modification regardless of approval policy | `STATIC_INSPECTION`, sourced: [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| Human checkpoint (`AskUserQuestion`-style stop-and-ask) | `AskUserQuestion` tool | An approval prompt under `on-request`/`untrusted`/granular policy is a stop-and-ask for a *specific pending action*, not a general-purpose question tool; whether Codex has a direct `AskUserQuestion` analog for arbitrary checkpoint questions (not tied to a sandboxed action) was **not found in available documentation** | `STATIC_INSPECTION`; **open / UNVERIFIED** |
| Independence (`I2`): a distinct session/identity forms its own judgment before seeing the builder's reasoning | Subagent via `context: fork` | Codex CLI subagent threads can independently review evidence; instructions must explicitly withhold builder reasoning/artifacts beyond the review scope when independent judgment is required | `STATIC_INSPECTION`, sourced: [Codex Subagents](https://developers.openai.com/codex/subagents/). This documents subagent availability and operation, not a guarantee of information isolation; enforce the VCPS independence conditions in the task setup. |
| Deterministic mechanical helper script invocation | `Bash(${CLAUDE_SKILL_DIR}/scripts/tool.py <subcommand> *)` pre-approved per skill | Same shape of invocation (a `scripts/` script inside the skill directory, run via shell) is supported, but **without the per-skill pre-approval scoping noted above** — its execution is governed by the repo-wide sandbox/approval/rules layers, not anything the skill itself declares | `STATIC_INSPECTION`, sourced: [Build skills](https://learn.chatgpt.com/docs/build-skills) |
| Reusable prompt template (pre-skills mechanism) | N/A | Custom prompts (`~/.codex/prompts/*.md`, `$1`/`$ARGUMENTS`/`$FILE` placeholders) — **documented as deprecated in favor of skills** | `STATIC_INSPECTION`, sourced: [Custom Prompts](https://developers.openai.com/codex/custom-prompts). Not used by this adapter; skills are the current mechanism. |

## Capability gaps, stated honestly (not silently simulated)

Per `VCPS-CORE-003` ("Where an agent cannot perform a required activity,
the adapter MUST surface this as an `EVIDENCE_GAP` or a human checkpoint,
never as a silent skip") and this mission's own instruction to mark any
Core-required capability Codex lacks as a documented limitation:

1. **No per-skill mutation pre-approval scoping.** The Claude Code
   adapter's defense-in-depth design — a skill's `SKILL.md` never lists
   `Write`/`Edit` or the mutating helper subcommand in its own
   `allowed-tools`, so every mutation hits an ordinary, visible
   permission prompt *specific to that skill's invocation* — has no
   directly equivalent Codex mechanism. Codex's `.codex/rules/*.rules`
   is the closest analog, but it is repository-wide: a rule marking
   `vcps_tool.py atomic-write` as `prompt` applies to *any* invocation of
   that command by *any* skill or ad hoc request, not specifically to
   this adapter's own skill boundary. This is a real architectural
   difference, not a smaller version of the same mechanism.
2. **Default sandbox already permits in-workspace writes without a
   prompt.** Claude Code's default (prompt on every `Write`/`Edit` unless
   pre-approved) and Codex's default (`workspace-write` + `on-request`:
   writes inside the repo proceed without asking; only *escaping* the
   sandbox asks) are opposite defaults for the specific question "does
   an ordinary in-workspace mutation get a human's attention by
   default." A Codex-side VCPS adapter that wants Claude-adapter-
   equivalent per-mutation visibility MUST explicitly configure either
   `approval_policy = "untrusted"` or a `.codex/rules/*.rules` entry
   for the mutating subcommand — it does not get this by merely omitting
   something from a skill file, the way the Claude adapter does.
3. **No confirmed general-purpose checkpoint-question primitive.**
   Available documentation describes approval prompts tied to a specific
   pending sandboxed/destructive action, not a free-form "stop and ask
   the human a question" tool parallel to `AskUserQuestion`. A Codex
   `vcps-setup` skill needing an `HC-07`-style ambiguous-ownership
   question may have to phrase it as plain conversational text and wait
   for a reply, rather than a structured tool call — recorded here as an
   open question, not resolved by assuming one exists.
4. **Rules require a one-time "trusted" repository decision.**
   Project-local `.codex/rules/` only load once a human has marked the
   repository trusted — a step with no direct Claude Code equivalent
   (Claude's skill `allowed-tools` apply as soon as the skill file is
   read, with no separate repo-trust gesture). This is a human checkpoint
   this adapter cannot skip or simulate; it is documented for whoever
   installs this adapter to actually perform.

## What this means for the Codex adapter

Given gap 2 above, every mutating skill explicitly requires the operator
to establish `approval_policy = "untrusted"` or a trusted
`.codex/rules/*.rules` prompt rule covering the intended command before
mutation. `vcps-audit` requires `sandbox_mode = "read-only"`. These
instructions disclose the desired boundary; they do not enforce it.

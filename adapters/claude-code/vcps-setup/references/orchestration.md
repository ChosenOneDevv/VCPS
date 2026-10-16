# Orchestration mapping (Claude Code adapter — informative)

This document resolves `OQ-005` in `standard/open-questions.md`: how VCPS's
agent-independent orchestration concepts — discovery, file access, command
execution, checkpoints, evidence, state, resume, capability absence, and
failure — map onto *this specific agent's* execution primitives.

**This mapping is adapter-layer, not Core.** Per `standard/VCPS.md`
`VCPS-CORE-001`, Core/Workflows/Templates MUST NOT name a specific agent
mechanism. Nothing here creates a new Core requirement; it only explains
how the Claude Code adapter satisfies the capability list Core already
requires of any adapter (`workflows/setup.md` `VCPS-SETUP-067`) and the
checkpoint protocol (`standard/human-checkpoints.md`). A different adapter
(Codex or otherwise) MAY map these concepts differently, provided it still
satisfies `VCPS-SETUP-067` and `VCPS-CORE-003`. This document is
informative only, even though it lives next to normative skill
instructions.

## Mapping table

| VCPS orchestration concept | Claude Code primitive | Notes |
|---|---|---|
| Skill invocation / entry point | `/vcps-setup` Skill (`SKILL.md`, `disable-model-invocation: true`) | Manual invocation only — this skill is never auto-triggered by the model on its own judgment, because it can mutate a repository. |
| Repository discovery | Exact `Bash` invocations only: `git -c core.fsmonitor=false status --short --untracked-files=all`; `git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv`; bounded `log`; exact `rev-parse --show-toplevel`; `git -c core.fsmonitor=false ls-files`; `Glob`; `Read` | Wildcard Git argument patterns are intentionally absent; target-controlled fsmonitor is disabled for index/status/diff/log queries, and external diff/textconv are disabled for diff. Other Git invocations require normal permission approval. |
| Filesystem read | `Read`, `Grep`, `Glob` | Pre-approved via `allowed-tools` (read-only, no side effects to gate). |
| Filesystem write | `Write` / `Edit`, or the bounded helper (`scripts/vcps_tool.py`) for atomic multi-field `project.yaml` updates | **Deliberately NOT blanket-pre-approved** in `SKILL.md`'s `allowed-tools`. Each write goes through Claude Code's normal permission prompt, so a human sees and approves the exact write before it happens — this is independent, OS/tool-level reinforcement of the mutation-budget discipline in `workflows/setup.md VCPS-SETUP-052`, not a substitute for it. |
| Bounded command execution | `Bash`, restricted via exact safe Git invocations and specific `vcps_tool.py` read-only subcommands (`detect`, `inventory`, `plan-hash`, `validate`, `resume-status`, `fingerprint`) | A command outside these patterns prompts for permission like any other Bash call; the skill does not attempt to self-authorize arbitrary command execution. Compound/chained Bash commands have caused false permission denials in testing — `SKILL.md` instructs single commands per call. Invocation order is subcommand first, then `--target`/`--core` (`vcps_tool.py <subcommand> --target <path> ...`) — this matches the `allowed-tools` pattern shape and was corrected after a live run (2026-10-05) showed the flags-before-subcommand shape led to an invocation failure. |
| Evidence capture | `Bash` output captured into an evidence record written via `Write`/the helper | The command's stdout/stderr/exit code is the raw material; the *evidence record* (tier, result, method, revision, limitations) is authored by the model per `standard/evidence-model.md §4`, not auto-generated from exit code alone (`VCPS-EVD-022`). |
| Setup state persistence | `project.yaml` under `.vcps/`, written atomically by `scripts/vcps_tool.py` (write-temp-file, validate, rename) | State lives in the repository, never in the conversation. See "Resume" below. |
| Human checkpoint interaction | `AskUserQuestion` | Presents the exact action/scope/revision per `VCPS-HC-010`; the decision is then persisted as an approval record under `.vcps/approvals/` via `Write` — the `AskUserQuestion` answer itself is not the approval record, the persisted file is. |
| Resume | Re-invocation of `/vcps-setup` in a fresh or continued session; state is read from `.vcps/project.yaml`'s `installation.stage_events` journal, never from conversation history | Satisfies `standard/portability.md VCPS-PORTABILITY-008`: "no private conversation state counts as progress" (`workflows/setup.md VCPS-SETUP-053`). A second Claude Code session (or a human) can resume correctly having never seen the first session's conversation. |
| Capability absence | Explicit `NOT_RUN` / `INCONCLUSIVE` evidence result, never a silent skip | Example: no network access to a package registry → `NOT_RUN` with the reason recorded, not omission of the check. |
| Failure handling | `SETUP_STATUS: PARTIAL` or `BLOCKED`, per `workflows/setup.md §6` | A missing capability is never turned into an assumed `PASS` (`VCPS-SETUP-067`). |
| Independence (builder/verifier separation, `standard/independence.md`) | `I1`: same conversation, disclosed phase switch (the model explicitly re-reads its own output against the spec before claiming verification, per `VCPS-IND-002`/`005`). `I2`: a distinct subagent (the `Agent` tool, `subagent_type` other than `fork`) that is not given the builder's reasoning, only the artifact to verify, per `VCPS-IND-003`. | The Setup Engine itself mostly does not require independence beyond `I0`/`I1` (it is not a Gate 4/5 verification run); this row documents the mapping for when a *future* workflow adapter (`REVIEW`, `BUG`, etc.) needs it, since the mapping is reusable. |

## Why this stays adapter-layer, not Core

Core's actual contract is already complete without this document:
`workflows/setup.md VCPS-SETUP-067` lists the capabilities any adapter
must supply (repository-relative read/write with atomic persistence, safe
YAML parsing, VCS inspection, bounded command execution, checkpoint
requests, durable evidence locators) and says a missing capability
produces `NOT_RUN`/`INCONCLUSIVE` evidence and `PARTIAL`/`BLOCKED` status —
an adapter does not get to assert its way to a stronger tier than it
actually has a capability for (`VCPS-SETUP-067`). `standard/
human-checkpoints.md` already defines the checkpoint protocol
agent-independently. Nothing in this file changes either. A later adapter
author can read this table for a worked example and build their own,
different mapping; cross-adapter consistency review is explicitly
deferred in `standard/open-questions.md` until a second adapter exists.

## Capabilities this adapter does NOT currently claim

Per `workflows/setup.md VCPS-SETUP-067`'s "optional capabilities" list,
this reference-phase adapter has no verified mapping yet for: hosted CI
inspection beyond what the fixed local Git queries/`Read` call can see,
external-provider verification, browser execution, or production
observation. An invocation that needs `E3`/`E4`/`E5` evidence and cannot
get it through `Read`/`Bash`/a disclosed human-provided locator records
`NOT_RUN`/`INCONCLUSIVE` and the run stays at `PARTIAL`, per the table
above — it does not fabricate a stronger tier.

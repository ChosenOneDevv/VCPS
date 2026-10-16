# Portability

This document owns: portability invariants — the rules that let a VCPS
project be understood, resumed, and acted on by any conforming agent or
human, not only the one that last touched it.

## 1. Principle

**VCPS-PORTABILITY-001.** A project's VCPS state — risk profile, level,
lifecycle state, gate outcomes, findings, evidence records, checkpoint
decisions, and acceptance records — MUST NOT depend on any single agent's
private memory, conversation history, or session state to be understood.

**VCPS-PORTABILITY-002.** VCPS artifacts MUST use open, plain-text formats
(Markdown with YAML frontmatter, plain YAML) that any agent, tool, or human
can read without a proprietary reader.

## 2. Non-authoritative pointers

**VCPS-PORTABILITY-003.** An agent-specific or project-local file (editor
memory, prompt files, caches) MAY exist, but MUST be non-authoritative. If
an agent-specific file and a canonical VCPS artifact disagree, the
canonical artifact wins; the agent-specific file is a pointer or
convenience copy, never a second source of truth.

**VCPS-PORTABILITY-004.** External evidence (hosted CI runs, provider
dashboards, ticket systems) MUST be referenced with a stable locator. For
assertions a gate or lifecycle transition actually depends on, a durable
excerpt (result, revision, key excerpt or hash) MUST also be stored in the
repository, so the record remains interpretable even if the external
locator later becomes unreachable.

## 3. Secrets

**VCPS-PORTABILITY-005.** Artifacts MUST NOT contain secrets, credentials,
or unredacted personal data. Evidence that would contain them MUST be
redacted before being persisted; a heuristic match is grounds to hold and
ask a human, not grounds to silently drop the evidence.

## 4. Handoff

**VCPS-PORTABILITY-006.** When a workflow run ends, or when in-progress
work is interrupted, the in-progress state MUST be recorded such that a
different agent or human can determine what happened and what remains,
without replaying conversation history. The handoff record MUST reference
the specification version, project level, lifecycle state, and gate
outcomes it depends on by their current source (project config, work-item,
gate records) — not restate them as a frozen snapshot that could drift out
of sync with those sources. The
handoff record MUST also reference (not duplicate) the current
project/work-item/gate/finding state, and MUST state any pending human
checkpoint with its exact action/scope/reason so the next session can
resume without re-deriving it.

## 5. Identifiers

**VCPS-PORTABILITY-007.** Identifiers in VCPS artifacts MUST be stable and
agent-independent. An artifact MUST NOT require an agent session ID to be
interpreted (session IDs MAY appear as informational provenance).

## 6. Taking over a project

**VCPS-PORTABILITY-008.** A new agent taking over a project MUST treat
recorded VCPS artifacts as the source of truth over its own prior
assumptions, and MUST re-derive current state (mode, stage, pending
checkpoints, findings) from those artifacts before acting, rather than
from any summary carried over in its own context.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-PORTABILITY-001`
through `VCPS-PORTABILITY-002`, `004`, `005`, `006` (core sentences), and
`007`–`008` are recovered verbatim from `standard/core-audit-0.1.md`'s
per-line requirement inventory, including the audit's own amendment to
`VCPS-PORTABILITY-006` (noted there as CA-018, "to require referencing
version/level/lifecycle state") — the §4 wording above incorporates that
amendment as the current, post-correction text rather than the
pre-correction version the audit found defective. `VCPS-PORTABILITY-003`
is reconstructed (not verbatim-recovered) from the recovered line 20
fragment ("memory, prompt files, caches) MAY exist, but MUST be
non-authoritative. If an") plus its direct restatement in
`standard/VCPS.md` §5 ("`VCPS.md` and agent-specific files are
non-authoritative pointers") and `templates/contract.md` ("`VCPS.md` and
agent-specific files are non-authoritative pointers to
`.vcps/project.yaml`"), both intact. This file deliberately names no
specific agent or tool.

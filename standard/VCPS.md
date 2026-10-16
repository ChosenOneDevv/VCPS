# VCPS Core Standard

- **Specification version:** `1.0.0` (authoritative value: [`/VERSION`](../VERSION))
- **Status:** Stable. Every entry in [`standard/open-questions.md`](open-questions.md)
  is resolved or explicitly deferred with reasoning. A requirement will
  not change without a version increment, per [`standard/versioning.md`](versioning.md) —
  this is the stability guarantee a `-draft` suffix explicitly withheld.
  This status covers **Core (this layer) only**: it is not a claim that
  every adapter, workflow executor, or evaluation-suite component is
  complete, live-tested, or production-proven — see
  [`evaluation/completion-roadmap.md`](../evaluation/completion-roadmap.md)
  for the actual, current implementation status of every other layer,
  and do not infer it from this line.

## 1. Purpose

VCPS (Vibe Coding Production Standard) defines the rules, evidence model, risk
model, gates, and human checkpoints that govern AI-assisted software
development from discovery to production. It is designed so that any capable
coding agent — or a human — can execute it, and so that project state survives
switching between agents.

## 2. Scope

VCPS applies to:

- new ("greenfield") projects;
- existing and legacy repositories, including repositories adopted mid-life;
- any change made with material AI assistance, and any change made in a
  repository that has adopted VCPS.

VCPS does not prescribe a programming language, framework, hosting provider,
test framework, CI system, or AI vendor.

## 3. Normative language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** are to be
interpreted as described in BCP 14 (RFC 2119, RFC 8174) when, and only when,
they appear in all capitals.

Text marked *Informative*, examples, and rationale are non-normative.

## 4. Architecture and layering

VCPS is organized into five layers:

1. **Core Standard** (`standard/`) — normative rules and models.
2. **Workflows** (`workflows/`) — procedures that apply the Core to a user intent.
3. **Project templates / schema** (`templates/`) — concrete artifact formats.
4. **Agent adapters** (`adapters/`) — bindings to specific coding agents.
5. **Validation / evaluation suite** (`evaluation/`) — conformance checks.

**VCPS-CORE-001.** Layers 1–3 MUST NOT contain requirements that name, assume,
or depend on a specific AI coding agent, model, model vendor, or agent-private
feature (for example: a named slash-command system, a named memory store, or a
named subagent API).

**VCPS-CORE-002.** A lower-numbered layer MUST NOT depend on a higher-numbered
layer. Workflows MAY reference the Core; the Core MUST NOT require a specific
workflow implementation beyond the workflow contracts it defines.

**VCPS-CORE-003.** An adapter MUST NOT weaken, reinterpret, or omit a Core or
Workflow requirement. An adapter MAY add stricter behavior. Where an agent
cannot perform a required activity, the adapter MUST surface this as an
`EVIDENCE_GAP` or a human checkpoint, never as a silent skip.

## 5. Canonical ownership

Each normative concept has exactly one owning document. Other documents MUST
reference the owner rather than restate the rule. If a restatement conflicts
with the owner, the owner wins and the restatement is a specification defect.

| Concept | Owner |
|---------|-------|
| Terms and definitions | [glossary.md](glossary.md) |
| Principles (informative) | [principles.md](principles.md) |
| Impact dimensions, project risk profile, change risk class (R0–R3), critical invariants, escalation | [risk-model.md](risk-model.md) |
| Project levels (L1–L3) and level-specific minimums | [levels.md](levels.md) |
| Evidence records, tiers (E0–E5), results, fidelity, staleness | [evidence-model.md](evidence-model.md) |
| Finding classifications, severity, finding status | [classifications.md](classifications.md) |
| Feature lifecycle states and transitions | [lifecycle.md](lifecycle.md) |
| Human checkpoints (HC-*) and approval records | [human-checkpoints.md](human-checkpoints.md) |
| Portability invariants | [portability.md](portability.md) |
| Anti-gaming rules (AG-*) | [anti-gaming.md](anti-gaming.md) |
| Builder/verifier independence modes (I0–I4) | [independence.md](independence.md) |
| Project artifact set and minimum fields | [artifacts.md](artifacts.md) |
| Specification versioning, drift, upgrade semantics | [versioning.md](versioning.md) |
| Gate outcomes, applicability matrix, blocking thresholds | [gates/README.md](gates/README.md) |
| Individual gate requirements | `gates/gate-N-*.md` |
| Workflow contract, intent routing | [../workflows/README.md](../workflows/README.md) |
| Setup state machine | [../workflows/setup.md](../workflows/setup.md) |
| Open design questions | [open-questions.md](open-questions.md) |

## 6. Requirement identifiers

**VCPS-CORE-010.** Every normative requirement SHOULD carry a stable identifier
of the form `VCPS-<AREA>-<NNN>` (or a short local form such as `AG-003` or
`HC-05` defined in its owning document). Identifiers MUST NOT be reused for a
different meaning across versions. Removed requirements are retired, not
renumbered.

Project artifacts, evidence, and findings SHOULD cite requirement identifiers
when they claim satisfaction or violation of a requirement.

## 7. Actors and roles

Roles are functional. One person or system MAY hold several roles unless a
requirement forbids it (see [independence.md](independence.md) and
[human-checkpoints.md](human-checkpoints.md)).

| Role | Responsibility |
|------|----------------|
| **Owner** | Human accountable for the project or component; final authority on risk acceptance. |
| **Approver** | Human authorized to resolve a specific human checkpoint. |
| **Builder** | Agent or human producing the change. |
| **Verifier** | Agent or human producing verification evidence for a change. |
| **Agent** | An AI system acting as builder and/or verifier. |
| **Adapter** | Integration code that lets a specific agent execute VCPS. |

**VCPS-CORE-020.** An AI agent MUST NOT act as Owner or Approver.

## 8. Conformance

**VCPS-CORE-030.** A project that adopts VCPS MUST record, in repository-readable
artifacts (see [artifacts.md](artifacts.md)):

1. the VCPS specification version it implements;
2. its project level per [levels.md](levels.md), with the risk-profile evidence
   supporting it;
3. its critical invariant registry per [risk-model.md](risk-model.md);
4. its setup status per [../workflows/setup.md](../workflows/setup.md).

**VCPS-CORE-031.** A project MUST NOT claim conformance to a draft
(`-draft`) VCPS version as a production assurance. Draft conformance claims
MUST be labelled as draft.

**VCPS-CORE-032.** A project whose setup is not `COMPLETE` MUST describe its
conformance as `PARTIAL` and list the incomplete setup stages.

**VCPS-CORE-033.** A conformance claim is itself a claim under the evidence
model. It MUST be backed by a system audit (see
[../workflows/audit.md](../workflows/audit.md)) at a recorded revision.

## 9. Precedence

When documents conflict:

1. this file (`VCPS.md`) and the owner named in §5;
2. other Core documents;
3. workflows;
4. templates;
5. adapters.

A stricter project-local policy MAY override a weaker VCPS default. A
project-local policy MUST NOT weaken a VCPS `MUST` or `MUST NOT`.

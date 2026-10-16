# Open Design Questions

Design questions tracked during `0.1.0-draft`. Each was resolved or
explicitly deferred with reasoning before `1.0.0`.

| ID | Question | Why it's open |
|----|----------|----------------|
| `OQ-001` — RESOLVED | What license governs this repository? | Apache License 2.0, chosen by the project owner 2026-10-07; see [`LICENSE`](../LICENSE) and decision below. |
| `OQ-002` — RESOLVED | Concrete artifact schema (JSON Schema / YAML) for each record type in [artifacts.md](artifacts.md). | Hybrid YAML and Markdown/YAML frontmatter contract in [templates/](../templates/README.md). |
| `OQ-003` — RESOLVED | Exact `.vcps/` directory layout (file-per-record vs. index files vs. database) for large legacy repositories with thousands of findings. | Canonical file-per-record layout in [templates/contract.md](../templates/contract.md#canonical-layout). |
| `OQ-004` — RESOLVED | How does VCPS interact with monorepos spanning multiple independently-leveled components sharing one CI pipeline? Partially addressed by VCPS-RISK-021, needs worked examples. | `project.yaml.components[]` (already schema-defined: `id`, `path`, optional `level`) plus `VCPS-RISK-021`'s shared-path escalation rule is the complete mechanism; see decision below. |
| `OQ-005` — RESOLVED (reference mapping, non-normative) | Mapping between VCPS agent-independent orchestration concepts (discovery, command execution, file access, checkpoints, evidence, resume, capability absence, failure) and agent execution primitives, including `I0`–`I4` independence modes. | First mapping in [adapters/claude-code/vcps-setup/references/orchestration.md](../adapters/claude-code/vcps-setup/references/orchestration.md); see decision below. |
| `OQ-006` — RESOLVED | Should `KNOWN_LIMITATION` have an expiry-forcing mechanism (e.g. mandatory re-review date) at `L3`, beyond the optional `expires` field in `HC-08` records? | No new mandatory mechanism; see decision below. |
| `OQ-007` — RESOLVED for setup | How setup handles a repository that is already governed by a *different* AI-coding-standard (not VCPS). | [SETUP-069](../workflows/setup.md#verification-remediation-baseline-and-ci) and [scenario 22](../evaluation/setup-scenarios.md) define bounded reconciliation. |
| `OQ-008` — RESOLVED | Quantitative definition of "observation window" defaults for `PRODUCTION_PROVEN` per level, if any default is desirable versus always per-feature. | No Core-mandated default; `project.yaml.lifecycle.default_observation_window_days` (nullable) is project-local policy. Already implemented this way in practice (see `evaluation/fixtures/phase-a-live-setup`/`phase-j-setup-resume`'s own `project.yaml`); see decision below. |
| `OQ-009` — RESOLVED | Whether a lightweight `L0` tier (no VCPS applied at all, e.g. a throwaway script) should be formalized or left as "VCPS not adopted". | Left as "VCPS not adopted"; no new tier. See decision below. |
| `OQ-010` — DEFERRED past `1.0.0` | Conformance badge/self-report format for public repositories claiming VCPS conformance (ties to `evaluation/` layer, not yet designed). | Premature to design a badge format for a specification whose own requirements are still changing pre-`1.0.0`; see decision below. |
| `OQ-011` — RESOLVED (reference mapping, non-normative) | Mapping between Core's generic intent-classification/risk-escalation contract (`workflows/README.md` `VCPS-WF-001/002/003`, `standard/risk-model.md` `VCPS-RISK-041/045`) and agent execution primitives for a general `/vcps` router, distinct from `OQ-005`'s setup-orchestration mapping. | First mapping in [adapters/claude-code/vcps-router/references/intent-classification.md](../adapters/claude-code/vcps-router/references/intent-classification.md); see decision below. |
| `OQ-012` — RESOLVED (reference mapping, non-normative) | Mapping between VCPS's agent-independent orchestration concepts and the Codex CLI's actual execution primitives — the first mapping for an agent other than Claude Code, testing whether `OQ-005`'s "other adapters MAY differ" expectation holds up in practice. | First mapping in [adapters/codex/references/capability-mapping.md](../adapters/codex/references/capability-mapping.md), built from current official Codex CLI documentation (no live Codex session available to verify); see decision below. |

## Resolved decisions

**OQ-001 — license.** Decision: Apache License 2.0, for the entire
repository (specification text and reference adapter code alike), chosen
by the project owner 2026-10-07 specifically so anyone can use this
specification and its reference adapters. See [`LICENSE`](../LICENSE).
Rationale: a permissive, patent-protecting license with no
copyleft/share-alike obligation removes the biggest practical barrier to
adoption for a standard that wants other agents, companies, and
individuals to build adapters and real projects on top of it without
legal review overhead; Apache-2.0's explicit patent grant and termination
clause (§3) also gives adopters more protection than a bare MIT grant
would. Compatibility consequence: every file in this repository,
including `standard/`, `workflows/`, and `templates/` (specification
text, not only code), is licensed under Apache-2.0 — this was a
deliberate single-license choice, not the dual
specification/implementation licensing an earlier draft of this document
considered, because the owner's own instruction ("herkes kullanabilsin
ayrıca Apache 2.0 olsun" — "let everyone be able to use it, and let it be
Apache 2.0") named one license for everyone, not two.

**OQ-002 — artifact schema.** Decision: record schemas use `schema_version:
"0.1.0"`; the project config uses `schema_version: "0.2.0"` for durable
Setup Engine state;
`project.yaml` is canonical machine-readable configuration; fixed singleton
and per-record Markdown files use mandatory YAML frontmatter. JSON Schema
2020-12 defines structural fields and [validation.md](../templates/validation.md)
defines cross-record checks. Rationale: deterministic parsing without losing
human review context. Compatibility consequence: older or newer schema
versions require the explicit migration/read-only behavior in
[contract.md](../templates/contract.md#unknown-fields-and-migrations);
unknown fields cannot be ignored.

**OQ-003 — layout.** Decision: one repository-relative `.vcps/` root with
`project.yaml`, `baseline.md`, `invariants.md`, `risk-model.md`, and
file-per-record directories. `VCPS.md` is a pointer. `approvals/` and
`work-items/` are added for Core-required approvals and the shared remaining
intents. Rationale: stable agent-independent IDs, append-friendly history,
and directory scanning without a duplicate authoritative index. Large
installations MAY build disposable derived indexes; those cannot own
classification, result, or status. Compatibility
consequence: installations using another root/layout need an explicit
versioned migration; existing records keep IDs and history. The legacy
registry is a filtered view of finding records, not a second owner.

**OQ-007 — competing governance during adoption.** Decision: ADOPT preserves
the other system, records source-path provenance, imports observed facts
only, and requires HC-07 for conflicting ownership before mutation.
Existing approvals never translate into VCPS checkpoint decisions.
Rationale: two systems may be useful concurrently, but neither silently
owns the other's consent or risk state. Compatibility consequence: adapters
need a read-only crosswalk and may return PARTIAL; no conversion is assumed.

**OQ-005 — orchestration mapping.** Decision: orchestration stays in the
adapter layer. Core's contract is already the capability list of
`VCPS-SETUP-067`, the checkpoint protocol, and the `NOT_RUN`/`PARTIAL`/
`BLOCKED` rules; no new Core requirement is added. The Claude Code adapter
publishes its mapping of those needs to Claude Code primitives (skill
invocation, `Read`/`Write`, bounded helper-script command execution,
`AskUserQuestion` checkpoints, repository-only state and resume, explicit
capability-absence representation, failure to `PARTIAL`/`BLOCKED`, and
independence via same-conversation `I1` / subagent `I2`). Rationale: a
reference mapping helps later adapter authors without letting one agent's
mechanism become a Core rule. Compatibility consequence: other adapters make
their own mapping and MAY differ provided they satisfy `VCPS-SETUP-067` and
`VCPS-CORE-003`; the Claude mapping is informative only. Cross-adapter
consistency review is deferred until a second adapter exists.

**OQ-011 — intent-classification/escalation mapping.** Decision: like
`OQ-005`, this mapping stays in the adapter layer; no new Core requirement
is added. Core's contract is already `VCPS-WF-001/002/003` (classify into
exactly one intent, treat wording as input not authority, re-route when a
run no longer fits its intent) and `VCPS-RISK-041/045` (mechanical
enforcement-path escalation; cumulative segmentation effect). The Claude
Code adapter publishes a `/vcps` router skill whose helper script checks
only the genuinely mechanical half of this contract (enforcement-path
matches, raw critical-domain/work-item-overlap facts) and leaves intent
classification, domain-level impact tracing, and segmentation judgment to
the model, per the same split `OQ-005` already established for the setup
adapter. Rationale: identical to `OQ-005`'s — a reference mapping helps
later adapter authors without letting one agent's mechanism become a Core
rule, and keeps a genuinely mechanical Core rule (`VCPS-RISK-041`) from
being re-implemented as a weaker, adapter-private heuristic. Compatibility
consequence: other adapters make their own mapping and MAY differ provided
they satisfy `VCPS-WF-001/002/003` and `VCPS-CORE-003`; the Claude mapping
is informative only. This router classifies and escalates only — it
dispatches to `AUDIT`/`REVIEW` executors where they exist (see
"Deliberately deferred" below for the remaining five).

**OQ-012 — Codex capability mapping.** Decision: like `OQ-005`/`OQ-011`,
this mapping stays in the adapter layer; no new Core requirement is
added. The Codex adapter publishes nine workflow skills built from
official Codex documentation (not from assumed parity with Claude Code),
with mapped capabilities sourced and gaps disclosed rather than silently
worked around. Rationale:
identical to `OQ-005`'s own — a reference mapping helps later adapter
authors, and this is also the first real test of `OQ-005`'s own stated
compatibility consequence ("other adapters make their own mapping and
MAY differ provided they satisfy `VCPS-SETUP-067` and `VCPS-CORE-003`").
It does: Codex's default sandbox/approval posture (`workspace-write` +
`on-request`) permits in-workspace mutation without a per-file prompt by
default, materially different from Claude Code's default, and Codex has
no per-skill mutation-scoping mechanism equivalent to `allowed-tools` —
both are documented as capability gaps, not silently matched by
assumption. Compatibility consequence: a human installing this adapter
MUST explicitly configure `approval_policy`/`.codex/rules/*.rules` to
recreate equivalent mutation visibility; this is a real operational
step the Claude Code adapter never required, not a cosmetic difference.
No live Codex session was available to verify any of this empirically
— the mapping is `STATIC_INSPECTION` of documentation, stated as such
throughout.

**OQ-004 — monorepos with independently-leveled components.** Decision:
no new Core requirement. `project.yaml.components[]` already supports a
per-component `id`/`path`/optional `level` (`templates/schemas/
project.schema.json`); a change is classified and gated against whichever
profile (project-wide or a specific component's) its own impact paths
touch, not against a single repo-wide level — this is how `risk-model.md`
already works per-change, not per-repository. `VCPS-RISK-021` is the
substantive rule for the monorepo-specific case this OQ names: a
lower-level component sharing a path with a higher-level one (shared
database, shared credentials, shared deploy unit) is treated at the
higher level for changes on that shared path. A single CI pipeline
serving multiple components is a `ci.job_gate_map` concern
(`templates/contract.md`), already schema-supported, not a gap in the
risk/level model itself. Rationale: the mechanism was already complete;
what was missing was recognizing it as complete, not new design. A
worked example remains a documentation nice-to-have, not a blocking gap
— `evaluation/`'s existing worked examples (todo-cli, synthetic-commerce)
are single-component and MAY gain a monorepo variant later, but `1.0.0`
does not require it.

**OQ-006 — `KNOWN_LIMITATION` expiry.** Decision: no new mandatory
expiry-forcing mechanism. The existing optional `expires` field on an
`HC-08` risk-acceptance decision already lets an owner set one when
appropriate; making it mandatory would force an artificial re-review
date onto limitations that are legitimately permanent (e.g. "we will
never support Internet Explorer," a deliberate architectural tradeoff
with no planned revisit). Rationale: `VCPS-CLS-030`-style owner judgment
already governs whether a limitation needs a revisit date; a blanket
mandatory mechanism would be exactly the kind of Core-imposed rigidity
`VCPS-CORE-001` cautions against when a narrower, already-existing
mechanism (the optional field, owner-set) covers the real need.
Compatibility consequence: none — this closes the question without
changing any existing schema or requirement.

**OQ-008 — observation window defaults.** Decision: no Core-mandated
default. `project.yaml.lifecycle.default_observation_window_days`
(nullable) is project-local policy; a `FEATURE` MAY set its own
`observation_window` instead (`lifecycle.md §2`). Rationale: a
one-size-fits-all default (e.g. "14 days") would be arbitrary across the
full range of VCPS-governed systems — a low-traffic internal tool and a
high-traffic consumer API need different windows to accumulate
meaningful `PRODUCTION_PROVEN` signal, and Core has no way to know which
a given project is. This was already the de facto behavior in practice
(every worked example and live fixture in this repository leaves it
project-local or null) before being named here as the actual resolution
rather than an unstated gap.

**OQ-009 — a formal `L0` tier.** Decision: no new tier; a project with
no VCPS installation is simply "VCPS not adopted," not an `L0`-leveled
VCPS project. Rationale: `levels.md`'s `L1`–`L3` exist to calibrate
*how much* evidence/process VCPS requires once adopted; a throwaway
script that nobody is tracking under VCPS at all needs no calibration,
because no VCPS requirement applies to it in the first place — naming
that absence "`L0`" would suggest it is a VCPS state with its own rules,
when it is precisely the absence of one. `workflows/setup.md`'s `NEW`
mode already starts a project at `L1` the moment it *is* adopted; nothing
between "not adopted" and `L1` needs a name.

**OQ-010 — conformance badge format.** Deferred past `1.0.0`, not
resolved: designing a public self-report/badge format now, while Core
requirements, schemas, and even this very open-questions list are still
changing, would either need revision at every pre-`1.0.0` change or
invite early adopters to badge against a moving target. Rationale:
`evaluation/`'s own layer (conformance checks) is itself still `PARTIAL`
— a badge format needs a settled thing to check conformance against.
Revisit once `1.0.0` itself is cut (see Phase M,
`evaluation/completion-roadmap.md`) and the evaluation layer has a real
conformance-check suite to point a badge at, not before.

## Deliberately deferred to later layers (not open questions, just not yet built)

- Templates layer: a complete schema/cross-record validator. The Claude
  adapter ships a partial mechanical helper only (see its README for coverage).
- Adapter layer: Claude Code has a setup adapter, a router, and all
  seven non-`SETUP` workflow executors (`adapters/claude-code/README.md`'s
  component list) as reference drafts. Codex has nine workflow skills
  (`adapters/codex/README.md`) as reference drafts. Claude setup has
  full `LIVE_ADAPTER_EXECUTION` evidence for both the dry-run and
  mutating paths (`evaluation/completion-roadmap.md` Phase A, closed
  2026-10-07); the other eight Claude components, and all Codex skills,
  have no `LIVE_ADAPTER_EXECUTION` evidence yet. Bindings for additional
  agents remain unstarted.
- Evaluation layer: conformance test suite (`evaluation/`).
- CI workflow definitions. (Installer scripts now exist —
  `adapters/install.py`, Phase K, closed 2026-10-07 — covering both
  adapters' skill installation and a vendored-Core option for
  Claude Code; the `0.1.0`→`0.2.0` project-schema migration itself is
  mechanized as `vcps_tool.py migrate-project-schema`.)

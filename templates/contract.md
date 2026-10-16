# Project artifact contract

Project schema version `0.2.0`; layout and other record schemas remain
`0.1.0`. [Core](../standard/VCPS.md) owns the meanings of risk,
evidence, findings, gates, lifecycle, and checkpoints. This layer owns their
repository representation.

## Canonical layout

```text
VCPS.md                         pointer only
.vcps/
  project.yaml                  config and installation state
  baseline.md                   adoption observations/history
  invariants.md                 invariant definitions
  risk-model.md                 impact ratings and paths
  approvals/                    checkpoint decisions and pre-authorizations
  findings/                     one finding per file
  features/                     FEATURE records
  reviews/                      REVIEW records
  bugs/                         BUG records
  releases/                     RELEASE records
  work-items/                   TINY, HOTFIX, AUDIT records
  evidence/                     one evidence record per file
  handoffs/                     one handoff per interruption/run
  gates/                        one gate evaluation per file
```

The extra `approvals/` directory is required by VCPS-HC-020/030. The extra
`work-items/` directory houses the remaining three intents under one shared
schema. Legacy findings are `findings/` records with `origin: LEGACY`; no
second legacy registry duplicates them. `VCPS.md` and agent-specific files
are non-authoritative pointers to `.vcps/project.yaml`.

Every Markdown artifact has exactly one YAML frontmatter document between
`---` lines, followed by narrative text. Structured state lives only in
frontmatter; prose cannot override it. `project.yaml` is plain YAML.
All local paths are repository-relative. Directory scans discover records.
Filenames locate files but do not own record identity.

## Identity and references

All record IDs are immutable and repository-wide unique. The prefixes
`FND`, `EVD`, `FEAT`, `REV`, `BUG`, `REL`, `WORK`, `HND`, `GATE`, `HCR`,
`PREAUTH`, and `BLO` use a lowercase hyphenated UUID version 4 suffix.
Invariants retain Core's `INV-` followed by at least three decimal digits.
Allocate an invariant number above the existing maximum and never renumber
one. IDs are not derived from filename, agent, conversation, or machine.
References use IDs; singleton references use fixed paths. A missing or
duplicate ID is invalid. Withdrawn/resolved IDs remain reserved.

## Canonical ownership

| Concept | Canonical artifact | References or projections | Mutation rule |
|---|---|---|---|
| Schema/layout and VCPS version | `project.yaml` | Handoff project reference; `VCPS.md` pointer | Versioned migration and config-history event |
| Project identity, level, components, commands, CI, critical domains, evidence policy | `project.yaml` | Work-item component/level reference | History event; HC-09 for downgrade |
| Installation mode/status/stage, execution plan and stage events | `project.yaml` `installation` | Handoff project reference | Append stage events; replace plan only after read-only replanning; no inferred COMPLETE |
| Dimension ratings and impact paths | `risk-model.md` frontmatter | Project level checked against derived rating | Reason/evidence and history on change |
| Invariant definitions/enforcement | `invariants.md` frontmatter | Work-item affected IDs | Preserve ID and amendment history |
| Active invariant IDs | `project.yaml` `applicable_invariants` | Invariant definitions must exist | Config history; no orphan IDs |
| Baseline scope/revision and observation history | `baseline.md` frontmatter | Project fixed baseline path | Original observations immutable; append only |
| Evidence tier/result/provenance/revision | `evidence/ID.md` frontmatter | Baseline, gate, finding references | Append correction history; never relabel a run |
| Finding classification/status/severity | `findings/ID.md` frontmatter | Work items and baseline cite ID | Preserve original; append transitions |
| Feature lifecycle state | `features/ID.md` frontmatter | Handoff work-item reference | Core transition rules and history |
| Other work-item state/risk/applicable gates | File in intent directory | Gates/handoffs cite ID | Change history and risk re-evaluation |
| Gate outcome/independence | `gates/ID.md` frontmatter | Work item/handoff gate refs | New evaluation supersedes old; retain both |
| Human decision/pre-authorization | `approvals/ID.md` frontmatter | Work item cites approval ID | Scope/revision bound; no silent rewrite |
| Handoff step/next actions | `handoffs/ID.md` frontmatter | References project/work/gates/findings | New handoff supersedes old |

The work-item `acceptance.state` is a **derived projection**: PENDING until
its HC-14 decision reference exists, then equal to that decision. Release
go/no-go is derived from HC-10. Gate outcomes in handoffs come from gate
references. A baseline check's result is dereferenced from its evidence
record, not copied into a second authoritative field. These projections
must be checked for agreement.
`change_class` and `project_level` in a gate record are immutable evaluation
snapshots, not current owners; current values belong to the work item and
`project.yaml`. A gate outcome of NOT_APPLICABLE must agree with the work
item's applicability decision.

## Schemas and field contract

The [JSON Schemas](schemas/) own required keys, optional keys, types,
enums, and unknown-field rejection. Common fields below clarify use:

- `project.yaml` requires `schema_version`, `artifact_layout_version`,
  `vcps_version`, `project`, `level`, `installation`, `repository`,
  `stack`, `commands`, `ci`, `critical_domains`,
  `applicable_invariants`, `evidence_policy`, `baseline_ref`, and
  `config_history`, and `lifecycle`. Optional: `components`, `project_local_policy_refs`,
  `notes`. Commands have stable IDs, purpose, repository-relative working
  directory, and exact command string. Empty discovered lists are valid;
  never invent commands or CI. Repository metadata is portable VCS type,
  credential-free remote, and default branch.
  `installation.pending_artifact_refs` lists canonical files that a setup
  stage has not created yet. A baseline reference may be pending only before
  Stage 8. COMPLETE requires the list empty and every reference resolved;
  a pending file due at the recorded stage is an inconsistency, not a
  license to skip it.
  `installation.plan` owns the active bounded dry-run; `plan_history` keeps
  earlier complete plans after replanning. `stage_events` is the append-only
  attempt/invalidation journal, with each event bound to one plan hash and
  scoped input fingerprint. `installation.stage` identifies the earliest
  outstanding stage. A missing plan is valid only during migration before
  Stage 4; active setup at Stage 4 or later requires a plan and events.
  `evidence_policy.minimum_tier_overrides` may only strengthen a Core
  minimum. Removing an active invariant requires the Core risk and
  checkpoint rules; editing its ID list cannot silently declassify a path.
- `risk-model.md` has project and optional component profiles with all
  D1–D9 ratings, paths, and evidence references. Level is owned only by
  `project.yaml` and must match Core's derivation.
- `invariants.md` has each INV assertion, owner, dimensions, component
  scope, enforcement paths, evidence need, and history. Project config
  owns which IDs are active.
- `baseline.md` has the exact revision and date, all configured check IDs
  with BLO observation IDs and evidence references (including blocked,
  NOT_RUN, ERROR, INCONCLUSIVE), inherited finding references, environment
  limitations, and append-only addition/resolution history. Evidence owns
  each result. A resolution keeps the original observation and cites a
  RESOLVED finding. An ADD_OBSERVATION history event carries a new BLO
  observation; a RESOLVE_OBSERVATION event references an existing BLO ID.
  Neither changes the initial `observations` array.
- Findings have Core classification/status, severity, domain, discovery,
  scope, affected invariants, blocking scope, evidence, producer/verifier,
  resolution, and history. LEGACY requires a touch rule and starts OPEN.
- Evidence has E0–E5 tier, result, assertion, method/action, environment,
  producer/verifier, timestamp, exact revision, freshness scope,
  artifacts, substitutions, limitations, related records, and corrections.
  E3 needs a retrievable CI run; E4 an external actor/action; E5 a
  production observation. E0 is a claim with NOT_RUN. A correction creates
  a new evidence ID linked by `supersedes_ref`; the prior run stays intact.
- One work-item schema covers FEATURE, REVIEW, BUG, RELEASE, TINY, HOTFIX,
  AUDIT. All have ID, intent, title, scope, component/level reference,
  risk class if a change, applicable gates, affected invariants,
  lifecycle/workflow state, evidence/findings/checkpoint references, and
  acceptance projection. FEATURE adds criteria and success signals/window;
  BUG links the defect; REVIEW cites intent sources; RELEASE identifies
  included changes, revision, and Gate 6.
- Gates have exact revision, evaluated activities, outcome, evidence,
  findings, checkpoint refs, independence, evaluator, and supersession.
- Approvals contain checkpoint, decision, exact scope, human actor, time,
  constraints, related work, revision where applicable, expiry, and reuse
  permission. Silence has no approval representation.
- Handoffs record workflow/step, project/work and gate/finding refs, pending
  checkpoint ID plus proposed action/scope/reason, and concise next actions.
  Version, level, lifecycle,
  and gate outcomes are obtained through those refs.

## Unknown fields and migrations

All structured mappings reject unknown keys and duplicate YAML keys.
No extension field silently becomes authoritative. Timestamps and versions
are quoted RFC 3339/SemVer strings; no custom tags, aliases, merges, or
multiple YAML documents. This avoids an old reader ignoring new safety
fields.

Schema versions use SemVer independently of `vcps_version`. Equal supported
schema: validate and proceed. Older schema: read with its matching schema,
preserve original files/IDs, create an explicit migration, validate the
result, and record a config-history event; never rewrite evidence or
approvals. Newer or unsupported schema: read-only diagnosis and stop writes;
never downgrade destructively. Missing/malformed version routes to REPAIR.
Core VCPS version drift still follows [versioning.md](../standard/versioning.md).

Project schema `0.1.0` is the supported predecessor; its matching schema is
[project-0.1.0.schema.json](schemas/project-0.1.0.schema.json). Migration to
`0.2.0` adds `installation.plan: null`, `plan_history: []`, and
`stage_events: []`, records a config-history migration event, and keeps all
existing observations and IDs. It then performs a new read-only dry-run and
reconstructs stage completion from existing artifacts and fresh
fingerprints; it never fabricates historical stage events. Until Stage 4
persists a valid plan/events, the setup is PARTIAL. This migration changes
only the project config schema, not layout or record schemas. No other
older project schema has a defined automatic migration.

# Phase 0 — Product Scope, Gate Baseline, and Traceability

Status: **COMPLETE — PLANNING BASELINE**  
Date: 2026-10-07  
Scope revision: working-tree documentation change based on repository HEAD
`37db8409fa9b16664c4259f282bd8f2f4189e9f0`; no Core requirement or gate
definition is changed by this charter.

This charter fixes the problem, user profiles, phase boundaries, gate
baseline, and evidence plan for Phases 0–5. It is an execution plan, not a
claim of Core certification, a gate record for an adopting project, or a
release approval.

## 1. Product problem and intended outcome

AI-assisted software work often produces code without a portable, inspectable
record showing intended behavior, risk, verification, security review, and
human release decisions. VCPS provides an agent-independent Core and
repository-readable workflow artifacts so a project can distinguish
`IMPLEMENTED`, `VERIFIED`, `ACCEPTED`, and `PRODUCTION_PROVEN` using evidence
appropriate to its risk.

For this repository, the near-term product outcome is a usable reference
implementation with a safe first-install path, repeatable validation, honest
adapter capability claims, and a release process that cannot turn missing
evidence or silence into `PASS`.

### Intended user profiles

| Profile | Job to be done | Initial success signal | Main risk/constraint |
|---|---|---|---|
| Individual starting a new repository | Install one agent adapter and begin with VCPS setup | Can follow one quick-start and see a validated setup result | Confusing Core, adapter, and project-schema versions |
| Team adopting an existing repository | Inspect current project, establish baseline and migrate gradually | Existing files are not overwritten; gaps and required decisions are reported | Legacy unknowns, dirty trees, existing governance files |
| Maintainer of a multi-component or critical project | Apply risk-based gates and retain evidence across changes/releases | Gate outcomes match revision, evidence tier, independence, and human decisions | False confidence from local-only or stale evidence |
| Adapter/integration contributor | Add or update a specific agent binding without changing Core meaning | Structural checks and live limits are documented and repeatable | Agent-specific behavior leaking into normative layers |
| Reviewer, auditor, or future agent | Resume work from portable records and challenge claims | Can trace a claim to source, revision, run, and decision | Missing provenance, injection, or ambiguous ownership |

## 2. Scope and non-goals

### Included in Phases 0–5

- Clarify users, supported claims, phase deliverables, and measurable exits.
- Preserve the Core/Workflow/Template/Adapter/Evaluation layering.
- Improve first install, diagnosis, validation, upgrade, recovery, and
  removal for Claude Code and Codex reference adapters.
- Establish repeatable local and CI evidence, complete the project-artifact
  validator against its contract, and exercise adapters with honest live
  acceptance records.
- Close or explicitly retain security and portability gaps, then prepare
  release units for a human Gate 6 decision.

### Excluded unless separately authorized and scoped

- Claiming vendor endorsement, third-party certification, or universal
  security assurance.
- Treating the synthetic Phase J project as a real customer acceptance or
  production observation.
- Making an agent the Owner/Approver or generating HC-08, HC-10, or HC-14
  decisions on behalf of a human.
- Changing the normative meaning of Core 1.0.0 as part of adapter/UX work.
  Any such proposal follows `standard/versioning.md` and receives a separate
  change scope, compatibility analysis, and version decision.
- Publishing a package before the project owner selects a distribution
  channel and the release evidence supports that claim.

## 3. Acceptance principles

1. Every feature or phase has observable acceptance criteria and an evidence
   source; narrative intent alone is not a pass.
2. No gate outcome is inferred from a test suite's overall green status.
   Applicability, revision, risk class, project level, findings, evidence
   tier/fidelity, independence, and checkpoint state remain explicit.
3. `NOT_EVALUATED`, `NOT_RUN`, `BLOCKED`, and `PARTIAL` remain distinct.
   No missing evidence or absent human response defaults to approval.
4. A user-facing install or update operation previews material changes,
   preserves unrelated/user-owned data, reports partial failure, and can
   verify what it installed.
5. Adapter capability claims identify runtime/version and the tested
   boundary; structural or simulated evidence is never presented as live
   execution evidence.
6. A phase may close with a named, bounded residual gap only if its exit
   criteria allow it and the gap has an owner, impact, and next decision.

## 4. Core gate applicability and repository traceability

The authoritative per-change matrix is
[`../standard/gates/README.md`](../standard/gates/README.md#4-applicability-matrix).
This section maps requirement families to current implementation/evidence;
it does not supersede that matrix or constitute a gate evaluation.

| Requirement(s) | Normative owner | Workflow/artifact touchpoint | Current validation/evidence | Phase 0 disposition |
|---|---|---|---|---|
| `VCPS-G1-001`–`003` | [Gate 1](../standard/gates/gate-1-product.md) | FEATURE/BUG/REVIEW/AUDIT intent, acceptance criteria, reconstructed intent; work-item/finding/evidence records | Workflow executors and sample records exist; full artifact validation and all adapter live paths are not established | Normative intent is clear; trace all criteria to record fields in Phase 2; live coverage in Phase 4 |
| `VCPS-G2-001`, `010`–`012`, `014`–`015` | [Gate 2](../standard/gates/gate-2-architecture.md) | Risk model, invariants, architecture/failure plans, verification plan | Workflow guidance and Phase J sample exist; some adapter executions and full validator checks remain incomplete | Gate recovery uncertainty retained; verify path-to-test links in Phase 2 and critical-state live cases in Phase 4 |
| `VCPS-G3-001`–`007`, `009`–`010` | [Gate 3](../standard/gates/gate-3-implementation.md), [anti-gaming](../standard/anti-gaming.md) | Diff, dependencies, secrets, baseline checks, work-item scope | Structural, simulated, and anti-gaming suites exist; there is no single top-level runner/CI | Implement runner and baseline-bound CI in Phase 2; broaden install failure/update cases in Phase 3 |
| `VCPS-G4-001`–`007`, `030`–`031` | [Gate 4](../standard/gates/gate-4-verification.md), [evidence model](../standard/evidence-model.md) | Evidence records, invariants, checks, regression tests, revision/fidelity | Helpers and evaluation records cover subsets; no hosted CI, so E3 is unavailable for this repository; Phase J demonstrates resulting BLOCKED state | Phase 2 must complete deterministic coverage and CI; Phase 4 must test actual independence/runtime behavior |
| `VCPS-G5-001`–`016` | [Gate 5](../standard/gates/gate-5-security.md), [risk model](../standard/risk-model.md) | Security categories selected by impact dimensions; evidence and limitations | Targeted security review and synthetic probes exist; audit explicitly leaves mutation-path and provider-ingestion work open | Preserve category-by-change applicability; Phase 2 wires scans; Phase 4/5 cover runtime boundaries and remaining threat review |
| `VCPS-GATE-001`–`002`, `010`–`011`, `020`–`021`, `030`–`032`, `040`, `050` | [Gate semantics](../standard/gates/README.md) | Gate record, outcome, evidence/finding/checkpoint refs, independence and supersession | Gate schemas and helper checks exist, but full Core conformance validation is incomplete | Validator in Phase 2 must enforce outcome/matrix/revision/history links; never infer a stronger status |
| `VCPS-G6-001`, `011`–`012`, `020` and `VCPS-GATE-021` | [Gate 6](../standard/gates/gate-6-release.md) / [gate semantics](../standard/gates/README.md#5-gate-6-per-release-unit) | Release record, included changes, HC-10, E5 observation | Release workflow/helper exists; no actual production release is claimed | Phase 5 release checklist may report readiness; the authorized human retains go/no-go |
| `VCPS-LVL-*`, `VCPS-RISK-*`, `VCPS-IND-*`, `VCPS-EVD-*`, `VCPS-HC-*` | [levels](../standard/levels.md), [risk](../standard/risk-model.md), [independence](../standard/independence.md), [evidence](../standard/evidence-model.md), [checkpoints](../standard/human-checkpoints.md) | Profile, risk, invariant, evidence, approval, handoff records | Schemas/helpers cover parts; conformance rules include exact revision, evidence tier, independence, human actor and checkpoint binding | Phase 2 matrix enumerates validator coverage; Phase 4/5 gather runtime evidence without creating synthetic human decisions |

### Risk and independence examples required by the plan

| Scenario | Expected class/level | Expected gate behavior | Evidence/independence expectation |
|---|---|---|---|
| Documentation typo with no policy or execution effect | `R0`, any level | G1/G2/G5 `NOT_APPLICABLE`; G3/G4 light; Gate 6 only if included in a release | Applicable static checks; `I0` allowed |
| Small-looking UI edit that changes authorization enforcement path | At least `R1`, classify from impact path; project level applies | Never route as `R0`/TINY based on wording; G2/G5 conditional on touched surfaces | L2 R1 requires `I1`; L3 R1 requires `I1`; adversarial verification |
| Change to payment/tenant critical state | `R3` where impact dimensions trigger; often L3 | G1–G5 required, Gate 4/5 cannot be passed on insufficient fidelity | L3/R3 requires E3 CI fidelity, `I2`; each affected invariant directly exercised |
| Release of a set containing mixed classes | Highest included class recorded | Gate 6 once for whole release unit; required G1–G5 outcomes and HC-10 checked | Current release revision; affirmative human decision and conditions satisfied |

These are plan-level acceptance scenarios, not claims that any particular
project has those risk ratings. Actual classification uses the facts and
impact-path evidence required by the owning Core documents.

## 5. Recovery and confidence register

No original gate backup was available in the repository evidence reviewed
for this phase. Do not silently rewrite Core 1.0.0 based on conjecture.

| Area | Source confidence disclosed by owning document | Phase 0 action | Follow-up |
|---|---|---|---|
| Gate applicability matrix | `gates/README.md` says exact cells were inferred from workflow summaries, TINY, and CA findings; exact G2 trigger text also paraphrased | Treat the current published 1.0.0 text as authoritative for implementation, but mark historical provenance `PARTIAL`; never “repair” it in adapter code | Search repository history/backup refs read-only; if none, raise a separately scoped Core change proposal with impact and versioning decision |
| Gate 1 | G1-001/003 recovered; G1-002/outcomes reconstructed | Retain recovery note; no conflicting intact citation surfaced in this phase | Include in future Core source/requirement graph audit |
| Gate 2 | G2-011/012 fragment/G2-015 and L3/R3 bullet recovered; G2-001 reconstructed; G2-014 ID uncertain; G2-010 ratified from Principles; G2-002..009 unexplained | Keep gaps explicit; no requirement IDs invented to fill gaps | If source is unavailable, preserve unused numbers and make any new rule separately versioned |
| Gate 3 | G3-001..007 recovered with a G3-007 boundary ambiguity; G3-009 inferred/corroborated; G3-010 ratified from TINY | Do not treat uncertain clause attribution as historical certainty | Requirement graph audit and source comparison if evidence appears |
| Gate 4 | G4-003..006, G4-030/031 recovered; G4-001/002 reconstructed; G4-001 ID inferred; G4-007 ratified | Keep the requirement ID attribution caveat visible | Confirm numbering/wording against any original backup before a future Core revision |
| Gate 5 | G5-001/012 narrow recovered text; G5-002..016 are new ratification decisions, not recovered original language | Treat added criteria as current published requirements, while preserving their design-decision provenance | Future revision may clarify rationale/coverage; do not remove or weaken as cleanup |
| Gate 6 | Some requirements reconstructed; Gate 6 veto behavior corrected from critical audit finding; G6-020 partly recovered | Preserve human veto and post-release E5 obligations; no “recorded decision means approved” shortcut | Re-audit release workflow against Gate 6 before any actual release |
| Independence | IND-001..005/010 recovered; I0/I3/I4 descriptions reconstructed | Do not assert certainty beyond the file's notes | Include level/risk/mode edge cases in Phase 2 tests |

**Core 1.0.0 constraint:** these confidence notes are provenance about how
the current text was reconstructed; they do not make the current published
requirements optional. If a future change alters their conformance meaning,
follow [`../standard/versioning.md`](../standard/versioning.md), including
compatibility and explicit versioning. A lower layer cannot independently
reinterpret a gate (`VCPS-CORE-003`).

## 6. Phase charters

| Phase | Product objective | Principal deliverables | Exit evidence | Planned gates / checkpoints |
|---|---|---|---|---|
| **0 — Scope and traceability** | Define user outcomes, boundaries, normative baseline, and proof of completion | This charter; user profiles; gate/requirement map; recovery register; phase cards; support/claim baseline | All phases have owners/artifacts/evidence/exits; Core uncertainty stays visible; documentation links and claims are internally consistent | Plan work is expected `R0`: G1/G2/G5 N/A, G3/G4 light. No Core change or human decision is manufactured. |
| **1 — First install** | Let a new user safely select and install a compatible adapter | Quick-starts; preflight/doctor; install plan preview; first validation and troubleshooting path | Fresh temporary projects can follow both adapter paths; preview matches install; incompatibility is surfaced before mutation | G1, G3, G4; G5 only for touched security categories; HC-01/HC-11/HC-12 where action triggers them |
| **2 — Validation and CI** | Produce repeatable artifact and code verification evidence | One runner; CI; schema library validation; 14-rule trace matrix/tests; baseline and evidence artifact linking | Clean checkout command and CI agree; covered requirements have positive/negative/boundary cases; E3 result is retrievable and revision-bound | G2–G5 as applicable; independence per level/R class; HC-08 for serious residual gaps |
| **3 — Installer lifecycle** | Support safe repeat, verify, upgrade, repair, and removal | Manifest; atomic install; verify/diff; upgrade/uninstall; migration backup/rollback; portable shared helper | Failure injection and user-edit cases prove no unrelated data loss; all install scopes verify; no duplicated helper drift | G1–G5 as applicable; HC-01/02/11/12 for destructive/live/secret actions |
| **4 — Live adapter acceptance** | Establish what real agents can execute and where they block | Adapter × skill acceptance matrix; live runs; two-way handoff; injection/denial probes | Runtime/version/revision/tool outputs retained; live and non-live boundaries explicit; required human actions are genuinely human | G3–G5; HC-06/08/10/14/16 as their specific triggers arise |
| **5 — Security and release readiness** | Bound residual risk and make release decisions auditable | Threat review; ingestion tests; supply-chain results; support/deprecation policy; release checklist; post-release observation plan | Security findings dispositioned; included gate outcomes current; HC-10 affirmative with conditions met; E5 window owner defined | Gate 5 and Gate 6 per release unit; HC-10 never inferred or pre-authorized |

### Supported claim baseline

| Area | Current documented claim | Phase 0 scope decision |
|---|---|---|
| Core | `VERSION`/`standard/VCPS.md` state 1.0.0 stable; stability applies to Core requirement meaning only | Retain distinction between Core stability and implementation maturity |
| Project schema | Template contract specifies schema 0.2.0 and supports 0.1.0 as a migratable predecessor | Adapter/setup/migration claims must keep schema version separate from Core version |
| Claude Code adapter | README identifies Core/schema write targets and setup capability; roadmap has live SETUP, FEATURE, REVIEW evidence | Phase 4 tracks remaining router/AUDIT/BUG/TINY/HOTFIX/RELEASE live coverage; keep exact revision limits |
| Codex adapter | Nine skills structurally tested; bounded read-only fixture use and cross-agent CLI handoff exist; general live skill acceptance remains open | Phase 4 must distinguish CLI read/continuation from skill loading and full workflow execution |
| Distribution | Installer works from local checkout; no published package | Phase 3 must make owner decision between supported checkout distribution and package release |
| Evaluation | Structural/simulated/live records exist; full Core conformance suite and CI are absent | Phase 2 is prerequisite to broad Gate 4/5 and stronger production claims |

## 7. Phase 0 completion record

### Deliverables

- Product problem, five user profiles, intended outcome, scope, and non-goals
  recorded in §§1–2.
- Acceptance principles recorded in §3.
- Gate requirement families and current evidence limits mapped in §4.
- R0/R1/R3 and release-unit examples recorded in §4, tied to owning Core
  documents and explicitly labeled illustrative.
- Gate reconstruction confidence and follow-up protocol recorded in §5.
- Scope, deliverables, exit evidence, and planned gates/checkpoints for
  Phases 0–5 recorded in §6.
- Current support/claim baseline recorded in §6.

### Exit assessment

| Exit criterion | Result | Evidence |
|---|---|---|
| User need and profiles identified | `PASS` (planning deliverable) | §§1–2 |
| Phase scope, dependencies, artifacts, exit evidence and planned gates stated | `PASS` (planning deliverable) | §§2, 6 |
| Normative gate-to-evidence map established without changing Core meaning | `PASS` (baseline established; downstream validator coverage remains open) | §§4–5 |
| Reconstructed Core uncertainty disclosed and not auto-resolved | `PASS` | §5; owning recovery notes remain canonical |
| Human checkpoint and release decision boundaries preserved | `PASS` (policy recorded; no project approval asserted) | §§2–3, 6 |
| README/roadmap/adapters/validation claims checked against current repository records | `PARTIAL` | Source claims were cross-read; exact requirement-level validation mapping and all cross-document contradictions are Phase 2 traceability work |

Phase 0 is **complete as a planning/baseline phase**. It does not claim that
the validation matrix has been implemented, any adapter is production-ready,
the gate reconstruction has been historically resolved, or any human
checkpoint has been approved. Its residual validation work is deliberately
carried into Phase 2 and its live behavior work into Phases 4–5.

### Gate note for this phase

This phase changes evaluation planning documentation only; it does not
change normative Core behavior or executable paths. The expected change
class is `R0`. Under the current published matrix, Gate 1, Gate 2, and Gate 5
are `NOT_APPLICABLE`; Gate 3 and Gate 4 use light scope. This is a planning
assessment, not a persisted project gate record: the repository does not
currently have an adopted `.vcps/` project record for this planning change.
`git diff --check` is the only mechanical check run for the new Markdown;
test suites were not run. No stronger Gate 4 result is claimed.

## 8. Decisions intentionally left open

1. **Published package vs. checkout install:** owner decision in Phase 3,
   based on desired support/release burden.
2. **Shared helper distribution:** choose an agent-neutral common package or
   generated/vendor copies with drift verification in Phase 3.
3. **Historical source for reconstructed gate documents:** search only
   available repository history/authorized backups; absence of a source does
   not authorize guessing or rewriting Core 1.0.0.
4. **Supported OS/Python/runtime matrix:** define from actual adapter and
   helper compatibility evidence in Phases 2–4; do not imply portability
   from structural tests on one host.

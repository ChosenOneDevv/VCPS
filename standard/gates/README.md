# Gates

This document owns: gate outcomes, the gate applicability matrix, blocking
thresholds, and the gate record format. Individual gate requirements are
owned by `gate-N-*.md`.

## 1. Gates

| Gate | Name | Concern |
|------|------|---------|
| Gate 1 | Product | Intended behavior and acceptance criteria are defined. |
| Gate 2 | Architecture | Design addresses trust boundaries, failure modes, and critical-state mechanisms before implementation. |
| Gate 3 | Implementation | The change is scoped, inspected, and free of fabrication/anti-gaming patterns. |
| Gate 4 | Verification | Evidence exists that the change behaves as intended. |
| Gate 5 | Security | Security-relevant categories (authorization, tenant isolation, business-logic abuse, and others per the change) are evaluated. |
| Gate 6 | Release | A human go/no-go decision gates deployment of a release unit. |

## 2. Outcomes

**VCPS-GATE-001.** `NOT_EVALUATED` MUST NOT be treated as `PASS` or
reported as if the gate ran. It means the gate was never attempted for
this change.

**VCPS-GATE-002.** `NOT_APPLICABLE` MUST cite the matrix row and the facts
that make it apply. An agent MUST NOT mark a gate `NOT_APPLICABLE` where the
matrix marks it `REQUIRED` for the change class.

| Outcome | Meaning |
|---|---|
| `PASS` | The gate's required activities are complete and its evidence/findings meet the threshold; excludes any unresolved finding in scope at or above the blocking severity threshold (`levels.md §5`). |
| `PARTIAL` | A gap remains; permitted only where this document's or a gate's own partial-progression rule (`VCPS-GATE-010`, §3) allows it, with the gap explicitly recorded — never a silent downgrade of `PASS`. |
| `BLOCKED` | The gate cannot pass. MUST carry one or more reason codes: `DEFECT` (open blocking defect), `EVIDENCE` (required evidence missing and gap is blocking), `DECISION` (pending human checkpoint), `DEPENDENCY` (prerequisite gate/external party not ready). |
| `NOT_APPLICABLE` | Per `VCPS-GATE-002`. |
| `NOT_EVALUATED` | Per `VCPS-GATE-001`. |

## 3. Partial progression

**VCPS-GATE-010.** A gate MAY progress with outcome `PARTIAL` only where a
gap is explicitly recorded as a finding with severity and touch rule, the
gap does not itself violate a critical invariant, and — at `L3` — any
residual gap at or above `MEDIUM` severity has an explicit `HC-08` decision
before the dependent work proceeds past this gate. A `PARTIAL` outcome
MUST NOT be silently treated as equivalent to `PASS` by a later gate or
workflow; each consumer checks the actual outcome, not an assumption that
"partial is good enough."

## 4. Applicability matrix

Change risk class (`R0`–`R3`, `risk-model.md §5`) drives which gates are
`REQUIRED`, conditional, or `NOT_APPLICABLE` for a given change. Gate 6 is
evaluated per release unit, not per change, and does not use this
per-change matrix (see §5).

| Gate | `R0` | `R1` | `R2` | `R3` |
|---|---|---|---|---|
| Gate 1 (Product) | `NOT_APPLICABLE` | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| Gate 2 (Architecture) | `NOT_APPLICABLE` | conditional (`VCPS-G2-001`: required only if the change touches a critical-state mechanism or trust boundary) | `REQUIRED` | `REQUIRED` |
| Gate 3 (Implementation) | required, light scope (scope discipline and secrets checks still apply; full diff/anti-gaming inspection scales with risk) | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| Gate 4 (Verification) | required, light scope (applicable automated checks only; no adversarial pass required) | `REQUIRED` | `REQUIRED` | `REQUIRED` at required fidelity (`levels.md §3`) |
| Gate 5 (Security) | `NOT_APPLICABLE` | conditional (required only for categories the change actually touches) | `REQUIRED` | `REQUIRED` |
| Gate 6 (Release) | — (per release unit; see §5) | — | — | — |

**VCPS-GATE-011.** Workflow documents MAY summarize this matrix for their
own intent (`workflows/README.md §4`), but this matrix is authoritative;
a workflow's summary MUST NOT weaken it (`VCPS-CORE-003`).

## 5. Gate 6 (per release unit)

**VCPS-GATE-020.** Gate 6 is evaluated once per release unit against the
full set of included changes, not once per individual change. It is
`REQUIRED` for every release regardless of the individual changes'
`R`-classes.

**VCPS-GATE-021.** Gate 6 `PASS` requires every `REQUIRED` Gate 1–5 outcome
on the release revision to be `PASS` or a permitted `PARTIAL`
(`VCPS-GATE-032`), and an affirmative `HC-10` decision: `APPROVED` or
`APPROVED_WITH_CONDITIONS` with every stated condition met. A `REJECTED`
`HC-10` decision, an unmet condition, or a missing decision MUST block
Gate 6 and the release — a human release veto is never inferred as
satisfied by default, and silence does not grant it.

## 6. Gate record

**VCPS-GATE-050.** Each gate evaluation MUST be recorded with: `gate`,
the evaluated revision, the change class and project/component level at
evaluation time, outcome, reason code(s) if `BLOCKED`, evidence
references, finding references, applicable checkpoint references,
independence mode actually used (Gates 4–5, per `independence.md §3`),
evaluator identity, and supersession link to any prior evaluation of the
same change.

**VCPS-GATE-030.** Gates 4 and 5 MUST be evaluated on a recorded revision.

**VCPS-GATE-031.** Gates MAY be evaluated iteratively. A gate's outcome is
the latest evaluation on the current revision; an earlier evaluation on a
superseded revision remains in the record but does not govern progression.

**VCPS-GATE-032.** Gate 4 MUST NOT be evaluated `PASS` before Gate 3 is
`PASS` or permitted `PARTIAL` on the same revision. Gate 6 MUST NOT be
`PASS` while any Gate 1–5 required for the included changes is not `PASS`
or a permitted `PARTIAL` on the release revision.

**VCPS-GATE-040.** An agent MUST NOT report a gate outcome stronger than its
actual evidence supports, and MUST NOT resolve a disagreement between two
conflicting check results (e.g. two CI jobs on the same scoped check, one
`PASS` and one `FAIL`) by reporting only the favorable one — both results
are retained and the unresolved conflict bars a scoped `PASS`
(`evidence-model.md VCPS-EVD-020`).

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-GATE-001`, `002`,
`030`, `031`, `032`, and `040` are recovered verbatim from
`standard/core-audit-0.1.md`'s per-line requirement inventory.
`VCPS-GATE-021`'s substance (Gate 6 `PASS` requiring `APPROVED`/
`APPROVED_WITH_CONDITIONS` with conditions met, tied to `HC-10`, and a
`REJECTED`/missing decision blocking release) is reconstructed from that
audit's finding CA-037, which describes the corrected rule in prose
without quoting it verbatim — CA-037 explicitly flagged the *pre*-fix
version as a CRITICAL defect ("it inverted the human release veto"), so
this reconstruction deliberately encodes the *post*-fix behavior CA-037
describes, not a guess. `VCPS-GATE-011`'s cross-reference to Gate 6 being
per-release-unit is grounded in finding CA-019, which states this
explicitly as an intentional, already-documented carve-out. §4's
applicability matrix table is the **least certain part of this file**:
no exact matrix cell was recovered verbatim; every cell is inferred from
indirect evidence — `workflows/README.md §4`'s informative per-intent
summary (intact), `workflows/tiny.md`'s R0 scope (intact, "light" Gate
3/4, N/A Gate 1/2/5), and finding CA-022's description of Gate 2's actual
R-class behavior ("R2/R3 remediation always evaluates Gate 2... R1
retains the conditional VCPS-G2-001 trigger"). The exact wording of
`VCPS-G2-001`'s trigger condition is itself not recovered — "critical-state
mechanism or trust boundary" is this reconstruction's best paraphrase from
context, not a quotation. This entire matrix table SHOULD be reviewed
against the original if a backup ever surfaces; until then, treat any
`NOT_APPLICABLE`/`REQUIRED` cell here as the adapter's and this
reconstruction's best inference, not a certainty.

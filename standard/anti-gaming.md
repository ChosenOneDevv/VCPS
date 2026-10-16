# Anti-Gaming Rules

This document owns rules that prevent weakening verification to obtain a
passing result. These rules apply to every agent and human, in every workflow.

## 1. Prohibited without a recorded exception

**VCPS-AG-000.** The following actions are **verification weakening**. An agent
MUST NOT perform them to make a task, gate, or check pass. Where such a change
is genuinely correct, it MUST go through the exception protocol (§2).

| ID | Rule |
|----|------|
| `AG-001` | MUST NOT delete, skip, quarantine, or disable a test or check. |
| `AG-002` | MUST NOT weaken an assertion (broader matcher, removed field check, increased tolerance, snapshot overwrite accepting new output) without recorded justification showing the old assertion was wrong. |
| `AG-003` | MUST NOT lower coverage, mutation, performance, or quality thresholds merely so the current change passes. |
| `AG-004` | MUST NOT make a blocking check non-blocking: `|| true`, `continue-on-error`, `allow_failure`, ignored exit codes, `--passWithNoTests` on a suite that should have tests, or equivalent. |
| `AG-005` | MUST NOT disable, downgrade, or scope-out lint, type checking, static analysis, or security scanning (config changes, blanket ignore comments, `any`-style escapes, excluding paths) without per-instance justification. |
| `AG-006` | MUST NOT change production behavior solely to satisfy a test the agent believes incorrect; the test's correctness MUST be resolved against intended behavior first. |
| `AG-007` | MUST NOT report `NOT_RUN`, `ERROR`, or `INCONCLUSIVE` as `PASS` (see VCPS-EVD-020). |
| `AG-008` | MUST NOT reclassify `EVIDENCE_GAP` as `DEFECT` without reproduction or static demonstration (see VCPS-CLS-001). |
| `AG-009` | MUST NOT declare a lifecycle state, gate `PASS`, or production readiness without the required evidence (see VCPS-LC-001). |
| `AG-010` | MUST NOT special-case test environments in production code (e.g. `if (process.env.TEST) return ok`) to pass checks. |
| `AG-011` | MUST NOT edit evidence, gate, finding, or checkpoint records to misstate what happened; corrections are appended, not rewritten. |
| `AG-012` | MUST NOT narrow the test selection (filters, focused tests, changed-files-only modes) for gate evidence below what the gate requires. |
| `AG-013` | MUST NOT replace real verification with mocks of the component under test. |
| `AG-014` | MUST NOT downgrade a change class or project level to reduce required gates (see VCPS-RISK-043, `HC-09`). |
| `AG-015` | MUST NOT catch, suppress, or otherwise prevent an error or failed assertion from propagating to its check's recorded result, solely to avoid a `FAIL`/`ERROR` outcome. |
| `AG-016` | MUST NOT change acceptance criteria or specification to match actual implementation behavior believed incorrect, without the exception protocol (§2); criteria changes MUST be justified against user/business intent, never against making the current implementation pass. |
| `AG-017` | MUST NOT rewrite or alter the baseline (see [../workflows/setup.md §Baseline Update Procedure](../workflows/setup.md#baseline-update-procedure)) to reclassify a newly-introduced failure as pre-existing. |

## 2. Exception protocol

**VCPS-AG-020.** A verification-weakening change is permitted only when:

1. the change is isolated and identifiable in the diff;
2. the justification is recorded, citing intended behavior (Gate 1 artifact,
   invariant, or owner statement) that shows the existing check is wrong or
   obsolete;
3. replacement verification is added where the old check covered a real
   assertion; and
4. for `R2`/`R3` scope, or any threshold or CI change, checkpoint `HC-06` is
   approved.

**VCPS-AG-021.** At `R0`/`R1` scope, a test that tests removed functionality MAY
be deleted with the justification recorded in the change, without `HC-06`,
provided the removal of the functionality is itself part of the approved intent.

## 3. Detection

**VCPS-AG-030.** Gate 3 and Gate 4 reviews MUST inspect the diff for the
patterns in §1. Detected unapproved weakening is a `DEFECT` of severity at
least `HIGH` against the change.

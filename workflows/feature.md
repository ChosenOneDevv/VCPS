# Workflow: FEATURE

## Purpose

Build new behavior, or materially change intended behavior, under full gate
discipline proportionate to risk.

## Entry conditions

`SETUP_STATUS` not `BLOCKED` on a dependent stage. Feature record created in
state `PROPOSED`.

## Steps

1. **Classify** change risk class per [../standard/risk-model.md §5](../standard/risk-model.md#5-change-risk-classes). Record provisionally; re-check per step.
2. **Gate 1** — Product Discovery. On `PASS`/`PARTIAL` → `SPECIFIED`.
3. **Gate 2** — Architecture & Failure Design (per applicability matrix).
4. **Implement.** Gate 3 — Implementation Quality & AI Coding Protocol. On `PASS`/`PARTIAL` → `CODED`.
5. **Verify.** Gate 4 — Verification & Adversarial QA.
6. **Security review.** Gate 5 (per applicability matrix).
7. On Gates 4–5 `PASS` (or permitted `PARTIAL`) on the same revision → `VERIFIED`.
8. **Acceptance.** Obtain `HC-14` acceptance against each criterion → `ACCEPTED`.
9. Hand off to [release.md](release.md) for Gate 6 and eventual `PRODUCTION_PROVEN`.

## Gate mapping

Full matrix per [../standard/gates/README.md §4](../standard/gates/README.md#4-applicability-matrix); `FEATURE` does not reduce any gate's depth below the matrix.

## Escalation / re-routing

- If discovery or implementation reveals a reported defect in *existing*
  unrelated behavior, split it into a `BUG` run rather than folding it in
  (VCPS-WF-003), unless fixing it is required to implement the feature.
- If scope is found to be `R0` throughout → re-route to [tiny.md](tiny.md).
- If an invariant is touched that was not in Gate 1 → re-run Gate 1/2 at `R3`.

## Outputs

Feature record progressed through states with evidence; gate records 1–5;
findings; checkpoint records; handoff record.

## Exit

`ACCEPTED` at minimum for the workflow to be considered complete; `CODED`/`VERIFIED` are valid stopping points when explicitly scoped (e.g. acceptance deferred to a stakeholder), recorded as such — not reported as "done".

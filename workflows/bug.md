# Workflow: BUG

## Purpose

Fix a reported incorrect behavior, with reproduction before fix and
regression evidence after.

## Entry conditions

A bug report (user-filed, agent-discovered, or monitoring-detected) exists.

## Steps

1. **Confirm intent.** Determine the intended behavior the report implies
   (Gate 1, light unless the report reveals ambiguity — then full depth).
2. **Reproduce.** Establish `E2`+ evidence of the defect (VCPS-CLS-001).
   Failure to reproduce → classify `EVIDENCE_GAP` (`INCONCLUSIVE`), do not
   proceed to fix a guessed cause without owner input.
3. **Classify change risk class** from what the fix touches
   (VCPS-RISK-040/041) — not from the bug's apparent triviality.
4. **Design** (Gate 2) whenever required by the applicability matrix.
   For `R1`, apply the conditional trigger in VCPS-G2-001; an `R2`/`R3`
   fix cannot mark Gate 2 `NOT_APPLICABLE` merely because its design is
   unchanged.
5. **Fix** (Gate 3).
6. **Verify** (Gate 4), including the regression-test requirement
   (VCPS-G4-030). A reproduced defect is exactly the case VCPS-G4-030
   targets; apply its tier/level conditions as written — this workflow does
   not strengthen or restate it.
7. **Security review** (Gate 5) if applicable per matrix — a bug fix that
   touches auth/data-access logic is at minimum `R2`.
8. **Confirm fix** against the original reproduction: the regression test
   fails on the parent revision and passes on the fix revision
   (VCPS-G4-031).

## Gate mapping

Per applicability matrix at the determined change class. `BUG` never uses
`TINY`'s reduced depth, even for a one-line fix, because `AG-014` and
VCPS-RISK-040 forbid sizing down by diff size.

## Escalation / re-routing

- Reproduction reveals the "bug" is actually a missing/undefined
  specification → re-route the specification question through Gate 1 fully;
  consider whether this is really a `FEATURE` gap.
- Reproduction reveals a security exposure → Gate 5 required regardless of
  original triviality assumption; consider [hotfix.md](hotfix.md) if live.
- Fix scope grows beyond the reported defect → `HC-13`.

## Outputs

Reproduction evidence, finding record (`DEFECT`, with history from report to
resolution), fix changes with gate records, regression test with before/after
evidence.

## Exit

`RESOLVED` finding status requires remediation evidence at the level's
required tier plus regression evidence per VCPS-CLS-031. Lifecycle state of
the affected feature follows [lifecycle.md demotion/promotion rules](../standard/lifecycle.md).

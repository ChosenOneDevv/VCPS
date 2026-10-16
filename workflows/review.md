# Workflow: REVIEW

## Purpose

Examine an existing screen, module, or feature against its *intended*
behavior, find gaps, remediate what is verified, and record what is not —
without pretending residual uncertainty is a defect or a clean bill of health.

## Entry conditions

A target scope (screen/module/feature/area) is identified. `SETUP_STATUS` not
`BLOCKED`.

## Steps

1. **Reconstruct intended behavior** (Gate 1, VCPS-G1-003): specifications,
   tickets, tests, docs, UI copy, domain rules, prior commits, owner
   statements. Cite each source and its evidence tier. Conflicting or absent
   sources are recorded as `EXTERNAL_ACCEPTANCE` ambiguity, not resolved by
   guess.
2. **Inspect current implementation.** Read the actual code path end to end
   (not just the entry point) for the scope. `E1` evidence.
3. **Gap analysis.** For each reconstructed behavior, compare expected vs.
   actual. Each divergence becomes a finding classified per
   [../standard/classifications.md](../standard/classifications.md):
   - Actual deviates from intended, reproduced or statically demonstrated per
     VCPS-CLS-001 → `DEFECT`.
   - Intended behavior unknown/unconfirmed → `EVIDENCE_GAP` or
     `EXTERNAL_ACCEPTANCE`.
   - Deviation is a deliberate accepted tradeoff with evidence of prior
     acceptance → `KNOWN_LIMITATION`.
4. **Remediate verified problems.** Only findings classified `DEFECT` under
   VCPS-CLS-001 are remediated as code changes, routed through Gates 2–5 at
   the change class the fix requires (same as [bug.md](bug.md) steps 3–6).
5. **Regression evidence.** VCPS-G4-030 applies to each remediated defect.
6. **Security review.** Inspect the reviewed scope using Gate 5's categories,
   including behavior outside a remediation diff. Record findings and evidence
   for that broader inspection; evaluate a Gate 5 outcome for each remediation
   diff according to the applicability matrix.
7. **Record remaining evidence gaps.** Every `EVIDENCE_GAP` and
   `EXTERNAL_ACCEPTANCE` not resolved in this run stays `OPEN`, with owner,
   or is routed to the legacy registry if the scope is pre-existing and
   outside this run's budget (VCPS-SETUP-022 pattern applies here too, cited
   not duplicated).

## Gate mapping

| Gate | Applies to |
|------|-----------|
| 1 | Reconstruction (always, light-to-full depending on scope risk). |
| 2 | For remediations, per the applicability matrix; `R2`/`R3` are required. |
| 3–5 | Applied to each remediation diff, per matrix at the remediation's change class; broader review inspection does not itself create a change gate outcome. |
| 6 | Via [release.md](release.md) if remediations ship. |

## Escalation / re-routing

- A finding reveals a security exposure reachable in production now →
  treat as `HC-05`-relevant immediately; consider [hotfix.md](hotfix.md) for
  the exposure, continue `REVIEW` for the rest.
- Reconstructed intent contradicts a registered invariant → `HC-08`.

## Outputs

Expected-vs-actual record, findings (all four classifications as
applicable), remediation changes with their own gate records, updated/legacy
evidence-gap entries, security findings.

## Exit

A `REVIEW` run's correctness is not measured by "no defects found" — it is
measured by whether every divergence was classified and every gap honestly
recorded. `REVIEW` exits with a report: counts by classification, remediated
items with evidence, and an explicit open-gaps list. A `REVIEW` MUST NOT
report a scope as "clean" or "fully verified" if any `EVIDENCE_GAP` remains
open in that scope — it reports `PARTIALLY REVIEWED` with the gaps listed.

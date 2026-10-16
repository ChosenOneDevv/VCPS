# Workflow: AUDIT

## Purpose

Assess a repository, component, or VCPS installation itself, without
changing behavior. Produces a report, not remediation.

## Entry conditions

An audit scope is identified: a component, the whole repository, or "the
VCPS installation" (used by [setup.md Stage 11](setup.md#stage-11--vcps-system-audit)
and by [VCPS.md §8 conformance claims](../standard/VCPS.md#8-conformance)).

## Steps

1. **Scope definition.** State exactly what is in and out of scope and why.
2. **Evidence inventory.** For the scope, enumerate existing evidence
   records, their tiers, revisions, and staleness (VCPS-EVD-050/051).
3. **Gate-outcome review.** For each change/feature in scope, confirm
   recorded gate outcomes are not stale and match the evidence on file —
   `AUDIT` does not re-run verification itself; it checks that verification
   claimed actually has evidence (`E1` review of records).
4. **Classification review.** Confirm findings are classified correctly per
   [../standard/classifications.md](../standard/classifications.md) — no
   `EVIDENCE_GAP` silently promoted to "resolved", no `DEFECT` silently
   reclassified without reproduction.
5. **Anti-gaming review.** Scan history/diffs in scope for
   [../standard/anti-gaming.md](../standard/anti-gaming.md) patterns not
   already flagged.
6. **Installation consistency** (when scope includes VCPS itself): config
   matches `VERSION`/artifacts; no orphaned references; levels and invariant
   registry still match current impact paths (re-derive, don't assume).
7. **Report.** Produce an audit report: coverage with numerator, denominator,
   scope, and evidence basis; gaps, misclassifications found, and conformance
   statement per VCPS-CORE-033.

## Gate mapping

`AUDIT` does not execute Gates 1–3 as production activities; it reviews their
records. Gate 4/5 activity is limited to confirming evidence exists and is
not stale — not re-executing verification (that is `REVIEW`'s job if gaps are
found). Gate 6 relevance is a readiness review, not a release decision.

## Escalation / re-routing

- A misclassification or gap found that implies live risk → do not fix in
  `AUDIT`; open a `REVIEW` or `BUG` run and reference it from the audit
  report.
- **VCPS-WF-AUDIT-001.** `AUDIT` MUST NOT modify code, tests,
  configuration, or behavior. Any such need is out-of-scope and routed
  elsewhere.

## Outputs

Audit report (coverage %, stale-evidence list, misclassification list,
anti-gaming findings, conformance statement), linked follow-up workflow runs.

## Exit

Report delivered with an explicit conformance statement
(`FULL` / `PARTIAL` / `NOT_CONFORMANT`) per VCPS-CORE-033, never silently
implied.

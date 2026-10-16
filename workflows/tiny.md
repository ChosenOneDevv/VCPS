# Workflow: TINY

## Purpose

Handle genuinely `R0` changes (copy, styling, comments, docs, formatting)
with minimum ceremony, without becoming a loophole for larger changes.

## Entry conditions

The change is provisionally believed `R0`: no behavior change reachable by
users or systems, and no enforcement-path file touched.

## Steps

1. **Verify `R0` eligibility** against
   [../standard/risk-model.md §5](../standard/risk-model.md#5-change-risk-classes)
   before proceeding, not after. If the change touches any file listed in a
   critical invariant's enforcement path, or changes behavior, STOP and
   re-route (VCPS-WF-003) — this check is mandatory, not optional, precisely
   because `TINY` is attractive to misuse.
2. **Make the change.**
3. **Gate 3 (light)** — VCPS-G3-010 scope: scope discipline, no secrets, no
   anti-gaming weakening, static checks run.
4. **Gate 4 (light)** — VCPS-G4-007: run configured checks, confirm no new
   failures vs. baseline.

## Gate mapping

Gates 1, 2, 5 are `NOT_APPLICABLE` by definition of `R0`. Gates 3 and 4 run at
light depth only.

## Escalation / re-routing

**VCPS-WF-TINY-001.** Any of the following found during the change MUST
immediately stop `TINY` and re-route to `BUG` or `FEATURE` at the correct
class: the diff affects logic, queries, access control, external calls,
schema, or anything on an invariant's enforcement path; the diff is larger
than a cosmetic change naturally requires; static checks fail in a way
suggesting behavior change.

## Outputs

Minimal: Gate 3/4 light records, diff.

## Exit

`CODED` with light Gate 3/4 `PASS`. `TINY` changes generally do not need
individual feature acceptance; they ride with the next release's Gate 6.

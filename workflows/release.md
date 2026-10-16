# Workflow: RELEASE

## Purpose

Move a release unit (one or more completed changes) to production under
Gate 6, and close the loop with post-release production evidence.

## Entry conditions

Every change in the release unit has reached the gate outcomes required by
its workflow (`FEATURE`/`BUG`/`REVIEW` remediations/`TINY`/`HOTFIX`) on a
common, non-stale revision.

## Steps

1. **Assemble release unit.** Identify the exact revision and the full change
   set it contains.
2. **Confirm prerequisite gates.** Per VCPS-GATE-032: every included change's
   required Gate 1–5 outcomes are `PASS`/permitted-`PARTIAL`/`NOT_APPLICABLE`
   on this revision, not stale.
3. **Gate 6.** Execute [../standard/gates/gate-6-release.md](../standard/gates/gate-6-release.md)
   at the depth required by the highest change class and project level in
   the unit.
4. **Go/no-go.** `HC-10` at `L2`+. A rejected decision or unmet condition
   stops deployment and leaves Gate 6 `BLOCKED`.
5. **Deploy** only after Gate 6 permits it and all required checkpoints are
   approved for this exact action.
6. **Post-release observation.** Collect `E5` evidence against each
   feature's success signals within its defined window
   (VCPS-G6-020/VCPS-G1-001 item 6).
7. **Promote.** Features with sufficient `E5` evidence and no open
   `CRITICAL`/`HIGH` production finding → `PRODUCTION_PROVEN`.
8. **On failure:** demote affected features (VCPS-LC-010), open `BUG` or
   trigger `HOTFIX`.

## Gate mapping

Gate 6 only; this workflow is Gate 6's procedural home. Gates 1–5 are
inherited, not re-executed, from the originating workflows.

## Escalation / re-routing

- A change in the unit has stale or missing required evidence →
  `BLOCKED (DEPENDENCY)`; either re-verify that change or remove it from the
  release unit.
- Post-release observation reveals failure → `HOTFIX` for live harm, `BUG`
  for the underlying defect, demotion per lifecycle rules regardless.

## Outputs

Release record, Gate 6 record, `HC-10` decision, post-release evidence,
feature lifecycle promotions/demotions.

## Exit

Release record `PASS`/`PARTIAL` with go decision recorded; `PRODUCTION_PROVEN`
promotions recorded separately as their own evidence arrives — a release
being live is not, by itself, `PRODUCTION_PROVEN` for any feature in it.

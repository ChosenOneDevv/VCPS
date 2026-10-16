# Workflow: HOTFIX

## Purpose

Remediate an urgent production problem quickly, while keeping the evidence
trail and deferring (never skipping) what cannot be done before relief.

## Entry conditions

A live production impact is confirmed (not merely reported) — users affected,
data at risk, or security exposure active.

## Steps

1. **Confirm production impact** (`E2`+: reproduce against production
   evidence/logs, or `E5` direct observation). Unconfirmed urgency MUST NOT
   invoke `HOTFIX`; use `BUG`.
2. **Minimal Gate 1**: state the exact harm and the smallest change that
   stops it. Full discovery is deferred, not skipped — recorded as a
   follow-up `EVIDENCE_GAP`.
3. **Gate 2**: REQUIRED if the fix touches a critical-state mechanism; MAY be
   deferred via `HC-16` otherwise, with the deferral recorded and a follow-up
   task created.
4. **Gate 3**: full — a time-pressured fix is exactly when scope discipline
   and anti-gaming rules matter most (`AG-004`, `AG-010` apply without
   exception for `HOTFIX`).
5. **Gate 4 (reduced)**: verification MAY be scoped to the specific harm and
   its immediate blast radius rather than the full suite, via `HC-16`, with
   the omitted scope recorded as `EVIDENCE_GAP` to be closed within a defined
   follow-up window.
6. **Gate 5**: REQUIRED for any category the fix touches — security
   shortcuts under time pressure are explicitly the failure mode this rule
   exists to prevent.
7. **Release** (expedited Gate 6, VCPS-G6-011/012 still apply; `HC-10` and
   `HC-03` are NOT waivable by `HOTFIX`).
8. **Immediate follow-up**: schedule a `BUG` or `REVIEW` run to close every
   `EVIDENCE_GAP` deferred under `HC-16`, within an explicit deadline.

## Deferral discipline

**VCPS-WF-HOTFIX-001.** `HC-16` is the only mechanism to defer a gate
requirement under `HOTFIX`. Each deferral MUST record: what was skipped, why,
the residual risk, and the follow-up commitment (owner + deadline). A gate
deferred this way is recorded `PARTIAL` or `BLOCKED` with reason, never
`PASS`.

**VCPS-WF-HOTFIX-002.** `HOTFIX` MUST NOT be used to bypass `HC-01` through
`HC-05` or `HC-11`/`HC-12` — urgency changes timeline, not authorization.

**VCPS-WF-HOTFIX-003. (Lapsed deferral)** A deferral whose recorded
follow-up deadline has passed without resolution becomes a blocking finding
at severity `HIGH` or higher (regardless of its original severity) and MUST
escalate to `HC-08` for explicit re-acceptance or immediate scheduling. It
MUST NOT silently persist past its deadline — a `HOTFIX` deferral is not a
permanent verification bypass.

## Escalation / re-routing

If the "urgent" problem turns out not to be live-production-impacting on
investigation, re-route to `BUG` and drop the expedited posture.

## Outputs

Impact evidence, minimal Gate 1 record, fix with full Gate 3, scoped Gate 4/5
evidence, `HC-16` deferral records with follow-up commitments, release
record.

## Exit

Production harm stopped with evidence; all deferrals have owners and
deadlines; follow-up workflow scheduled and linked.

---
name: vcps-hotfix
description: Remediate a CONFIRMED live production problem quickly, deferring (never skipping) what cannot be done before relief, per workflows/hotfix.md. Use only when production impact is already confirmed — unconfirmed urgency MUST use /vcps-bug instead.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py lapsed-deferral-check *), AskUserQuestion
---

# /vcps-hotfix

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/hotfix.md` in the *current target
repository*. **Read that file in full now** — this skill is a thin
dispatcher over it, not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-hotfix.md`). `HOTFIX` is the highest-risk workflow to
get wrong in exactly the direction of "urgency justifies skipping
things" — this skill exists to compress ceremony without ever letting
that compression become silent skipping.

## 0. First: is this actually confirmed? (Entry condition)

`workflows/hotfix.md`'s entry condition is a **confirmed** live
production impact — `E2`+ reproduction against production evidence/logs,
or `E5` direct observation. **Unconfirmed urgency MUST NOT invoke
`HOTFIX`** — if you cannot point to actual evidence of live impact right
now, stop and use `/vcps-bug` instead. "The user said it's urgent" is not
confirmation.

## 1. Confirm production impact (Step 1)

State exactly what evidence you have and at what tier.

## 2. Minimal Gate 1 (Step 2)

State the exact harm and the smallest change that stops it. Full
discovery is **deferred, not skipped** — record it as a follow-up
`EVIDENCE_GAP` now, not as an afterthought.

## 3. Gate 2 (Step 3)

REQUIRED if the fix touches a critical-state mechanism; MAY be deferred
via `HC-16` otherwise — see "Deferral discipline" below before deferring
anything.

## 4. Gate 3 — full, no exception (Step 4)

`AG-004`/`AG-010` apply **without exception** for `HOTFIX`. Time pressure
is exactly when scope discipline and anti-gaming rules matter most, not
a reason to relax them. You MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <file> [...]
```
as a candidate-only check on your own fix before committing it.

## 5. Gate 4 — reduced, via `HC-16` only (Step 5)

Verification MAY be scoped to the specific harm and its immediate blast
radius, **via `HC-16`** — not simply by deciding to skip the rest. The
omitted scope MUST be recorded as `EVIDENCE_GAP` with a follow-up window.

## 6. Gate 5 — required for any touched category (Step 6)

No exception. Security shortcuts under time pressure are exactly the
failure mode this rule exists to prevent.

## 7. Release — expedited Gate 6 (Step 7)

`VCPS-G6-011/012` still apply. **`HC-10` and `HC-03` are NOT waivable by
`HOTFIX`** (`VCPS-WF-HOTFIX-002`) — urgency changes the timeline, never
the authorization. Hand off to `/vcps-release` for the actual Gate 6
execution.

## 8. Immediate follow-up (Step 8)

Schedule a `/vcps-bug` or `/vcps-review` run to close every `EVIDENCE_GAP`
deferred under `HC-16`, with an explicit deadline — this is not optional
cleanup, it is part of this workflow's own exit condition.

## Deferral discipline (`VCPS-WF-HOTFIX-001`/`002`/`003`)

- `HC-16` is the **only** mechanism to defer a gate requirement under
  `HOTFIX`. Every deferral MUST record what was skipped, why, the
  residual risk, and the follow-up commitment (owner + deadline) — as
  the approval record's `deferral_follow_up` field.
- `HOTFIX` MUST NOT be used to bypass `HC-01` through `HC-05` or
  `HC-11`/`HC-12` — urgency changes timeline, not authorization.
- A gate deferred this way is recorded `PARTIAL` or `BLOCKED` with
  reason — **never `PASS`**.
- Before closing out (and periodically on any `HOTFIX`-touched
  repository), run:
  ```
  ${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py lapsed-deferral-check --target <repo>
  ```
  A deferral with a passed deadline (or none recorded at all) is flagged
  as a candidate — per `VCPS-WF-HOTFIX-003` this becomes a blocking
  `HIGH`+ finding requiring `HC-08` re-acceptance or immediate
  scheduling, not something that silently persists.

## Escalation / re-routing

If the "urgent" problem turns out not to be live-production-impacting on
investigation, re-route to `/vcps-bug` and drop the expedited posture —
immediately, not after finishing the fix under the wrong workflow.

## Exit

Production harm stopped with evidence; every deferral has an owner and a
deadline; the follow-up workflow is scheduled and linked. A `HOTFIX` run
with an undated, unowned deferral has not actually exited this workflow
correctly, whatever the production state looks like right now.

## Never

- Never invoke this skill for merely *reported* (not confirmed) urgency.
- Never defer a gate requirement through any mechanism other than `HC-16`.
- Never treat `HC-10` or `HC-03` as waivable, regardless of pressure.
- Never let a deferral's follow-up go unscheduled or undated.

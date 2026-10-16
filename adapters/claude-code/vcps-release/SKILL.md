---
name: vcps-release
description: Move a release unit to production under Gate 6, and close the loop with post-release production evidence, per workflows/release.md. Use once every change in the unit has already reached its required gate outcomes via /vcps-feature, /vcps-bug, /vcps-review remediation, /vcps-tiny, or /vcps-hotfix.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py release-readiness-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), AskUserQuestion
---

# /vcps-release

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/release.md` in the *current target
repository*. **Read that file in full now**, plus
`standard/gates/gate-6-release.md` in full — this skill is a thin
dispatcher over both, not a restatement (`standard/VCPS.md`
`VCPS-CORE-003`).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-release.md`). **This skill never performs an actual
deployment** — Step 5 ("Deploy") is a human/infrastructure action this
skill does not and should not automate; its own job ends at a correctly
recorded Gate 6 outcome and go/no-go decision.

## 1. Assemble the release unit (Step 1)

Identify the exact revision and the full change set (work-item IDs) it
contains.

## 2. Confirm prerequisite gates (Step 2, `VCPS-GATE-032`)

Run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py release-readiness-check --target <repo> --release-revision <rev> --work-item-ref <id> [--work-item-ref <id> ...]
```
This mechanically checks, for every included work item: does each
applicable gate have a recorded outcome at all; is that outcome
`PASS`/`PARTIAL`/`NOT_APPLICABLE` (never `BLOCKED`/`NOT_EVALUATED`); was
it evaluated on *this* release revision (a mismatch is a staleness
**candidate**, not an automatic fail — `VCPS-EVD-050/051` may permit
carry-forward, which is your judgment, not the script's); and whether an
`HC-10` decision already exists on this revision. **Every `issue` this
reports must be resolved or explicitly justified before Gate 6 can
`PASS`** — do not proceed past an unresolved `issues` entry by assuming
it's fine.

## 3. Gate 6 (Step 3)

Execute `standard/gates/gate-6-release.md` at the depth required by the
highest change class and project level in the unit. Gate 6 is evaluated
**once per release unit**, against the full included set — not once per
change (`VCPS-GATE-020`).

## 4. Go/no-go — `HC-10` (Step 4)

Required at `L2`+. **A rejected decision or an unmet condition stops
deployment and leaves Gate 6 `BLOCKED`** — this is never inferred as
satisfied by default, and silence is not a decision (`VCPS-GATE-021`).
You (the agent) MUST NOT set this decision yourself.

## 5. Deploy (Step 5 — not this skill's job)

Only after Gate 6 permits it and every required checkpoint is approved
for this exact action. The actual deployment mechanism is outside this
skill's scope — report readiness and the recorded decision; do not
attempt to trigger a deployment pipeline from here.

## 6. Post-release observation (Step 6)

Collect `E5` evidence against each feature's success signals within its
defined observation window (`VCPS-G6-020`/`VCPS-G1-001` item 6). This
happens after real deployment, in a later session/run — this skill does
not simulate production observation.

## 7. Promote (Step 7)

Features with sufficient `E5` evidence and no open `CRITICAL`/`HIGH`
production finding → `PRODUCTION_PROVEN`. Before closing out, you MAY
run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check --target <repo>
```
to confirm your new release/promotion records resolve their own
cross-references.

## 8. On failure (Step 8)

Demote affected features per `standard/lifecycle.md` `VCPS-LC-010`; open
a `/vcps-bug` run for the underlying defect, or `/vcps-hotfix` if the
failure is itself a live production harm.

## Escalation / re-routing

A change in the unit has stale or missing required evidence →
`BLOCKED (DEPENDENCY)`; either re-verify that change (via its own
workflow) or remove it from the release unit and re-run
`release-readiness-check`.

## Exit

Release record `PASS`/`PARTIAL` with the go decision actually recorded —
never implied. `PRODUCTION_PROVEN` promotions are recorded separately as
their own evidence arrives: **a release being live is not, by itself,
`PRODUCTION_PROVEN` for any feature in it.**

## Never

- Never trigger an actual deployment from this skill.
- Never set an `HC-10` decision yourself, or treat silence as one.
- Never report Gate 6 `PASS` while `release-readiness-check` has an
  unresolved `issues` entry you haven't explicitly addressed.
- Never claim `PRODUCTION_PROVEN` from the release going live alone,
  without the feature's own `E5` observation-window evidence.

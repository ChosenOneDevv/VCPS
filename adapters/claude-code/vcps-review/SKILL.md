---
name: vcps-review
description: Examine an existing screen, module, or feature against its intended behavior, find and remediate genuine defects, and honestly record what remains uncertain, per workflows/review.md. Use when the user asks to review existing behavior, check whether something still works as intended, or audit a feature for correctness — not for a reported bug with a known symptom (use /vcps, which will route that to BUG) and not for a read-only VCPS-installation health check (use /vcps-audit).
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), AskUserQuestion
---

# /vcps-review

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/review.md` in the *current target repository*.
**Read that file in full now**, plus `workflows/bug.md` steps 3–6 (Step 4
below routes remediation through them) — this skill is a thin dispatcher
over both, not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-review.md`). Unlike `/vcps-audit`, most of this
workflow's actual work (reconstructing intent, reading code, gap
analysis) is inherently your own judgment — there is very little to
mechanize here, and this skill does not pretend otherwise.

## 1. Reconstruct intended behavior (Step 1, Gate 1 / `VCPS-G1-003`)

Cite every source you use (specs, tickets, tests, docs, UI copy, domain
rules, prior commits, owner statements) and its evidence tier. A
conflicting or absent source is an `EXTERNAL_ACCEPTANCE` ambiguity to
record, not something to resolve by guessing.

## 2. Inspect current implementation (Step 2)

Read the actual code path end to end for the scope, not just its entry
point. This is `E1` evidence.

Before judging staleness of anything you cite, you MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory --target <repo>
```
A `matches_head: false` entry is a staleness **candidate**
(`VCPS-EVD-050/051/053`), not a verdict — check its `scope` against what
actually changed.

## 3. Gap analysis (Step 3)

For each reconstructed behavior, compare expected vs. actual per
`standard/classifications.md`:
- Reproduced or statically demonstrated deviation → `DEFECT`.
- Intended behavior unknown/unconfirmed → `EVIDENCE_GAP` or
  `EXTERNAL_ACCEPTANCE`.
- Deliberate accepted tradeoff with prior acceptance evidence →
  `KNOWN_LIMITATION`.

This is entirely your judgment. No subcommand does gap analysis.

## 4. Remediate verified problems only (Step 4)

Only `DEFECT`-classified findings get remediated as code changes.
Route each fix through Gates 2–5 at the change class it requires — follow
`workflows/bug.md` steps 3–6 directly (same gate mapping `BUG` uses).
**Do not remediate `EVIDENCE_GAP` or `EXTERNAL_ACCEPTANCE` findings as if
they were confirmed defects** (`VCPS-CLS-003`/`AG-008`).

## 5. Regression evidence (Step 5)

`VCPS-G4-030` applies to each remediated defect: a reproduction test
where practical.

## 6. Security review (Step 6)

Inspect the reviewed scope using Gate 5's categories, including behavior
outside any remediation diff. Record findings/evidence for that broader
inspection; evaluate a Gate 5 outcome for each remediation diff per the
applicability matrix.

## 7. Record remaining evidence gaps (Step 7)

Every `EVIDENCE_GAP`/`EXTERNAL_ACCEPTANCE` not resolved this run stays
`OPEN` with an owner, or routes to the legacy registry if the scope is
pre-existing and outside this run's budget (same pattern as
`workflows/setup.md` `VCPS-SETUP-022`, cited not duplicated here).

Before closing out, you MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check --target <repo>
```
to confirm any new finding/evidence records you created actually
resolve their own cross-references.

## Exit

Per `workflows/review.md`'s own exit condition: **do not** report a scope
as "clean" or "fully verified" if any `EVIDENCE_GAP` remains open in it.
Report `PARTIALLY REVIEWED` with the gap list, or report full counts by
classification (`DEFECT`/`EVIDENCE_GAP`/`EXTERNAL_ACCEPTANCE`/
`KNOWN_LIMITATION`) with remediated items and their evidence.

## Escalation / re-routing

- A finding reveals a security exposure reachable in production now →
  treat as `HC-05`-relevant immediately; consider `/vcps` (which will
  route to `HOTFIX`) for the exposure, continue `REVIEW` for the rest.
- Reconstructed intent contradicts a registered invariant → `HC-08`.

## Never

- Never remediate an `EVIDENCE_GAP`/`EXTERNAL_ACCEPTANCE` as if it were a
  confirmed `DEFECT`.
- Never report "clean"/"fully verified" with an open `EVIDENCE_GAP` in scope.
- Never treat a stale-looking evidence entry as either definitely stale
  or definitely still valid without checking its actual scope.

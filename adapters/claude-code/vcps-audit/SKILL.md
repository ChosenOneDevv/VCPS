---
name: vcps-audit
description: Assess a repository, component, or VCPS installation itself without changing behavior, per workflows/audit.md. Produces a report, never remediation. Use when the user asks for an audit, a conformance check, a VCPS installation consistency check, or "how healthy is our VCPS state" — not for finding and fixing bugs (use /vcps for that).
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py gate-reference-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py baseline-history-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py record-history-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-diff-scan *), Bash(${CLAUDE_SKILL_DIR}/../vcps-setup/scripts/vcps_tool.py validate *), AskUserQuestion
---

# /vcps-audit

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/audit.md` in the *current target repository*.
**Read that file in full now** — this skill is a thin dispatcher over it,
not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).

**`VCPS-WF-AUDIT-001` is absolute: this workflow MUST NOT modify code,
tests, configuration, or behavior.** Every tool this skill pre-approves is
read-only. If you find yourself about to `Write`/`Edit` anything, STOP —
that need is out of scope for `AUDIT` and belongs in a `REVIEW` or `BUG`
run instead (per `workflows/audit.md`'s own escalation rule).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence yet (see
`evaluation/vcps-audit.md`).

## 1. Scope definition (Step 1)

State exactly what is in scope: the whole repository, one component, or
"the VCPS installation itself" (this skill's most common use, mirroring
`workflows/setup.md` Stage 11). Record what is explicitly out of scope
and why.

## 2. Evidence inventory (Step 2)

Run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory --target <repo>
```
This gives you every evidence record's tier, result, and recorded
revision, plus `matches_head` against the current `git HEAD`. Per
`VCPS-EVD-050/051/053`: a `matches_head: false` entry is a **staleness
candidate**, not a verdict — check its `scope` against what has actually
changed before concluding it is genuinely stale. Do not trust this
script's lack of a flag as proof of freshness either; it only compares
against `HEAD`, not against the specific consumer's actual dependency
scope.

## 3. Gate-outcome review (Step 3)

Run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py gate-reference-check --target <repo>
```
This flags gate records with structurally missing required fields
(`BLOCKED` without `reason_codes`, `PARTIAL` without `partial_gap`,
`NOT_APPLICABLE` without `applicability_basis`, Gates 4/5 without
`independence_mode`) and unresolved `evidence_refs`/`finding_refs`. It also
surfaces a **candidate inconsistency** when a `PASS` gate cites
`NOT_RUN`/`ERROR`/`INCONCLUSIVE` evidence (`VCPS-EVD-020`); review the record
context yourself rather than treating that mechanical match as a verdict.
**This is not re-running verification** — `workflows/audit.md` Step 3 is
explicit that `AUDIT` checks that verification claimed actually has
evidence on file, at `E1` review depth, never re-executing it.

## 4. Classification review (Step 4)

Read the findings in scope (`.vcps/findings/*.md`) directly. Check per
`standard/classifications.md`: no `EVIDENCE_GAP` silently marked
`RESOLVED` without evidence; no `DEFECT` reclassified without
reproduction (`VCPS-CLS-001`); `RISK_ACCEPTED` at `HIGH`+ severity has an
`HC-08` record. This is model judgment — no subcommand classifies this
for you.

## 5. Anti-gaming review (Step 5)

For changed tracked files, first look for whole-file test deletion or
movement out of a test path relative to the current `HEAD`:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-diff-scan --target <repo>
```
This surfaces filename-based `AG-001` candidates for staged and unstaged
deletions only; it cannot see already-committed deletions or every kind of
check removal. Review the actual diff regardless. For changed/added source
files, run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <file> [...]
```
This flags only the most literally-recognizable `AG-001`/`004`/`005`/`010`
patterns (`.skip(`, `|| true`, `continue-on-error: true`, etc.) as
**candidates**, per `standard/anti-gaming.md` `VCPS-AG-020/021` — a match
is not itself a violation; a legitimate recorded exception may cover it.
Most `AG-*` rules (assertion weakening, threshold lowering, mock
substitution) require semantic diff understanding this script does not
attempt — read the actual diffs in scope yourself for those.

## 6. Installation consistency (Step 6, when scope includes VCPS itself)

Run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check --target <repo>
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py baseline-history-check --target <repo>
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py record-history-check --target <repo>
${CLAUDE_SKILL_DIR}/../vcps-setup/scripts/vcps_tool.py validate --target <repo>
```
`orphan-check` finds references that don't resolve to any record this
script found (candidates, not automatic defects — it does not know about
legitimately withdrawn/reserved IDs). `baseline-history-check` compares a
tracked baseline with `HEAD`, surfacing edits to immutable observations,
history rewrites, and new additions needing provenance review; it cannot
compare a baseline that is new at `HEAD`, nor see committed changes before
that `HEAD`. `record-history-check` compares committed append-only histories
and immutable evidence/gate/approval records against the worktree; mismatches
are AG-011 candidates requiring review, not automatic violations. Its scope is
tracked Markdown under `.vcps/`, so it cannot establish history for new or
already-rewritten committed records. `vcps_tool.py validate` reuses the
setup adapter's own mechanical checks (ID uniqueness, required top-level
fields, plan-hash recomputation). Neither is the complete JSON-Schema/
cross-record validator deferred to roadmap Phase E — re-derive levels and
invariant impact paths yourself per `workflows/audit.md` Step 6 ("re-derive,
don't assume").

## 7. Report (Step 7)

Produce an audit report with: scope, coverage (numerator/denominator and
evidence basis — never a bare percentage without showing the count),
every gap and misclassification found, anti-gaming candidates (labeled as
candidates), and an explicit conformance statement per `VCPS-CORE-033`:
`FULL`, `PARTIAL`, or `NOT_CONFORMANT`. Never leave this implied.

## Never

- Never modify code, tests, configuration, or behavior under this skill.
- Never re-run verification and call the result an audit finding — that's
  `REVIEW`'s job if a gap is found here.
- Never report a bare coverage percentage without its numerator/denominator.
- Never treat an anti-gaming or orphan-reference candidate as a confirmed
  finding without your own review.
- Never claim `FULL` conformance while any discovered gap remains unlisted.

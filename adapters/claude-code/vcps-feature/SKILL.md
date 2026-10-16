---
name: vcps-feature
description: Build new behavior, or materially change intended behavior, under full gate discipline proportionate to risk, per workflows/feature.md. Use for new capability work, not for fixing a reported defect (use /vcps-bug) or a genuinely R0 cosmetic change (use /vcps-tiny).
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py escalation-check *), Bash(${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py project-context *), Bash(${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py segmentation-scan *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan *), AskUserQuestion
---

# /vcps-feature

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/feature.md` in the *current target
repository*. **Read that file in full now** — this skill is a thin
dispatcher over it, not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).
This is the highest-ceremony of the per-change workflows (the full
Gate 1–5 matrix, no reduced depth anywhere) — read
`standard/gates/README.md` §4 (applicability matrix) and each
`standard/gates/gate-N-*.md` you'll actually need before claiming any
gate outcome.

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-feature.md`). Every step below names which gate it
maps to; none of this skill's mechanical touchpoints make a gate
judgment for you — they only surface raw facts, same split as every
other component in this adapter.

## 1. Classify change risk class (Step 1, `standard/risk-model.md` §5)

Before anything else, determine the files this feature will plausibly
touch and run:
```
${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [...]
${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py project-context --target <repo>
${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py segmentation-scan --target <repo> --touched-path <path> [...]
```
`forced_r3: true` is a floor you MUST NOT lower. `critical_domains` are
candidates for your own impact-path tracing (`VCPS-RISK-002`), never an
auto-escalation by name. `segmentation-scan`'s overlaps are raw facts for
`VCPS-RISK-045`'s cumulative-effect judgment. Record the class
provisionally; re-check it continuously through the whole run — a
feature that starts `R1` and grows into touching an invariant's
enforcement path becomes `R3` mid-flight, not only at the end.

## 2. Gate 1 — Product Discovery (Step 2)

On `PASS`/`PARTIAL` → feature lifecycle state `SPECIFIED`. Full depth at
`R1`+; see `standard/gates/gate-1-product.md`.

## 3. Gate 2 — Architecture & Failure Design (Step 3)

Per the applicability matrix (`VCPS-G2-001`'s conditional trigger at
`R1`; required at `R2`/`R3`). See `standard/gates/gate-2-architecture.md`.

## 4. Implement (Step 4, Gate 3)

On `PASS`/`PARTIAL` → `CODED`. Before/after your own diff, you MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <file> [...]
```
as a candidate-only sanity check (see its own `note` field). See
`standard/gates/gate-3-implementation.md`.

## 5. Verify (Step 5, Gate 4)

See `standard/gates/gate-4-verification.md`. You MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory --target <repo>
```
to sanity-check staleness candidates on evidence you're citing. Actual
test/build execution goes through ordinary `Bash` permission prompts —
this skill ships no command-execution wrapper (same reasoning as
`/vcps-bug`'s `SKILL.md`).

## 6. Security review (Step 6, Gate 5 per matrix)

See `standard/gates/gate-5-security.md`.

## 7. `VERIFIED` (Step 7)

On Gates 4–5 `PASS` (or permitted `PARTIAL`, `gates/README.md` §3) on the
*same revision* as `CODED` → `VERIFIED`. Independence mode per
`standard/levels.md` §4 — record what was actually practiced
(`independence.md` `VCPS-IND-005`), not what was merely required.

## 8. Acceptance (Step 8, `HC-14`)

Obtain acceptance against *each* criterion from an Owner or delegated
acceptor → `ACCEPTED`. You (the agent) MUST NOT set this yourself
(`VCPS-LC-003`).

## 9. Hand off to `/vcps-release`

For Gate 6 and eventual `PRODUCTION_PROVEN`. Before closing out, you MAY
run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check --target <repo>
```
to confirm your new records resolve their own cross-references.

## Escalation / re-routing

- Discovery/implementation reveals a defect in *existing* unrelated
  behavior → split into a `/vcps-bug` run rather than folding it in
  (`VCPS-WF-003`), unless fixing it is required to implement this feature.
- Scope found to be `R0` throughout → re-route to `/vcps-tiny`.
- An invariant is touched that wasn't accounted for in Gate 1 → re-run
  Gate 1/2 at `R3`.

## Exit

`ACCEPTED` at minimum for the workflow to be considered complete.
`CODED`/`VERIFIED` are valid, honestly-reported stopping points when
explicitly scoped (e.g. acceptance deliberately deferred to a
stakeholder) — never report either state as "done" (`VCPS-LC-001`).

## Never

- Never claim a gate outcome stronger than the evidence you actually
  produced.
- Never set `ACCEPTED` or any lifecycle state past `VERIFIED` on your
  own authority.
- Never lower a provisionally `R3` classification without a recorded
  justification and, if lowering from `R3` specifically, `HC-09`.

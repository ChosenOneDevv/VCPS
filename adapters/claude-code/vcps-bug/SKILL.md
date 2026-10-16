---
name: vcps-bug
description: Fix a reported incorrect behavior, with reproduction before the fix and confirmed regression evidence after, per workflows/bug.md. Use when the user reports a specific defect with a symptom (not a general "review this area" request — use /vcps-review for that, which dispatches here only after it finds a confirmed DEFECT).
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(git worktree list --porcelain), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py evidence-inventory *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py orphan-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan *), AskUserQuestion
---

# /vcps-bug

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/bug.md` in the *current target repository*.
**Read that file in full now** — this skill is a thin dispatcher over it,
not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-bug.md`). Like `/vcps-review`, this workflow is mostly
your own judgment (reproduction, root-cause, fix). **Deliberately not
provided:** an automated "run the test command for me" helper. Running an
arbitrary project test command from inside a pre-approved script would
mean that command executes with no permission prompt at all, regardless
of what it actually does — exactly the mutation-budget-bypass/command-
injection shape this adapter's security posture exists to prevent
elsewhere (see `adapters/claude-code/lib/README.md` for the same
reasoning applied to evidence logic). Every actual test/build command you
run goes through Claude Code's ordinary, per-call `Bash` permission
prompt, same as any other command — this skill pre-approves only
read-only `git` inspection and the shared lib's three read-only
subcommands.

## 1. Confirm intent (Step 1, Gate 1)

Determine the intended behavior the report implies. Light depth unless
the report itself reveals ambiguity about what "correct" means — then
go to full Gate 1 depth rather than guessing.

## 2. Reproduce (Step 2, `VCPS-CLS-001`)

Establish `E2`+ evidence of the defect — actually run something and
observe the failure, not merely read code and conclude it looks wrong.
**If you cannot reproduce it: classify `EVIDENCE_GAP` (`INCONCLUSIVE`)
and stop here. Do not proceed to "fix" a guessed cause without owner
input** — this is the single most load-bearing instruction in this
workflow and the one most tempting to skip under time pressure.

## 3. Classify change risk class (Step 3, `VCPS-RISK-040/041`)

From what the fix will actually touch — never from how trivial the bug
*looks*. `AG-014`/`VCPS-RISK-040` forbid sizing down by diff size: a
one-line fix to an invariant's enforcement path is still `R3`.

## 4. Design (Step 4, Gate 2 when required)

Per the applicability matrix. At `R1`, apply `VCPS-G2-001`'s conditional
trigger. An `R2`/`R3` fix cannot mark Gate 2 `NOT_APPLICABLE` merely
because the design itself didn't change.

## 5. Fix (Step 5, Gate 3)

Before writing the fix, you MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <file> [...]
```
against the files you are about to touch, as a sanity check before and
after — a candidate match (`.skip(`, `|| true`, etc.) in your own diff is
worth noticing before you commit it, not just at `/vcps-audit` time.

## 6. Verify (Step 6, Gate 4, `VCPS-G4-030`)

Run the project's actual configured checks (its real `Bash` permission
prompt applies, as always). `VCPS-G4-030`: a reproduced `DEFECT` SHOULD
get a regression test (REQUIRED at `L3`/`R3` unless `HC-08` accepts the
gap) — apply this exactly as written, do not strengthen or soften it.

## 7. Security review (Step 7, Gate 5 when applicable)

A bug fix touching auth/data-access logic is `R2` at minimum, per
`workflows/bug.md` itself — re-check your Step 3 classification if you
didn't already account for this.

## 8. Confirm the fix (Step 8, `VCPS-G4-031`)

**The regression test MUST be confirmed to fail on the parent (pre-fix)
revision and pass on the fix revision** — not merely pass now. The safe
way to do this without touching your actual working tree: create an
isolated worktree at the parent revision, run the regression test there,
then remove it:
```
git worktree add --detach <tmp-dir> <parent-revision>
cd <tmp-dir> && <the project's real test command for this test> ; cd -
git worktree remove --force <tmp-dir>
```
Repeat (or reuse your already-fixed working tree) for the fix revision.
Record both results as evidence. A regression test that already passed
on the parent revision does not demonstrate anything — it is not
evidence of this fix, and `VCPS-G4-031` is not satisfied by skipping this
check because "it's probably fine."

## Escalation / re-routing

- Reproduction reveals the "bug" is actually missing/undefined
  specification → re-route the specification question through full
  Gate 1; consider whether this is really `FEATURE` work instead.
- Reproduction reveals a security exposure → Gate 5 is required
  regardless of the original triviality assumption; consider `/vcps`
  (which will route to `HOTFIX`) if the exposure is live now.
- Fix scope grows beyond the reported defect → `HC-13`.

## Exit

`RESOLVED` finding status requires remediation evidence at the level's
required tier **plus** regression evidence per `VCPS-CLS-031`. The
affected feature's lifecycle state follows `standard/lifecycle.md`'s
demotion/promotion rules — a `BUG` fix does not by itself re-promote a
demoted feature past `CODED` without its own fresh verification.

## Never

- Never proceed to fix a guessed cause when reproduction failed.
- Never size down the risk class because the diff looks small.
- Never report a regression test as satisfying `VCPS-G4-031` without
  actually having confirmed it fails on the parent revision.
- Never run an arbitrary project command from inside a pre-approved
  script path — every real command execution goes through an ordinary,
  visible `Bash` permission prompt.

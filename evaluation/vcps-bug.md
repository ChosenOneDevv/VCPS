# Evaluation record: Claude Code BUG workflow (`/vcps-bug`)

- Adapter version: `0.1.0-draft.6` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/bug.md`
- Date: 2026-10-06

## Provenance

New component. Second slice of roadmap Phase D (after `AUDIT`/`REVIEW`),
chosen next because it shares `workflows/bug.md`'s gate mapping with
`/vcps-review`'s own Step 4 dispatch target — building `BUG` now means
that shared Core document is exercised by two independent callers, not
just referenced by one.

## Scope, stated honestly

Like `/vcps-review`, `workflows/bug.md`'s eight steps are almost entirely
judgment: confirming intent, reproducing, classifying risk from what the
fix touches (not its apparent size), designing, fixing, verifying,
security review, and confirming the regression against the parent
revision. The three mechanical touchpoints it does use
(`evidence-inventory`, `orphan-check`, `antigaming-scan`) are the shared
helper `/vcps-audit` and `/vcps-review` already use, tested once in
`adapters/claude-code/lib/tests/run_tests.py`, not re-counted here.

**A deliberate design decision, not an oversight:** this skill does
**not** ship a mechanical helper that executes an arbitrary project test
command to automate `VCPS-G4-031`'s parent-fails/fix-passes confirmation,
even though that confirmation is itself genuinely mechanical (run a
command, compare two boolean results). Wrapping an arbitrary
caller-supplied command inside a script whose invocation is pre-approved
in `allowed-tools` would mean that command executes with **no permission
prompt at all**, regardless of what it actually does — exactly the
mutation-budget-bypass/command-injection risk this adapter's security
posture (see `adapters/claude-code/lib/README.md`'s reasoning, applied
here to a different mechanism) exists to prevent. `SKILL.md` instead
documents the safe manual procedure (an isolated `git worktree` at the
parent revision, the project's own already-permission-prompted test
command, teardown) and leaves every actual command execution behind
Claude Code's ordinary per-call `Bash` prompt.

## Results

Command: `python3 adapters/claude-code/vcps-bug/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Every pre-approved `Bash` entry is read-only `git` or the shared lib — never a generic command runner | STRUCTURAL_TEST | PASS | Direct structural proof of this record's own safety claim above, not just an assertion in prose. |
| S5 | Explicitly states why no command-execution helper is pre-approved | STRUCTURAL_TEST | PASS | |
| S6 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S7 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S8 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S9 | States the reproduce-before-fix rule | STRUCTURAL_TEST | PASS | "Do not proceed to fix a guessed cause without owner input." |
| S10 | States the risk-class-not-by-triviality rule | STRUCTURAL_TEST | PASS | `AG-014`/`VCPS-RISK-040` cited. |
| S11 | States the `VCPS-G4-031` parent-fails/fix-passes confirmation rule | STRUCTURAL_TEST | PASS | |
| S12 | `workflows/bug.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 12/12 pass. No `SIMULATED_EXECUTION` tests —
no workflow-specific mechanical logic exists beyond the shared lib's own
already-tested subcommands, by this record's own stated design decision.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** No `claude -p` run of this skill has been attempted. As with
`/vcps-review`, this is the highest-value live run to pursue among this
repository's workflow components: reproduction quality, risk
classification from actual impact (not diff size), and the worktree-
based regression confirmation procedure are all observable only in a
live run, not in structural testing.

## Known limitations and unresolved evidence

- No live run; reproduction/classification/fix quality entirely
  unverified.
- `VCPS-G4-031`'s confirmation procedure is documented, not automated;
  whether a live session actually follows the worktree-isolation
  procedure correctly (vs. e.g. forgetting to remove the temporary
  worktree, or running the wrong test command) is unverified.
- No coverage of the `HOTFIX`/`FEATURE` re-routing escalation paths this
  workflow's own "Escalation / re-routing" section names — those require
  a live run that actually hits one of those conditions to observe.

# Evaluation record: Claude Code REVIEW workflow (`/vcps-review`)

- Adapter version: `0.1.0-draft.4` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/review.md` (and, for
  remediation, `workflows/bug.md` steps 3–6, dispatched to directly rather
  than duplicated)
- Date: 2026-10-06

## Provenance

New component. Roadmap Phase D's first slice (REVIEW; see
`evaluation/vcps-audit.md` for the other half of this slice, built
together because both lean on the same shared mechanical helper,
`adapters/claude-code/lib/vcps_evidence.py`).

## Scope, stated honestly

`workflows/review.md`'s seven steps are almost entirely natural-language
judgment: reconstructing intended behavior from heterogeneous sources,
reading code end to end, comparing expected vs. actual, and deciding
remediation. Unlike `/vcps-audit`, there is very little here that is
genuinely mechanizable — this skill's own `SKILL.md` says so directly
rather than manufacturing a mechanical helper subcommand where none is
warranted. The two mechanical touchpoints it does use
(`evidence-inventory` for staleness candidates while reconstructing
intent, `orphan-check` for self-consistency of new records before
closing out) are the same shared helper `/vcps-audit` uses, and its own
test coverage (`adapters/claude-code/lib/tests/run_tests.py`) is not
re-counted here.

Remediation is **not** reimplemented by this skill: Step 4 dispatches
directly to `workflows/bug.md` steps 3–6 for gate mapping, the same
pattern `/vcps` uses for naming (not re-executing) a workflow document.

## Results

Command: `python3 adapters/claude-code/vcps-review/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | Remediation (Step 4) goes through Claude Code's own permission prompts, same defense-in-depth principle as every other skill in this adapter. |
| S4 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S5 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S6 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S7 | References `workflows/bug.md` for remediation gate mapping | STRUCTURAL_TEST | PASS | Confirms Step 4 dispatches rather than restates (`VCPS-CORE-003`). |
| S8 | States the `EVIDENCE_GAP`-as-`DEFECT` misuse rule | STRUCTURAL_TEST | PASS | `AG-008`/`VCPS-CLS-003` cited. |
| S9 | States the "never report clean with an open gap" exit rule | STRUCTURAL_TEST | PASS | |
| S10 | `workflows/review.md` exists | STRUCTURAL_TEST | PASS | |
| S11 | `workflows/bug.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 11/11 pass. No `SIMULATED_EXECUTION` tests are
defined for this skill specifically — there is no workflow-specific
mechanical logic to simulate beyond what
`adapters/claude-code/lib/tests/run_tests.py` already covers for the
shared helper both `/vcps-review` and `/vcps-audit` call.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** No `claude -p` run of this skill has been attempted. This is
the highest-value live run to pursue next among this repository's
workflow components: `REVIEW`'s correctness is almost entirely a
judgment call (intent reconstruction, gap classification), which is
exactly what structural/simulated testing cannot evaluate — unlike
`/vcps-audit`'s heavier mechanical core, `/vcps-review`'s real behavior
is observable only in a live run.

## Known limitations and unresolved evidence

- No live run; the actual judgment quality of intent reconstruction and
  gap classification is entirely unverified.
- No test exercises the Step 4 remediation path end to end (that would
  require a live run through `workflows/bug.md`'s own gates, which
  itself has no dedicated adapter skill yet — remediation is expected to
  proceed via the general-purpose agent following `bug.md` directly,
  same as `/vcps`'s own documented hand-off pattern).
- The `EXTERNAL_ACCEPTANCE` classification path (Step 1's "conflicting
  or absent source") has no coverage of any kind, mechanical or
  otherwise, beyond `SKILL.md`'s own instruction to record it.

# Evaluation record: Claude Code TINY workflow (`/vcps-tiny`)

- Adapter version: `0.1.0-draft.7` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/tiny.md`
- Date: 2026-10-06

## Provenance

New component. Third slice of roadmap Phase D (after `AUDIT`/`REVIEW`
and `BUG`), chosen next per the roadmap's own stated preference: the
lowest-ceremony remaining workflow, a deliberate contrast case after
three judgment-heavy slices.

## Scope, stated honestly

`TINY` is explicitly the most misuse-prone intent in
`workflows/README.md`'s list — the whole point of this skill is to keep
it honest, not to make non-trivial changes feel lighter. It reuses two
existing mechanical helpers rather than introducing a new one:
`vcps-router`'s `escalation-check` (the exact same `VCPS-RISK-041`
enforcement-path floor `/vcps` itself uses) for the mandatory Step 1
eligibility check, and the shared lib's `antigaming-scan` for an
optional Gate 3 sanity pass. Both are tested in their own components'
suites, not re-counted here.

## Results

Command: `python3 adapters/claude-code/vcps-tiny/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Every pre-approved `Bash` entry is read-only `git`, the router, or the shared lib | STRUCTURAL_TEST | PASS | |
| S5 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S6 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S7 | Router script exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S8 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S9 | States the Step 1 eligibility check is mandatory, not optional | STRUCTURAL_TEST | PASS | |
| S10 | Cites `VCPS-WF-TINY-001` | STRUCTURAL_TEST | PASS | |
| S11 | `workflows/tiny.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 11/11 pass. No `SIMULATED_EXECUTION` tests —
no workflow-specific mechanical logic exists beyond the already-tested
router/lib subcommands this skill reuses.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** The highest-value thing to observe in a live run here is
whether the model actually stops at Step 1 when `escalation-check`
reports `forced_r3: true`, rather than rationalizing past it under a
"it's just a tiny tweak" framing — this is exactly the failure mode the
mission's own `§17`/roadmap-Phase-C "undersell" case targets, now
applied to the one workflow explicitly designed to be exploitable that
way.

## Known limitations and unresolved evidence

- No live run; whether the model actually honors the mandatory Step 1
  stop (versus treating it as a suggestion) is entirely unverified.
- `escalation-check` only catches the one mechanical case
  (registered-invariant enforcement-path matches); the broader
  `VCPS-WF-TINY-001` triggers (logic/query/access-control/external-call/
  schema changes, oversized diffs, suspicious static-check failures) are
  model judgment with zero mechanical coverage, by design — these are
  not reducible to a deterministic check.

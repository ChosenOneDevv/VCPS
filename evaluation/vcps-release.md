# Evaluation record: Claude Code RELEASE workflow (`/vcps-release`)

- Adapter version: `0.1.0-draft.7` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/release.md`
- Date: 2026-10-06

## Provenance

New component, the last of roadmap Phase D's seven slices — closing
Phase D entirely. Required one new shared mechanical helper:
`adapters/claude-code/lib/vcps_evidence.py`'s `release-readiness-check`,
built because `VCPS-GATE-032`'s prerequisite-gate check ("every included
change's required Gate 1–5 outcomes are PASS/permitted-PARTIAL/
NOT_APPLICABLE on this revision, not stale") is genuinely mechanical —
it was validated directly against the Phase B worked example's own
`REL-006` record during authoring, which correctly surfaced every gate
gap that record's own narrative says is open (`BUG-005`'s Gate 3 not yet
filed, `FEAT-003`'s Gates 1/3/4 not yet filed, no `HC-10` decision on the
release revision) — proving the check's output matches a human-authored,
intentionally-incomplete release record's own documented state.

## Scope, stated honestly

This skill **never performs an actual deployment** — Step 5 is
explicitly named as outside its scope; its job ends at a correctly
recorded Gate 6 outcome and go/no-go decision. It also never sets the
`HC-10` decision itself (`VCPS-GATE-021`: a human release veto is never
inferred as satisfied by default).

## Results

Command: `python3 adapters/claude-code/vcps-release/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Every pre-approved `Bash` entry is read-only `git` or the shared lib | STRUCTURAL_TEST | PASS | |
| S5 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S6 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S7 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S8 | Explicitly states it never performs an actual deployment | STRUCTURAL_TEST | PASS | |
| S9 | States the agent MUST NOT set `HC-10` itself | STRUCTURAL_TEST | PASS | |
| S10 | States a live release is not by itself `PRODUCTION_PROVEN` | STRUCTURAL_TEST | PASS | |
| S11 | Cites the once-per-release-unit Gate 6 rule | STRUCTURAL_TEST | PASS | `VCPS-GATE-020` cited. |
| S12 | `standard/gates/gate-6-release.md` exists | STRUCTURAL_TEST | PASS | |
| S13 | `workflows/release.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 13/13 pass. `release-readiness-check`'s own
logic is tested in `adapters/claude-code/lib/tests/run_tests.py` tests
`21`–`25` (revision-mismatch staleness candidate, clean matching-
revision case, `BLOCKED` outcome flagged, missing work-item reference
flagged, `HC-10` decision surfaced), plus validated by hand against the
real Phase B worked example as described above — not re-counted here.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** The highest-value thing to observe live: whether the model
genuinely stops and reports `BLOCKED` when `release-readiness-check`
surfaces an unresolved gap, rather than narrating past it — the same
"never claim a PASS the evidence doesn't support" failure mode every
other component in this adapter is designed to resist.

## Known limitations and unresolved evidence

- No live run; whether the model actually treats every
  `release-readiness-check` issue as blocking (per this skill's own
  "Never" section) rather than selectively addressing some is
  unverified.
- Whether a `PARTIAL` gate outcome in the release unit is actually
  "permitted" per `gates/README.md` §3 is left entirely to model
  judgment — `release-readiness-check` reports the outcome value, not
  whether its `PARTIAL` is a legitimate one.
- This closes roadmap Phase D's seventh and final slice. None of the
  seven workflow executors (`SETUP` plus these seven) has any
  `LIVE_ADAPTER_EXECUTION` evidence beyond the setup adapter's own
  partial dry-run history (`evaluation/claude-code-adapter.md`) — Phase
  D's `CODED`/`TESTED_STRUCTURALLY` ceiling applies to all of them
  equally until live runs happen.

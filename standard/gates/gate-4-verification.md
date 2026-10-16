# Gate 4: Verification

Confirms evidence exists that the change behaves as intended, at the
independence mode and evidence tier the project level and change class
require.

## Required activities

**VCPS-G4-001.** Each critical invariant property named in Gate 2 MUST
have at least one evidence record on the change revision.

**VCPS-G4-002.** Every automated check applicable to the change scope MUST
be run. Results MUST be compared against the baseline; a newly introduced
failure blocks `PASS` (see `workflows/setup.md` Stage 8; this is the same
baseline comparison `VCPS-G3-009` uses).

**VCPS-G4-003. (Adversarial pass)** For `R1` and above, the verifier MUST
begin from intended behavior and attempt to refute the builder's claims
rather than confirm them, per the independence mode in effect
(`independence.md VCPS-IND-002`).

**VCPS-G4-004. (Invariant evidence for `R3`)** Each affected invariant
MUST be directly exercised by evidence specific to it — not merely
inferred from unrelated tests passing.

**VCPS-G4-005. (Business outcome)** Evidence MUST check business
outcomes, not merely a process exit code or HTTP status
(`evidence-model.md VCPS-EVD-022`).

**VCPS-G4-006. (Independence)** Verification MUST meet the independence
mode required for the project's level and the change's risk class
(`levels.md §4`).

**VCPS-G4-007. (`R0` light scope)** At `R0` (`gates/README.md §4`), Gate 4
is limited to running the applicable automated checks and confirming no
new failure versus the baseline (`VCPS-G4-002`); the adversarial pass
(`VCPS-G4-003`) and independence requirements beyond `I0`
(`VCPS-G4-006`/`levels.md §4`) do not apply at `R0`.

**VCPS-G4-030. (Regression test)** A `DEFECT` that has been reproduced
SHOULD receive an automated regression test covering the specific
failure; at `L3` on `R3` scope the regression test is REQUIRED unless
`HC-08` accepts the gap. Where a regression test is not practical (e.g. it
requires unavailable infrastructure), the reason MUST be recorded.

**VCPS-G4-031.** A regression test added under `VCPS-G4-030` MUST be
confirmed to fail on the parent (pre-fix) revision and pass on the fix
revision — demonstrating it actually reproduces the original failure, not
merely that it passes now.

## Outcomes

Per `gates/README.md §2`. `PASS` requires `VCPS-G4-001`–`006` satisfied
with no unresolved blocking finding and the required independence mode
actually practiced (`VCPS-G4-007` narrows this at `R0`). `PARTIAL` is
permitted only under `gates/README.md §3`'s conditions (e.g. a
baseline-inherited failure, or a regression test gap recorded under
`VCPS-G4-030`). `NOT_APPLICABLE` only per `gates/README.md §4`'s matrix.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-G4-003` through `006`
and `VCPS-G4-030` (including its parent-revision sentence) are recovered
verbatim from `standard/core-audit-0.1.md`'s per-line requirement
inventory. `VCPS-G4-030`'s `SHOULD`-in-general-but-`REQUIRED`-at-`L3`/`R3`
strength is independently corroborated by that same audit's finding
CA-001, which describes this exact rule while correcting an unrelated
document (`workflows/bug.md`) that had restated it at the wrong, fixed
strength — CA-001's description ("`SHOULD` in general and `REQUIRED` only
at `L3` on `R3` scope") is the source for this file's phrasing, not a
guess. `VCPS-G4-001` and `VCPS-G4-002` are reconstructed: `VCPS-G4-002`'s
existence and role are corroborated by `workflows/setup.md`'s own text
("the reference used by `VCPS-G3-009` and `VCPS-G4-002` comparisons going
forward," intact) and by a recovered sentence fragment ("to the change
scope MUST be run. Results MUST be compared against the baseline;"), but
the exact original wording around that fragment is reconstructed, not
quoted. `VCPS-G4-001`'s wording is built from a recovered fragment
("invariant property named in Gate 2 MUST have at least one evidence
record on") with reconstructed framing; its requirement-ID number is this
reconstruction's inference from numeric sequence, not recovered directly.

**2026-10-05, ratification pass.** Two gaps found by the requirement-graph
check, both in untouched original files: `VCPS-G4-007` is cited by
`workflows/tiny.md` ("Gate 4 (light) — VCPS-G4-007: run configured
checks, confirm no new failures vs. baseline") with no definition
anywhere in this file's first pass; added here directly from that
sentence. `VCPS-G4-031` is cited by `workflows/bug.md` ("the regression
test fails on the parent revision and passes on the fix revision
(VCPS-G4-031)") — the first reconstruction pass had folded this exact
content into `VCPS-G4-030`'s closing sentence instead of giving it its
own ID; it is now split out as its own rule, matching `bug.md`'s
`MUST`-level framing ("Confirm fix...") rather than the softer `SHOULD`
wording the first pass had attached to it.

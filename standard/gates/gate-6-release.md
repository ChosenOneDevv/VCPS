# Gate 6: Release

The human go/no-go decision gating deployment of a release unit. Evaluated
per release unit, not per change (`gates/README.md §5`).

## Required activities

**VCPS-G6-001.** A release unit is the set of changes being deployed
together; Gate 6 evaluates that set as a whole, against the highest
change class any included change carries (`workflows/README.md
VCPS-WF-010`: "`RELEASE` MUST record the highest class in its release
unit").

**VCPS-G6-011.** The release record MUST enumerate every included change
and its current gate outcomes on the release revision.

**VCPS-G6-012.** A release MUST NOT proceed while any included change has
an unresolved blocking finding, regardless of time pressure — this
requirement is explicitly not waivable by `HOTFIX`
(`workflows/hotfix.md`: "`HC-10` and `HC-03` are NOT waivable by
HOTFIX").

**VCPS-G6-020.** After release, observed production evidence (`E5`) MUST
be collected over the observation window defined in Gate 1 and linked
back to each included feature's record, so `PRODUCTION_PROVEN`
(`lifecycle.md §2`) can be assessed from it rather than assumed.

## Outcome table

**VCPS-GATE-021** (`gates/README.md §5`) owns the core rule: `PASS`
requires every required Gate 1–5 outcome on the release revision to be
`PASS` or a permitted `PARTIAL`, and an affirmative `HC-10` decision
(`APPROVED` or `APPROVED_WITH_CONDITIONS` with every condition met). A
`REJECTED` decision, an unmet condition, or no decision at all blocks
Gate 6 and the release — this is the human release veto, and it is never
satisfied by silence or by a missing record defaulting to "go."

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-G6-020` is recovered
verbatim (through "observed production evidence (`E5`) MUST be") from
`standard/core-audit-0.1.md`'s per-line requirement inventory; its
continuation is reconstructed from `standard/lifecycle.md`'s intact
`PRODUCTION_PROVEN` row, which already describes `E5` evidence "of the
feature's success signals over the observation window defined in Gate 1."
`VCPS-G6-001` is reconstructed from audit finding CA-019, which names it
directly as the source of the per-release-unit definition, combined with
`workflows/README.md VCPS-WF-010`'s intact "highest class" sentence.
`VCPS-G6-011` and `VCPS-G6-012`'s ID numbers are corroborated externally —
`workflows/hotfix.md` (intact) cites "`VCPS-G6-011`/`012` still apply"
under expedited `HOTFIX` release and separately states `HC-10`/`HC-03`
are not waivable — but their exact original wording is reconstructed from
that context, not quoted. The outcome-table correction this file
describes (`VCPS-GATE-021`, defined in `gates/README.md`) is grounded in
audit finding CA-037, a CRITICAL-severity finding against the *original*
(pre-correction) version of this exact file: the original Gate 6 `PASS`
row required only "a recorded decision" with no check that the decision
was actually affirmative, which CA-037 states "inverted the human release
veto." This reconstruction deliberately encodes CA-037's corrected
behavior, not the defective original — a human reviewer should know this
file's outcome logic is a *fix*, already applied here, not a faithful
copy of what was lost.

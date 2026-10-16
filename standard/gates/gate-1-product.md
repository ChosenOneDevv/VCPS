# Gate 1: Product

Confirms intended behavior and acceptance criteria are defined before
design or implementation proceeds.

## Required activities

**VCPS-G1-001.** Before implementation, record:

1. The intended behavior, in terms a non-builder reviewer could verify
   against.
2. Acceptance criteria the feature/change will be judged against.
3. Success signals and observation window, where the change is a
   `FEATURE` reaching `PRODUCTION_PROVEN` (`lifecycle.md §2`).
4. The change's risk classification (`risk-model.md`), with reasoning.
   This classification MUST cite impact-path evidence per
   `VCPS-RISK-010`, not assume the project's existing ratings apply
   unchanged to this change's specific path.

**VCPS-G1-002.** Where the user's own wording conflicts with what the
change actually does (e.g. "small tweak" that touches an enforcement
path), Gate 1 records the actual scope, not the requester's framing
(`workflows/README.md VCPS-WF-002`).

**VCPS-G1-003.** For `REVIEW` and `AUDIT`, intended behavior MUST be
reconstructed from the best available source (existing spec, tests,
product documentation, or direct owner statement) rather than invented by
the agent. Where sources conflict or are absent, the ambiguity MUST be
recorded as an `EVIDENCE_GAP`, not silently resolved by the agent's own
guess at what was intended.

## Outcomes

`PASS` — intended behavior, acceptance criteria, and risk classification
are recorded with their evidence basis. `PARTIAL` — recorded but with an
explicit gap (e.g. acceptance criteria incomplete), per `gates/README.md
§3`. `BLOCKED` — cannot proceed without a human decision (e.g. conflicting
stakeholder intent). `NOT_APPLICABLE` — only where `gates/README.md §4`'s
matrix marks Gate 1 not applicable (`R0`).

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-G1-001` (including the
item 4 impact-path citation sentence added per audit finding CA-016) and
`VCPS-G1-003` are recovered verbatim from `standard/core-audit-0.1.md`'s
per-line requirement inventory. `VCPS-G1-002` is reconstructed from
`workflows/README.md VCPS-WF-002` (intact) applied to the Gate 1 context,
not a recovered original line — no inventory line captured a Gate-1-local
statement of this rule, so this may duplicate rather than cite
`VCPS-WF-002`; a human reviewer should check whether the original file
instead cross-referenced it. The "Outcomes" section's specific wording is
reconstructed from `gates/README.md §2`'s outcome definitions applied to
this gate; it is not a recovered original passage.

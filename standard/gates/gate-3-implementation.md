# Gate 3: Implementation

Confirms the change is scoped, inspected, and free of fabrication and
verification-weakening patterns before verification begins.

## Required activities

**VCPS-G3-001. (Scope discipline)** The change MUST be limited to the
stated intent; incidental changes (reformatting of untouched files,
dependency bumps) MUST be separated or justified.

**VCPS-G3-002. (Read before write)** The builder MUST inspect existing
code, conventions, and tests in the affected area before modifying it, and
MUST follow existing conventions unless a recorded reason justifies
diverging from them.

**VCPS-G3-003. (No fabrication)** The builder MUST NOT introduce calls to
APIs, methods, configuration options, or dependencies that do not actually
exist or have not been verified to exist.

**VCPS-G3-004. (Dependencies)** New dependencies MUST be justified, pinned
per project convention, and checked against the project's existing
dependency and security posture before being added.

**VCPS-G3-005. (Error handling)** Errors MUST NOT be silently swallowed on
`R2`/`R3` paths. Failure paths named in Gate 2 MUST be implemented.

**VCPS-G3-006. (Secrets)** Secrets MUST NOT be committed, logged, or
embedded in source code, configuration, or test fixtures.

**VCPS-G3-007. (Anti-gaming)** The diff MUST be inspected for verification
weakening patterns (`anti-gaming.md §1`); each Gate 2 design property MUST
be traceable to the code implementing it.

**VCPS-G3-009. (Static checks against baseline)** Available lint and type
checks MUST be run on the revision and compared against the recorded
baseline (`workflows/setup.md` Stage 6). A newly introduced lint/type
failure blocks `PASS`; a pre-existing (baseline) failure in the same check
is reported with its original result per `VCPS-SETUP-019` and does not by
itself block `PASS`, but yields `PARTIAL` with a linked finding naming the
inherited failure.

**VCPS-G3-010. (`R0` light scope)** At `R0` (`gates/README.md §4`), Gate 3
is limited to: scope discipline (`VCPS-G3-001`), secrets (`VCPS-G3-006`),
anti-gaming inspection (`VCPS-G3-007`), and static checks run
(`VCPS-G3-009`) — the full diff/dependency/error-handling/traceability
activities (`VCPS-G3-002`–`005`) are not required at `R0`, since by
definition an `R0` change touches no enforcement path.

## Outcomes

**Shared rule:** `PASS` excludes any unresolved finding in scope at or
above the blocking severity threshold (`gates/README.md §2`). Gate 3
`PASS` additionally requires passing static checks on newly introduced
code per `VCPS-G3-009`; a baseline (pre-existing) static-check failure
does not itself block `PASS` but is named in a `PARTIAL` outcome's
finding — the raw check result is never silently reported as passing
(`VCPS-SETUP-042` preserves raw results). `BLOCKED` applies per
`gates/README.md §2`'s reason codes.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-G3-001` through
`VCPS-G3-007` are recovered verbatim (with minor connective-word
reconstruction to bridge a handful of uncaptured lines between numbered
items) from `standard/core-audit-0.1.md`'s per-line requirement
inventory. The second clause of `VCPS-G3-007` ("each Gate 2 design
property MUST be traceable...") is stitched from a recovered fragment at
a later line number with no requirement-ID marker in between it and
`VCPS-G3-007`'s header — it is plausibly `VCPS-G3-007`'s own continuation
(both concern diff inspection) but could instead belong to an
unrecovered `VCPS-G3-008`; treat that attribution as uncertain.
`VCPS-G3-009`'s ID is corroborated externally: `workflows/setup.md`
`VCPS-SETUP-019` (intact) cross-references "`VCPS-G3-009`'s 'baseline'
comparison" by name, and audit finding CA-025 describes its corrected
behavior in prose ("Gate 3 PASS requires passing static checks... its
PARTIAL row names inherited failures... the check remains FAIL [for the
raw baseline record]"). This file's §"Outcomes" section is built from
CA-025's description, not a verbatim recovery, and should be treated with
the same caution as the rest of this reconstruction's non-quoted prose.

**2026-10-05, ratification pass.** `VCPS-G3-010` was added after the
requirement-graph check found it cited by name in `workflows/tiny.md`
(untouched, intact — "Gate 3 (light) — VCPS-G3-010 scope: scope
discipline, no secrets, no anti-gaming weakening, static checks run."),
with no corresponding definition anywhere in this file's first
reconstruction pass. Its content here is built directly from that
citing sentence, cross-referenced against `gates/README.md §4`'s `R0`
row ("required, light scope"), which this ID evidently names.

# Gate 2: Architecture

Confirms a design addresses trust boundaries, failure modes, and
critical-state mechanisms before implementation, for changes where that
design work actually matters (see applicability, `gates/README.md §4`).

## Applicability

**VCPS-G2-001.** `NOT_APPLICABLE` at `R0`. At `R1`, required only where the
change touches a critical-state mechanism or trust boundary — a change
touching authoritative state on an `R2`/`R3` path, the design MUST state
how each applicable property below (§§2–4) is addressed; at `R2`/`R3`,
always `REQUIRED`.

## Required design properties

**VCPS-G2-011. (Trust boundaries)** The design MUST identify each trust
boundary and MUST treat frontend/client input, external provider
responses, and other untrusted input (`glossary.md` "Untrusted input") as
unvalidated until the design states how it is checked at the boundary.

**VCPS-G2-012. (Failure design)** The design MUST enumerate failure modes
for the operations it introduces or changes, and — for any operation
involving a migration, destructive action, or external transaction —
MUST specify: forward plan, backward/rollback or forward-fix plan, data
integrity handling during the transition, and what happens if the
operation fails partway.

**VCPS-G2-010. (Critical state engineering)** For a critical state change
(an operation on authoritative data, `risk-model.md` D1/D2/D5), the
design MUST state how each of the following is engineered, not assumed:
authorization (who may invoke it), isolation (concurrent/cross-tenant
access cannot corrupt it), atomicity (it either fully applies or fully
does not), idempotency/concurrency (repeated or concurrent invocation
behaves safely), observability (it can be detected/audited after the
fact), and recovery (how to detect and correct it if it goes wrong).

**VCPS-G2-014. (Privileged AI actions)** For privileged AI-initiated
actions MUST define: the action allowlist, limits, human approval
thresholds, and how the action is logged for later audit.

**VCPS-G2-015.** For each property above, the design MUST name the
verification method Gate 4 will use to confirm it was actually built as
designed, not merely described.

- At `L3` with `R3`, the design MUST be reviewed at independence mode `I1`
  or higher (`independence.md`).

## Outcomes

Per `gates/README.md §2`. `PASS` requires every applicable property above
addressed with a named verification method. `PARTIAL` requires the gap
recorded per `gates/README.md §3`. `NOT_APPLICABLE` only per `VCPS-G2-001`.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-G2-011`, `VCPS-G2-012`
(through "MUST specify: forward plan..."), `VCPS-G2-015`, and the closing
`L3`/`R3` independence bullet are recovered verbatim from
`standard/core-audit-0.1.md`'s per-line requirement inventory.
`VCPS-G2-001`'s applicability rule is reconstructed from a recovered
fragment ("authoritative state on an R2/R3 path, the design MUST state
how each of") combined with audit finding CA-022's prose description of
the corrected behavior ("R2/R3 remediation always evaluates Gate 2... R1
retains the conditional VCPS-G2-001 trigger") — the ID number
`VCPS-G2-001` and its role as *the* trigger condition are stated directly
by CA-022, but the exact original sentence boundaries are not recoverable.
`VCPS-G2-014`'s content (the AI-action allowlist/limits/approval-threshold
sentence) is recovered verbatim as a sentence fragment, but **its
requirement ID is this reconstruction's inference**, not recovered — the
inventory capture does not include the line carrying its
`**VCPS-G2-0NN.**` label. The gap between `VCPS-G2-001` and `VCPS-G2-011`
(ten unused numbers) is real and unexplained: nothing recovered indicates
what, if anything, `VCPS-G2-002`–`VCPS-G2-009` contained, and this file
does not guess at filling it. A human reviewer should treat this file's
ID numbering and the §"Required design properties" boundaries as
lower-confidence than its individual recovered sentences.

**2026-10-05, ratification pass.** `VCPS-G2-010` was one of the ten
previously-unexplained numbers above — it is now resolved, not guessed:
`standard/principles.md` (untouched, intact) cites it by name at P-07,
"Critical state changes are engineered, not hoped for. Authorization,
isolation, atomicity, idempotency/concurrency, observability, recovery,"
with a direct link to this file. That six-item list is quoted verbatim
from `principles.md` as this rule's content; only the surrounding
definition/framing sentence is this reconstruction's own. The same
pass's citation audit also independently corroborates `VCPS-G2-011`'s
scope: `principles.md` P-06 ("Untrusted by default... LLM output are
untrusted inputs") cites both this file and `gates/gate-5-security.md`
together, matching `gate-5-security.md VCPS-G5-008`'s LLM-output-trust
rule, which was written independently during this same pass before this
citation was found.

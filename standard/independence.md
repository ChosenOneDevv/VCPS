# Builder/Verifier Independence

This document owns: independence modes (`I0`–`I4`) between the party that
builds a change and the party that verifies it. Required minimums per
level and change class are owned by
[levels.md §4](levels.md#4-independence-minimums).

## 1. Principle

**VCPS-IND-001.** VCPS MUST NOT require any particular vendor, model, or
agent identity to satisfy an independence mode. What matters is the
functional separation described below, not which product provides it.

## 2. Modes

| Mode | Separation |
|------|------------|
| `I0` | None required. The builder's own report is accepted without a distinct verification pass. Appropriate only for `R0` changes, or `R1` at `L1` (see `levels.md §4`). |
| `I1` | Same identity MAY build and verify, but verification is a distinct, disclosed phase: the verifier MUST begin from intended behavior (not from the implementation just produced) and MUST attempt to refute the builder's claims rather than confirm them. |
| `I2` | The verifier MUST be a distinct identity/session from the builder, and MUST NOT be given the builder's implementation approach or reasoning before forming its own verification judgment; it MAY read it afterward to reconcile findings. |
| `I3` | As `I2`, and the verifier MUST use a materially different method, tool, or environment than the builder used, to reduce correlated blind spots (e.g. a different test approach, a different reviewer tool, not merely a different session of the same approach). |
| `I4` | Independent verification wholly outside the building party's control — an external human reviewer, a separate team, or a formal/independent audit process not directed by whoever built the change. |

**VCPS-IND-002.** At `I1` and above, the verifier MUST begin from intended
behavior (the specification/acceptance criteria), not from the
implementation itself, and MUST attempt to refute the builder's claims
rather than confirm them.

**VCPS-IND-003.** At `I2` and above, the verifier MUST NOT be given the
builder's implementation approach or reasoning before forming its own
independent judgment. It MAY read it afterward to reconcile.

**VCPS-IND-004.** A verifier MUST NOT modify the change under verification
while acting in the verifier role; doing so collapses the independence the
mode exists to provide.

**VCPS-IND-005.** At `I1`, the producer and verifier MAY be the same
identity, but the switch between builder phase and verifier
phase MUST be disclosed. At `I2` or higher, the verifier MUST be a distinct
identity from the builder. A gate or evidence record's claimed mode
MUST match what actually happened, not what was required; claiming a higher
mode than was actually practiced is a finding against the record, not a
formality.

## 3. Recording

**VCPS-IND-010.** Each gate record for Gates 4 and 5 MUST record the
independence mode actually used. Where the required mode could not be met
(e.g. no distinct reviewer), the gap MUST be recorded as an `EVIDENCE_GAP`
and the gate MUST NOT exceed `PARTIAL`. At `L3` with an `R3` change, the
gate MUST be `BLOCKED` until independence at the required mode is actually
achieved — a recorded gap does not substitute for it at that level/class.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. `VCPS-IND-001` through
`VCPS-IND-005` and `VCPS-IND-010` are recovered verbatim from
`standard/core-audit-0.1.md`'s per-line requirement inventory, which
quoted these exact lines (including the audit's own correction to
`VCPS-IND-005` noted there as CA-009) before the file was lost. The §2
mode table's one-line descriptions for `I1`/`I2` restate the recovered
`VCPS-IND-002`/`003`/`005` text directly. `I0`, `I3`, and `I4`'s
descriptions have no recovered source text — no inventory line captured
them — and are reconstructed from how `levels.md §4` (intact) uses the
five-mode ladder (`I0` for `R0`/`L1`-`R1`, up to "`I3` or `I4` SHOULD" at
`L3`/`R3`) plus the ordinary meaning of an ascending independence scale.
These three SHOULD be treated as the lowest-confidence part of this file
and reviewed against the original if a backup ever surfaces. This file
deliberately does not name any specific agent, product, or session
mechanism (per `VCPS-CORE-001`); any adapter's mapping of these modes onto
its own execution primitives belongs in that adapter's own documentation
(see `adapters/claude-code/vcps-setup/references/orchestration.md` for an
example, which the Claude Code adapter's OQ-005 resolution already
points to in `standard/open-questions.md`).

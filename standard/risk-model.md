# Risk Model

This document owns: impact dimensions, the project risk profile, critical
invariants, change risk classes (`R0`–`R3`), and escalation rules.
Project levels (`L1`–`L3`) are derived here and defined in [levels.md](levels.md).

## 1. Impact, not keywords

**VCPS-RISK-001.** Risk classification MUST be based on the actual impact of
failure, determined by tracing what the system does — data it writes, money or
goods it moves, permissions it grants, actions it takes, and who is affected.

**VCPS-RISK-002.** Risk classification MUST NOT be derived solely from the
presence of keywords, dependency names, or directory names (for example a
`payments/` folder, a `stripe` dependency, or the word "admin"). Keywords MAY
be used to find candidates for inspection; the classification MUST cite the
impact path that justifies it.

*Informative example:* A repository containing a `billing/` directory that only
renders a static pricing page has no financial-state impact. A repository with
no "payment" keyword that decrements a stored balance on API calls does.

## 2. Impact dimensions

Each dimension is rated `0` (none) to `3` (severe).

| ID | Dimension | 3 = severe, examples |
|----|-----------|----------------------|
| D1 | **Data integrity** | Corruption or loss of authoritative records; irreversible writes. |
| D2 | **Financial / accounting state** | Money, balances, invoices, ledgers, pricing, refunds. |
| D3 | **Security & access** | Authentication, authorization, tenant isolation, secrets, privilege. |
| D4 | **Privacy & compliance** | Personal / regulated data, audit trails, retention, legal obligations. |
| D5 | **Physical / inventory state** | Stock, reservations, fulfillment, real-world side effects. |
| D6 | **Reversibility** | Destructive operations, migrations, external transactions that cannot be undone. |
| D7 | **Blast radius** | Number of users / tenants / systems affected by one failure. |
| D8 | **Autonomous action** | Privileged AI-initiated actions, automated decisions affecting people or money. |
| D9 | **Availability dependence** | Business or safety reliance on the system being up. |

**VCPS-RISK-010.** Each non-zero rating MUST cite at least one impact path
(code location, data store, or external interaction) as `E1 STATIC` evidence
or stronger. A rating with only `E0 CLAIMED` support MUST be recorded as an
`EVIDENCE_GAP` and the rating MUST be treated as the higher of the candidate
values until resolved.

## 3. Project level derivation

**VCPS-RISK-020.** The project (or component) level is derived from the
dimension ratings:

| Condition | Level |
|-----------|-------|
| Any dimension rated `3`, **or** two or more of D1–D6, D8 rated `2` | `L3` |
| Any dimension rated `2`, **or** the system is used by people other than its builders with persistent data | `L2` |
| Otherwise | `L1` |

**VCPS-RISK-021.** A repository MAY classify components separately. Where a
lower-level component can affect a higher-level component's invariant
(shared database, shared credentials, shared deploy unit), the lower-level
component MUST be treated at the higher level for changes on that shared path.

**VCPS-RISK-022.** Lowering a project or component level requires checkpoint
`HC-09`. Raising it does not.

## 4. Critical invariants

**VCPS-RISK-030.** An `L2` or `L3` project MUST maintain a critical invariant
registry. Each entry MUST include: identifier (`INV-<NNN>`), statement as an
assertion, owner, impact dimensions, enforcement path (files, schema objects,
configuration, checks), and required evidence for changes on the path.

**VCPS-RISK-031.** At `L3`, every dimension rated `3` MUST be covered by at
least one registered invariant, or an `EVIDENCE_GAP` explaining why none has
been identified yet.

*Informative examples:* "A tenant can never read another tenant's rows."
"Ledger entries for a transaction sum to zero." "An order cannot reserve more
stock than available." "A refund cannot exceed the captured amount."
"An AI agent cannot issue a refund above N without human approval."

## 5. Change risk classes

Every change receives a class. The class drives gate applicability
([gates/README.md](gates/README.md)). The project level drives evidence
strength ([levels.md](levels.md)).

| Class | Name | Definition |
|-------|------|------------|
| `R0` | TRIVIAL | No behavior change reachable by users or systems: copy, styling, comments, docs, formatting — **and** touches no enforcement path. |
| `R1` | STANDARD | Behavior change confined to low-impact paths; no critical invariant, trust boundary, schema, or external transactional integration touched. |
| `R2` | SENSITIVE | Touches a trust boundary, authentication/authorization surface, persistent schema, external integration, or a path rated `2` in any dimension. |
| `R3` | CRITICAL | Touches an enforcement path of a registered critical invariant, a dimension rated `3`, a destructive operation, a migration on authoritative data, or privileged AI action. |

**VCPS-RISK-040.** The change class MUST be determined from what the change
touches, not from its size. Diff size MUST NOT lower a class.

**VCPS-RISK-041. (Escalation)** A change MUST be raised to `R3` if it modifies
any file, schema object, configuration, or check listed in a critical
invariant's enforcement path, including changes to tests that verify that
invariant. *Example:* a one-line CSS-adjacent change that also alters a
`disabled` attribute guarding a duplicate-payment button is `R3`.

**VCPS-RISK-042.** When the class is uncertain, the higher candidate class MUST
be used until evidence supports the lower one.

**VCPS-RISK-043.** A change's class MAY be re-evaluated during work. If it
rises, all gates required by the new class MUST be evaluated before the change
leaves its workflow. If an agent wishes to lower it, the agent MUST record the
justification; lowering from `R3` requires `HC-09`.

**VCPS-RISK-044.** Changes to VCPS artifacts that alter risk profile, level,
invariant registry, gate policy, or checkpoint pre-authorizations are `R2` at
minimum.

**VCPS-RISK-045. (Segmentation / cumulative effect)** Classification MUST
consider other pending or recently-merged changes that are part of the same
logical unit of work (same feature, ticket, or branch lineage). An agent
MUST NOT segment a change whose combined effect would be `R2`/`R3` into
separate, lower-classified changes to avoid required gates. Where
segmentation is suspected, the cumulative effect of the related sequence
governs classification, not any single slice of it in isolation.

## 6. Unknown impact

**VCPS-RISK-050.** If an impact path cannot be traced (missing code,
generated code, opaque external service), the gap MUST be recorded as an
`EVIDENCE_GAP`, and classification MUST assume the plausible worst case among
the evidence-supported candidates.

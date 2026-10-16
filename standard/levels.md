# VCPS Levels

This document owns project levels and the minimum evidence, independence, and
blocking expectations that vary by level. How a level is *derived* is owned by
[risk-model.md](risk-model.md#3-project-level-derivation).

## 1. Levels

| Level | Name | Typical shape (informative) |
|-------|------|-----------------------------|
| `L1` | Low-risk application | Prototypes, internal tools without authoritative data, static or content sites, personal projects. Failures are cheap and reversible. |
| `L2` | Production application | Real users, persistent data, authentication, ordinary business logic. Failures are costly but bounded and recoverable. |
| `L3` | Critical business application | Combinations of multi-tenancy, authorization, financial/accounting state, payments, inventory, destructive operations, database migrations on authoritative data, privileged AI actions, external transactional providers, compliance-sensitive workflows. Failures cause irreversible, financial, legal, or cross-tenant harm. |

**VCPS-LVL-001.** A project MUST record its level and the risk-profile
evidence supporting it before any workflow other than `SETUP` or `AUDIT` claims
VCPS conformance.

**VCPS-LVL-002.** The level is a property of a project or component, not of a
change. A change's burden is determined by both the level and the change risk
class ([risk-model.md §5](risk-model.md#5-change-risk-classes)).

## 2. Minimum evidence tier for verification

Minimum evidence tier (see [evidence-model.md](evidence-model.md)) required for
a gate's required assertions to count toward `PASS`.

| Assertion kind | L1 | L2 | L3 |
|----------------|----|----|----|
| Build, type check, lint, unit tests | `E2 LOCAL` | `E3 CI` | `E3 CI` |
| Integration / behavior tests for the change | `E2 LOCAL` | `E3 CI` | `E3 CI` |
| Invariant assertions (`R3` changes) | n/a | `E3 CI` | `E3 CI` at required fidelity (§3) |
| Manual / exploratory verification | `E2 LOCAL` | `E2 LOCAL` with recorded steps | `E2 LOCAL` with recorded steps **and** independent verifier |
| Real external provider behavior | `E2 LOCAL` against sandbox, if used | `E4 EXTERNAL` or provider sandbox `E2`+ | `E4 EXTERNAL` before `ACCEPTED` |
| Feature acceptance | Owner `E4` (MAY be merge approval) | Owner `E4` | Owner `E4` with acceptance criteria listed |
| Production success | `E5` SHOULD | `E5` for `PRODUCTION_PROVEN` | `E5` for `PRODUCTION_PROVEN` with defined window |

**VCPS-LVL-010.** Where no CI exists, an `L2`/`L3` project MAY substitute
`E2 LOCAL` evidence only if the gap is recorded as an `EVIDENCE_GAP` with an
owner. Such gates MUST NOT exceed `PARTIAL`.

## 3. Fidelity minimums (L3)

**VCPS-LVL-020.** At `L3`, assertions about concurrency, transaction
isolation, locking, migration behavior, or query semantics MUST be evidenced on
the same database engine family and major version as production (or a
documented compatible one). Embedded, in-memory, or emulated engines MAY
supplement but MUST NOT replace this evidence. See
[evidence-model.md §5](evidence-model.md#5-scope-and-fidelity).

**VCPS-LVL-021.** At `L3`, assertions about external transactional providers
MUST NOT be satisfied by mocks alone before the feature is `ACCEPTED`.

## 4. Independence minimums

| Change class | L1 | L2 | L3 |
|--------------|----|----|----|
| `R0` | `I0` | `I0` | `I0` |
| `R1` | `I0` | `I1` | `I1` |
| `R2` | `I1` | `I1` | `I2` |
| `R3` | `I1` | `I2` | `I2`, and `I3` or `I4` SHOULD |

Modes are defined in [independence.md](independence.md).

## 5. Blocking severity threshold

A finding blocks gate `PASS` when its severity is at or above the threshold.
Severities are defined in [classifications.md](classifications.md#3-severity).

| Level | Blocking at or above |
|-------|----------------------|
| `L1` | `CRITICAL` |
| `L2` | `HIGH` |
| `L3` | `HIGH`; `MEDIUM` when the finding is on an `R3` scope |

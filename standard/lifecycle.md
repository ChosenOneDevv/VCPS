# Feature Lifecycle

This document owns feature lifecycle states, transitions, and demotion.

## 1. States

| State | Meaning |
|-------|---------|
| `PROPOSED` | Intent recorded; not yet specified. |
| `SPECIFIED` | Intended behavior and acceptance criteria defined (Gate 1, and Gate 2 when applicable). |
| `CODED` | Implementation exists on a recorded revision and passed Gate 3. **Working, not done.** |
| `VERIFIED` | Required verification and security evidence exists for the revision (Gates 4–5). |
| `ACCEPTED` | An authorized human (or required external party) accepted the feature against its acceptance criteria. |
| `PRODUCTION_PROVEN` | Released and observed functioning correctly in production. |
| `WITHDRAWN` | Abandoned or removed; record retained. |

`CODED`, `VERIFIED`, `ACCEPTED`, and `PRODUCTION_PROVEN` are the minimum states
every conforming implementation MUST support. `PROPOSED`, `SPECIFIED`, and
`WITHDRAWN` MAY be collapsed at `L1`.

## 2. Transition requirements

Required gates are those applicable for the change class per
[gates/README.md §4](gates/README.md#4-applicability-matrix). Evidence tiers are
per [levels.md §2](levels.md#2-minimum-evidence-tier-for-verification).

| To state | Requirements |
|----------|--------------|
| `SPECIFIED` | Gate 1 `PASS` or `PARTIAL`; Gate 2 `PASS`/`PARTIAL`/`NOT_APPLICABLE`. |
| `CODED` | Implementation on a recorded revision; Gate 3 `PASS` or `PARTIAL`. |
| `VERIFIED` | Gates 4 and 5 each `PASS`, permitted `PARTIAL`, or `NOT_APPLICABLE` where the applicability matrix allows, on the **same revision** as `CODED`; no open blocking finding; independence per [levels.md §4](levels.md#4-independence-minimums). `PARTIAL` is permitted only under [gates/README.md §3](gates/README.md#3-partial-progression). |
| `ACCEPTED` | `VERIFIED`; `E4 EXTERNAL` acceptance record from the Owner or delegated acceptor (checkpoint `HC-14`) referencing each acceptance criterion; open `EXTERNAL_ACCEPTANCE` findings resolved or `RISK_ACCEPTED`. |
| `PRODUCTION_PROVEN` | Released through a Gate 6 `PASS`; `E5 PRODUCTION` evidence of the feature's success signals over the observation window defined in Gate 1; no open `CRITICAL`/`HIGH` production finding on the feature. |

**VCPS-LC-001.** A feature MUST NOT be reported as done, complete, finished,
verified, or production-ready unless it is in the corresponding state with its
evidence recorded. Reporting language MUST use the state name when precision
matters.

**VCPS-LC-002.** States MUST NOT be skipped. A feature MAY transition through
several states in one workflow run if each state's requirements are met.

**VCPS-LC-003.** An agent MUST NOT move a feature to `ACCEPTED` or
`PRODUCTION_PROVEN` on its own authority. `ACCEPTED` requires a human or
external party; `PRODUCTION_PROVEN` requires production observation.

## 3. Demotion

**VCPS-LC-010.** A feature MUST be demoted when its supporting evidence becomes
stale ([evidence-model.md §6](evidence-model.md#6-revision-binding-and-staleness))
or a blocking finding is opened against it:

| Event | Demote to |
|-------|-----------|
| Change in scope after `VERIFIED`, before re-verification | `CODED` |
| Blocking `DEFECT` opened | `CODED` (or `SPECIFIED` if the specification is wrong) |
| Acceptance criteria changed | `VERIFIED` (if still verified) |
| Production regression / incident attributed to the feature | `CODED` (defect must be fixed and re-verified before re-reaching `VERIFIED`/`ACCEPTED`) |
| Rollback of the feature | `ACCEPTED` or lower per remaining evidence |

**VCPS-LC-011.** Demotion MUST be recorded with cause. Demotion MUST NOT
require human approval; promotion beyond `VERIFIED` does.

## 4. Feature record

**VCPS-LC-020.** A feature record MUST include: `id`, `title`, `state`,
`level`/component, acceptance criteria (identified), linked invariants,
linked changes and revisions, gate records, evidence references, open
findings, state history, and (for `PRODUCTION_PROVEN`) success signals and
observation window.

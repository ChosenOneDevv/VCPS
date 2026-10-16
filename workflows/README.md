# Workflows

Workflows apply the Core Standard to a user intent. They define *sequence*;
the Core defines *requirements*. A workflow MUST NOT weaken a Core requirement
(VCPS-CORE-003 applies equally to workflows).

## 1. Intents

| Intent | Use when | Document |
|--------|----------|----------|
| `SETUP` | Installing, adopting, upgrading, or repairing VCPS in a repository. | [setup.md](setup.md) |
| `FEATURE` | Building new behavior or changing intended behavior. | [feature.md](feature.md) |
| `REVIEW` | Examining and remediating an existing screen/module against its intended behavior. | [review.md](review.md) |
| `BUG` | Fixing a reported incorrect behavior. | [bug.md](bug.md) |
| `TINY` | Making an `R0` change. | [tiny.md](tiny.md) |
| `HOTFIX` | Urgent production remediation under time pressure. | [hotfix.md](hotfix.md) |
| `AUDIT` | Assessing a repository, component, or VCPS installation without changing behavior. | [audit.md](audit.md) |
| `RELEASE` | Moving a release unit to production. | [release.md](release.md) |

## 2. Intent classification

**VCPS-WF-001.** Before starting work, the executor MUST classify the request
into exactly one primary intent and record it. Requests spanning intents MUST
be split into separate workflow runs or handled by the stricter intent.

**VCPS-WF-002.** The user's wording is input, not authority, for intent
classification. A request phrased as "small tweak" that meets `R1`+ criteria
MUST NOT be run as `TINY`. A request phrased as "hotfix" without production
impact MUST NOT be run as `HOTFIX`.

**VCPS-WF-003. (Re-routing)** If during a run the work no longer fits its
intent (e.g. `TINY` touches an enforcement path, `BUG` reveals missing
intended behavior, `AUDIT` would require changes), the executor MUST stop the
current run, record the reason, and continue under the correct intent.
Evidence already gathered MAY be carried over if not stale.

## 3. Workflow contract

Each workflow document defines:

1. **Purpose** and trigger.
2. **Entry conditions.**
3. **Steps**, each mapped to gates.
4. **Gate mapping** (which gates, which depth).
5. **Outputs** (artifacts produced or updated).
6. **Escalation / re-routing** conditions.
7. **Exit** conditions and the lifecycle state reachable.

**VCPS-WF-010.** Every workflow run MUST:

- record its intent and project/component level used; change workflows MUST
  record their change class, and `RELEASE` MUST record the highest class in
  its release unit. `SETUP` and read-only `AUDIT` MUST record their scope
  rather than invent a change class;
- record outcomes for gates it actually evaluates per
  [../standard/gates/README.md](../standard/gates/README.md); `SETUP` and
  read-only `AUDIT` MUST record the gate states they inspect without
  inventing new gate outcomes;
- record findings per [../standard/classifications.md](../standard/classifications.md);
- end with a handoff record per VCPS-PORTABILITY-006;
- report its final status using VCPS terms (gate outcomes, lifecycle states,
  finding classifications) rather than informal language such as "done" or
  "all good".

## 4. Gate mapping summary

*Informative summary.* Each workflow document is authoritative for its own
mapping; the applicability matrix in
[../standard/gates/README.md §4](../standard/gates/README.md#4-applicability-matrix)
is authoritative for which gates are required by change class.

| Intent | G1 | G2 | G3 | G4 | G5 | G6 |
|--------|----|----|----|----|----|----|
| `FEATURE` | matrix | matrix | matrix | matrix | matrix | via `RELEASE` |
| `REVIEW` | reconstruct (G1-003) | inspect | for remediation | matrix | matrix | via `RELEASE` |
| `BUG` | confirm intent | if fix changes design | matrix | matrix + regression | matrix | via `RELEASE` |
| `TINY` | N/A | N/A | light | light | N/A | via `RELEASE` |
| `HOTFIX` | minimal | deferrable (`HC-16`) | matrix | reduced, deferrable (`HC-16`) | matrix for touched categories | expedited |
| `AUDIT` | reconstruct | inspect | inspect | evidence collection only | inspect | readiness review |
| `RELEASE` | — | — | — | — | — | full |
| `SETUP` | — | — | baseline checks | baseline | baseline audit | — |

# Evidence Model

This document owns: evidence records, tiers (`E0`–`E5`), results, fidelity,
and staleness.

## 1. Principle

**VCPS-EVD-001.** Every gate outcome, lifecycle state transition, finding
classification, or conformance claim MUST be backed by a recorded evidence
reference at or above the tier its rule requires. A claim without a
recorded reference is `E0 CLAIMED` and MUST NOT by itself support a `PASS`.

**VCPS-EVD-002. (No upward inference)** A stronger claim MUST NOT be
inferred from a weaker tier of evidence, from a related but different
assertion, or from the absence of a contrary finding. Silence is not
evidence.

**VCPS-EVD-003.** An agent's own unverified statement that a check passed,
a property holds, or a task is complete MUST NOT itself be counted as
executable evidence — it is `E0 CLAIMED` regardless of how confidently it
is phrased. Only a recorded method, environment, and result (§4)
constitute evidence above `E0`.

## 2. Evidence tiers

| Tier | Name | Meaning |
|------|------|---------|
| `E0` | `CLAIMED` | An assertion stated without supporting evidence. Cannot support a gate `PASS`. |
| `E1` | `STATIC` | Static inspection: reading code/config/CI definitions, a parse-only check, documentation review. No execution. |
| `E2` | `LOCAL` | Local execution: the check actually ran, on a developer/agent machine or equivalent, with a captured result. |
| `E3` | `CI` | A retrievable hosted CI run on the exact evaluated revision, with a durable run locator. |
| `E4` | `EXTERNAL` | An external actor or action: a real (non-mocked) third-party provider, or a human decision/acceptance recorded as evidence. |
| `E5` | `PRODUCTION` | A production observation: the asserted behavior was actually observed in the live production environment. |

## 3. Results

**VCPS-EVD-010.** Every evidence record MUST carry exactly one result:
`PASS`, `FAIL`, `NOT_RUN`, `ERROR`, or `INCONCLUSIVE`.

- `PASS` — the check ran and the assertion held.
- `FAIL` — the check ran and the assertion did not hold.
- `NOT_RUN` — the check was not executed (missing tool, credential,
  environment, network, registry, or withheld because its effects could
  not be safely bounded).
- `ERROR` — the check attempted to run but could not complete (crash,
  timeout, infrastructure failure) without reaching a PASS/FAIL
  determination.
- `INCONCLUSIVE` — the check ran but its result does not reliably
  determine the assertion (e.g. a flaky reproduction, an ambiguous
  observation).

**VCPS-EVD-020.** `NOT_RUN`, `ERROR`, and `INCONCLUSIVE` MUST NOT be
reported, summarized, or counted as `PASS`. A summary over multiple checks
MUST report the worst result present, not an average or a majority.

**VCPS-EVD-021.** A substitute execution environment (mock, emulator,
in-memory/embedded engine, sandbox, test double) MAY produce evidence
scoped to that substitute, but MUST NOT be labeled as evidence for the
real target unless the substitute is the explicitly documented compatible
equivalent (see §5). In particular — informative, non-exhaustive — a
YAML/config parse-only check is not evidence of a hosted CI run; an
embedded/in-memory database (e.g. PGlite) is not evidence of the
production database engine's concurrency or locking behavior; a mocked
provider is not evidence of real-provider acceptance; a process exit code
or HTTP status alone is not evidence of business-level success; and local
execution is not evidence of a production observation. (See
`workflows/setup.md` `VCPS-SETUP-059` for the same rule applied at Stage 6.)

**VCPS-EVD-022.** A process exit code or HTTP status alone MUST NOT be
treated as proof of business success. Evidence MUST check the business
assertion itself (the state, value, or side effect the assertion is
actually about), not only that a call returned without erroring.

## 4. Evidence record

**VCPS-EVD-030.** An evidence record MUST contain:

| Field | Meaning |
|---|---|
| `id` | Stable identifier (`EVD-<uuid>`). |
| `tier` | `E0`–`E5`. |
| `result` | Per §3. |
| `assertion` | The precise, falsifiable statement being evaluated (see `glossary.md`). |
| `method` | Command, test identifier, procedure, or inspection method. Executable evidence MUST include a reproduction command or procedure. |
| `environment` | Where it ran: local/CI/sandbox/production, runtime/engine versions where relevant to fidelity. |
| `revision` | The exact evaluated content (see §6). |
| `scope` | Files/components/paths the assertion is actually about. |
| `producer` / `verifier` | Role and identity, at the granularity available (see §4.1). |
| `timestamp` | When the evidence was produced. |
| `artifacts` | Durable locators for logs/output. For external locators (hosted run pages, dashboards, tickets) MUST include enough information to retrieve them later and SHOULD store a durable excerpt/hash in the repository per `portability.md` `VCPS-PORTABILITY-004`. |
| `substitutions` | Any substitute environment used, and what it does/doesn't prove (§5). |
| `limitations` | Known gaps in what this evidence actually demonstrates. |
| `related` | Other evidence/finding/gate records this bears on. |
| `corrections` | Links to any correcting record (§7). |

**VCPS-EVD-031.** At `L2` and above, `E3`+ evidence citing an external
system (a hosted CI run, a provider dashboard) MUST include a retrievable
run locator and enough repository-local summary (`VCPS-EVD-030`
`artifacts`) that the evidence remains interpretable even if the external
locator later becomes unreachable (`portability.md VCPS-PORTABILITY-004`).

### 4.1 Producer and verifier identity

**VCPS-EVD-032.** Producer and verifier identity MUST be recorded at the
granularity available. VCPS MUST NOT require any specific vendor, model, or
agent identity format — a role (human/agent) plus whatever stable identity
the environment provides is sufficient. What matters is that producer and
verifier identity is distinguishable where independence (`independence.md`)
requires it, not the specific identity scheme used.

## 5. Scope and fidelity

**VCPS-EVD-040.** Fidelity is how faithfully the environment used for
evidence represents the environment the assertion is actually about. Where
the evaluated environment differs from the one the assertion is about, the
producer MUST list the difference in `limitations`.

**VCPS-EVD-041.** Evidence produced on a substitute MUST NOT support
assertions about the real target at a tier or fidelity the substitute
cannot actually provide (see `VCPS-LVL-020`/`021` for the `L3` fidelity
floor on database and external-provider assertions).

**VCPS-EVD-011.** The `E1`/`E2` boundary is load-bearing, not cosmetic:
static inspection (reading code, config, or a CI file) MUST NOT be
reported, summarized, or relied upon as if it were executed verification.
The table below is normative, not merely illustrative.

| Evidence | MUST NOT be used to prove |
|---|---|
| Config/CI YAML parse (`E1`) | A hosted CI run actually executed (`E3`) |
| Embedded/in-memory/emulated database engine | Concurrency, transaction isolation, locking, or migration behavior of the production database engine family |
| Mocked external provider | Real external-provider acceptance (`E4`) |
| Process exit code / HTTP status alone | Business-level success of the asserted behavior |
| Local execution (`E2`) | A production observation (`E5`) |
| Static inspection (`E1`) | Executed verification (`E2`+) |

## 6. Revision binding and staleness

**VCPS-EVD-050.** Evidence is bound to the exact revision it evaluated. A
later revision requires fresh or explicitly carried-forward evidence before
it may rely on a prior result.

**VCPS-EVD-051.** Stale evidence MUST NOT support a gate `PASS` or lifecycle
transition for a later revision, except that `E1`/`E2` evidence MAY be
carried forward unchanged when the producer can show nothing in the
evidence's scope changed between revisions; the record MUST state the
original and current revision and the basis for treating them as
equivalent for the assertion. That carry-forward is itself `E1` evidence and
MUST NOT be used to satisfy a requirement for `E2` or stronger.

**VCPS-EVD-052. (Dirty-worktree revision)** An uncommitted (dirty) worktree
is a valid evidence revision only if it is reconstructable: the evidence
record MUST identify the exact evaluated content, including relevant
untracked files, by content hash or an equivalent manifest, not merely a
timestamp. A bare timestamp alone MUST NOT identify a dirty worktree
revision. Before evidence produced on a dirty worktree revision is treated
as supporting a later committed revision, the producer MUST establish that
its scope is unchanged between the two, per `VCPS-EVD-051`.

**VCPS-EVD-053.** Recompute staleness from revision, scope, and dependency
changes at the time evidence is relied upon; do not trust a previously
stored freshness label without re-checking it against the current revision.

## 7. Corrections

**VCPS-EVD-060.** An evidence record MUST NOT be edited to change what was
actually observed (`AG-011`). A correction creates a new evidence record
linked by `supersedes_ref`; the prior record and its original result remain
intact and visible.

## 8. Negative and absence assertions

**VCPS-EVD-070.** An assertion that something does *not* happen (e.g. "a
tenant cannot read another tenant's rows") MUST be shown positively: a
recorded attempt that was blocked, not merely the absence of a recorded
failure. The absence of a test is not evidence the property holds.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption (the git object store's loose
objects were found empty, and the working-tree file was 0 bytes). Section
3's modal text (`VCPS-EVD-001/002/020/022/030/032/041/051/052`, the field
table under `VCPS-EVD-030`, and the closing sentence of §8) is recovered
verbatim from `standard/core-audit-0.1.md`'s per-line requirement
inventory, which quoted these exact lines before the file was lost. The
`E0`–`E5` tier names are cross-referenced verbatim from `glossary.md` and
`levels.md` (both intact) and from inline tier usage in
`workflows/setup.md` and `templates/validation.md` (both intact). The
substitution-prohibition table in §5 and the `NOT_RUN`/`ERROR`/
`INCONCLUSIVE` result definitions in §3 are reconstructed from the
identical, already-normative phrasing in `workflows/setup.md`
`VCPS-SETUP-059` and `templates/validation.md` item 6 (both intact,
quoted near-verbatim here rather than paraphrased) rather than recovered
from the lost file directly. Requirement numbers not listed above
(`VCPS-EVD-012`..`019`/`021`/`042`-`049`/`054`-`059`/`061`-`069`, if any
existed) are not recoverable and are not asserted here; this
reconstruction only restates what could be grounded in surviving text.

**2026-10-05, ratification pass.** `VCPS-EVD-003`, `VCPS-EVD-011`, and
`VCPS-EVD-031` were added during the dedicated recovery-ratification
audit's requirement-graph check, which found these three IDs cited by
`standard/core-audit-0.1.md`'s own text (untouched, in its "Agent
statement called executable evidence," "Static inspection called
executed verification," and portability-handoff rows) but never defined
anywhere in the surviving or previously-reconstructed material — dangling
references, not merely absent numbers. Their content here is built from
that citing context (e.g. `VCPS-EVD-031` from "Retrievable run locator
and repository summary at L2+") rather than recovered original wording,
and is flagged accordingly. This closes those three dangling references;
it does not claim to recover their original text. It SHOULD be reviewed
against the original if a backup ever surfaces.

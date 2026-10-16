# Workflow: SETUP

## Purpose

Install, adopt, upgrade, or repair a VCPS installation in a repository. This
is the agent-independent setup **state machine**. Agent adapters (e.g. a
Claude Code `/vcps-setup` or a Codex setup skill) execute this state machine;
they MUST NOT define their own divergent sequence.

## Entry conditions

Any repository, regardless of VCPS status.

## 1. Modes

**VCPS-SETUP-001.** On entry, the executor MUST determine mode by inspecting
the repository (not by asking the user first):

| Mode | Condition |
|------|-----------|
| `NEW` | No canonical `.vcps/` root, VCPS config, or VCPS-like governance artifacts exist, and no application code, tests, or CI need reconciliation. |
| `ADOPT` | No canonical `.vcps/` root exists, but application code, tests, CI, or noncanonical governance artifacts need reconciliation. |
| `UPGRADE` | A structurally valid installation exists with an older supported VCPS or project schema version and no internal inconsistency. |
| `REPAIR` | A canonical `.vcps/` root or config exists but is inconsistent: missing/malformed config, missing referenced artifacts already due at its recorded stage (excluding explicitly pending artifacts), malformed records, unsupported version, or contradictory risk/level data. |

**VCPS-SETUP-002.** `REPAIR` takes precedence over `UPGRADE` when both
conditions hold. An `AHEAD` VCPS or project schema version MUST route to
read-only `REPAIR` diagnosis and MUST NOT be auto-downgraded (VCPS-VER-011).

**VCPS-SETUP-003. (Resume)** A valid, internally consistent config that
records `SETUP_STATUS` `PARTIAL` or `BLOCKED` from a prior run MUST be
resumed directly from its recorded stage/checkpoint, without re-entering
mode selection, provided its `vcps_version` is not `BEHIND` or `AHEAD`
(those cases route to `UPGRADE`/`REPAIR` as usual). A consistent-but-incomplete
prior run is a distinct case from `REPAIR` (which addresses inconsistency)
and from `NEW`/`ADOPT` (which addresses absence of a config) — it is neither.

**VCPS-SETUP-004. (Already complete)** A valid, internally consistent config
at the executing version with `SETUP_STATUS` `COMPLETE` MUST route to a
consistency check equivalent to Stage 11 and report the existing status.
Setup MUST NOT create a fresh baseline or overwrite existing records merely
because it was invoked again.

## 2. Stages

Stages are sequential but a later stage MAY reveal the need to revisit an
earlier one (recorded, not silently looped).

### Stage 1 — Repository discovery

**VCPS-SETUP-010.** Identify: repository boundaries, components/services,
languages, entry points, existing documentation of intent, existing tests,
existing CI, deployment targets, and whether a production environment exists.
Evidence: `E1`.

### Stage 2 — Stack / toolchain discovery

**VCPS-SETUP-011.** Identify build, test, lint, type-check, security-scan, and
format commands actually used (not assumed) per component. Record exact
commands and their current exit behavior. Evidence: `E1`/`E2`.

**VCPS-SETUP-012.** Where no CI exists, record this as an `EVIDENCE_GAP` with
level implications (VCPS-LVL-010); do not block `NEW`/`ADOPT` solely on its
absence.

### Stage 3 — Risk classification

**VCPS-SETUP-013.** Apply [../standard/risk-model.md](../standard/risk-model.md)
to determine project/component level(s) and impact-path evidence. Apply
[../standard/levels.md](../standard/levels.md) to derive minimums.

**VCPS-SETUP-014.** Draft the critical invariant registry for `L2`/`L3`
components (VCPS-RISK-030). Exhaustive invariant discovery is NOT required in
this stage; coverage SHOULD improve over subsequent `REVIEW`/`AUDIT` runs.

### Stage 4 — VCPS scaffold

**VCPS-SETUP-015.** Create the VCPS artifact root and config
([../standard/artifacts.md](../standard/artifacts.md)), recording
`vcps_version` = the executing specification version, artifact schema/layout
versions, discovered toolchain commands, levels/profile from Stage 3, current
stage/status, and any canonical artifacts planned but not yet created.

### Stage 5 — Dirty-tree / legacy classification

**VCPS-SETUP-016.** Classify repository content older than this setup run:

| Finding | Handling |
|---------|----------|
| Uncommitted changes of unknown origin | `HC-07`; MUST NOT be discarded or committed without owner decision. |
| Unexplained files (no clear purpose, not referenced, not obviously generated) | `HC-07`. |
| Disabled/skipped tests, `|| true`, suppressed lint | Record as legacy `EVIDENCE_GAP` or `DEFECT` (§9), not fixed silently in this stage. |
| Dead/orphaned code paths | Record as `EVIDENCE_GAP` (classification uncertain) for later `REVIEW`. |
| Uncommitted or pending migration scripts (especially destructive ones) | `HC-02`; MUST NOT be applied or discarded during setup. |

**VCPS-SETUP-017.** This stage MUST NOT delete, rewrite history of, or force-
push over any content. Those require `HC-04` regardless of mode.

### Stage 6 — Baseline verification

**VCPS-SETUP-018.** Attempt every discovered applicable check from Stage 2
that can be run safely on the current revision, without modifying code to
make it pass. Record `NOT_RUN` for every withheld or unavailable check. Record every result
(`PASS`/`FAIL`/`NOT_RUN`/`ERROR`/`INCONCLUSIVE`) — this is the baseline.

**VCPS-SETUP-019.** The baseline MUST NOT be used to justify weakening checks;
it exists only to distinguish pre-existing failures from newly introduced
ones in later workflows (VCPS-G3-009's "baseline" comparison).

### Stage 7 — Locally actionable remediation

**VCPS-SETUP-020.** The executor MAY fix trivial, unambiguous, local
tooling issues that block running checks at all (e.g. a missing dev
dependency, an invalid config file preventing the linter from starting),
provided the fix is `R0` and recorded. It MUST NOT fix substantive baseline
`FAIL`s in this stage — those are legacy findings (§9), not setup work. After
any such fix, affected checks MUST be rerun and the pre-fix and post-fix
results recorded; Stage 8 uses the post-fix revision for the baseline.

### Stage 8 — Baseline establishment

**VCPS-SETUP-021.** Persist the baseline (§Stage 6) as a VCPS artifact bound
to the exact setup revision, including a reconstructable dirty-worktree
snapshot where applicable (VCPS-EVD-052). This is the reference used by
`VCPS-G3-009` and `VCPS-G4-002` comparisons going forward.

#### Baseline Update Procedure

**VCPS-SETUP-027.** The original baseline observations MUST remain immutable.
After establishment, baseline history MAY only be extended by:

1. **widening** it when broader coverage finds additional genuinely
   pre-existing failures, with evidence from the original setup revision or
   an earlier reconstructable revision that they pre-date the mutation; or
2. **appending a resolution entry** when a `RESOLVED` finding with
   remediation evidence shows that exact failure was fixed. A derived view
   MAY omit resolved failures, but MUST preserve the original observation and
   its resolution link.

**VCPS-SETUP-028.** Any other change to the baseline — in particular,
altering it to make a newly-introduced failure read as pre-existing — is
verification weakening (`AG-017`) and MUST go through the `AG` exception
protocol ([../standard/anti-gaming.md §2](../standard/anti-gaming.md#2-exception-protocol)).

### Stage 9 — Legacy evidence-gap registry

**VCPS-SETUP-022.** Every Stage 5/6 finding not remediated in Stage 7 MUST be
recorded in the legacy registry with classification per
[../standard/classifications.md](../standard/classifications.md), severity,
and a touch rule. Legacy registry findings MUST be created in status `OPEN`.
A legacy finding MUST NOT be created, or default to, status `RISK_ACCEPTED`
— that status requires `HC-08` per `VCPS-CLS-030`, applied explicitly, never
assumed at the point of discovery. "Pre-VCPS legacy" is not equivalent to
"accepted" or "safe" until a human says so.

**VCPS-SETUP-023. (Ratchet rule)** A legacy finding MUST NOT block unrelated
work. It MUST be escalated to the current workflow's gates when: the current
change touches the same file/enforcement path; the finding's severity is
`CRITICAL` and the project is `L2`+; or the finding's severity is `HIGH` or
`CRITICAL` and the project is `L3` (escalates regardless of touch, via
`HC-08` to accept or schedule remediation).

**VCPS-SETUP-024.** The legacy registry MUST NOT be used to convert
unexamined legacy `EVIDENCE_GAP`s into `DEFECT`s (`AG-008` applies).

### Stage 10 — CI quality-gate alignment

**VCPS-SETUP-025.** Where CI exists, record the mapping between VCPS gates and
CI jobs/checks (which CI job provides which `E3` evidence). Where CI does not
exist, record this as an `EVIDENCE_GAP` affecting all `E3` requirements and
note the level consequence (VCPS-LVL-010). Creating new CI pipelines is an
adapter/implementation concern, not performed by this Core-level stage.

### Stage 11 — VCPS system audit

**VCPS-SETUP-026.** Run an internal consistency check equivalent to
[audit.md](audit.md) scoped to the VCPS installation itself: config
consistency, artifact cross-references resolve, no orphaned findings,
version recorded correctly. Produce `SETUP_STATUS`.

## 3. Mode-specific notes

**VCPS-SETUP-030. (`UPGRADE`)** Apply VCPS-VER-012: surface every artifact
whose meaning changed under the new version for human review before
continuing to Stage 3 onward with new assumptions. A project-schema-only
upgrade follows the explicit migration in the artifact contract and keeps
the same protection for meanings and history.

**VCPS-SETUP-031. (`REPAIR`)** Diagnose the specific inconsistency first;
Stages 1–2 MAY be skipped if prior results are still valid (not stale per
VCPS-EVD-050); Stage 4 is a correction, not a fresh scaffold, and MUST
preserve existing record IDs and history. If the inconsistency is an
`AHEAD` or unsupported older version, stop immediately after confirming it;
do not proceed to Stage 2 onward until a compatible specification/migration
governs.

## 4. Human checkpoints requiring a stop

`HC-01`, `HC-02`, `HC-03`, `HC-04`, `HC-07` (routine in Stage 5), `HC-08`
(accepting serious legacy findings into risk-accepted status), `HC-05` if
remediation would otherwise touch security posture, `HC-09` if discovered
risk profile is lower than an existing (pre-VCPS) assumption.

## 5. Outputs

Config, risk profile, invariant registry (draft), baseline, legacy registry,
CI-gate mapping (or its gap), setup status record, handoff record.

## 6. Exit / status

| `SETUP_STATUS` | Meaning |
|----------------|---------|
| `COMPLETE` | All 11 stages concluded with no pending checkpoint or unresolved setup evidence gap. This describes installation completeness, not product safety or production readiness. |
| `PARTIAL` | Scaffold exists; the baseline may still be pending before Stage 8, or later stages have recorded gaps (e.g. no CI or no executable tests for an existing production application). Project MAY use other workflows only where their dependent stages are complete, with `PARTIAL` conformance (VCPS-CORE-032/VCPS-SETUP-040). |
| `BLOCKED` | A stage cannot proceed without a pending human decision. |

**VCPS-SETUP-040.** Other workflows MAY run with `SETUP_STATUS` `PARTIAL` but
MUST NOT run with it `BLOCKED` on a stage their gates depend on.

**VCPS-SETUP-041.** `SETUP_STATUS` MUST NOT be `COMPLETE` while any `L2`+
project has an undispositioned `CRITICAL` legacy finding, or any `L3`
project has an undispositioned `CRITICAL` or `HIGH` legacy finding
("undispositioned" = not `RESOLVED` and not explicitly `RISK_ACCEPTED` via
`HC-08`). Such a project's setup stops at `PARTIAL` (or `BLOCKED` pending
`HC-08`) — an honest status under `VCPS-CORE-032`, not a blocker to using
other workflows per `VCPS-SETUP-040`.

**VCPS-SETUP-042.** An existing production application with no executable
tests MUST record a verification `EVIDENCE_GAP` with owner and cannot have
`SETUP_STATUS` `COMPLETE`. Baseline entries with `FAIL`, `NOT_RUN`, `ERROR`, or
`INCONCLUSIVE` MUST retain those results; baseline establishment MUST NOT imply that their
underlying behavior is accepted, safe, or verified. Every such result MUST
have a linked finding with severity and touch rule.

## 7. Deterministic Setup Engine contract

This section specifies execution of the eleven stages above. It does not
change the owners of evidence, risk, findings, approval, or artifact meaning.
The Setup Engine version is the executing VCPS specification version in
`VERSION`. A project configuration written by this engine uses project schema
`0.2.0` and layout version `0.1.0`
([artifact contract](../templates/contract.md)).

### Entry, mode, and dry-run

**VCPS-SETUP-050.** Inspect the repository boundary, canonical `.vcps/`
root, config existence and parseability, supported versions, and existing
project/governance content in that order. Apply `VCPS-SETUP-001`/`002`:
inconsistent canonical installation (including missing config) → `REPAIR`;
consistent older supported installation → `UPGRADE`; consistent equal
installation → `VCPS-SETUP-003`/`004`; no canonical installation with existing
content → `ADOPT`; otherwise → `NEW`. A separate, noncanonical governance
system remains `ADOPT` and is never overwritten as if VCPS owned it.
Unsupported older schema and newer schema/specification receive read-only
`REPAIR` diagnosis with external `BLOCKED` result until a compatible
migration/executor is available. An unparsable config is never guessed from
file names.

The supported write target is VCPS `1.0.0` with project schema `0.2.0` and
layout `0.1.0`. Projects recording the legacy `0.1.0-draft` Core version
may update that version label in place because the `1.0.0` release changes
no requirement content. The only defined project-schema migration source
is the same VCPS/layout version with project schema `0.1.0`
([migration rule](../templates/contract.md#unknown-fields-and-migrations)).
Other older or unknown specification versions are diagnosed read-only until
an explicit version migration is published. Executors extend this support
matrix by versioned specification, not by adapter guesswork.

**VCPS-SETUP-051.** Before any repository mutation, provide a read-only
dry-run with proposed mode, level and uncertainty, paths to create/modify,
check commands and `NOT_RUN` reasons, likely checkpoints, and a mutation
budget. The dry-run MUST NOT execute checks with side effects, install
dependencies, access production, or change files. It is mandatory again
when mode, risk, revision, check set, or planned mutation scope changes.
If an adapter cannot preview these facts, it stops before writes with
`PARTIAL` or `BLOCKED` as appropriate.

**VCPS-SETUP-052.** At Stage 4, persist the dry-run as
`project.yaml.installation.plan`. `sha256` is SHA-256 of UTF-8 canonical JSON
of the plan object excluding `sha256` (sorted keys, no whitespace, UTF-8
characters unescaped); this is
an integrity binding, not a signature. The plan records the base revision,
mode, level, create/modify paths, intended checks, likely checkpoints, and
allowed paths/operations plus maximum changed files, bytes, and commands.
No deletion, move, history rewrite, or production operation is in a routine
setup budget. Before each mutation, compare the intended path, operation,
count, and byte estimate to the plan and current repository state. Expansion
requires a new read-only plan and applicable checkpoint; it is never silently
absorbed. Unexpected writes found afterward stop the stage for diagnosis.
Before replacement, append the prior complete plan to
`installation.plan_history`. A plan hash in an old stage event resolves to
exactly one archived or active plan.

### Persistent progress and resume

**VCPS-SETUP-053.** `project.yaml.installation.stage_events` is the
append-only stage journal. Each event records stage, event state, time,
input revision and scoped path fingerprint, output revision, plan hash,
evidence/finding/approval references, pending checkpoints, mutation paths,
and reason. The fingerprint is SHA-256 over sorted repository-relative paths
in `input_scope` and their content hashes/status including absence; it
includes relevant config, lockfiles, VCS state, and prior stage outputs.
The input fingerprint excludes that stage's output paths and the
`installation.plan`, `plan_history`, `stage_events`, `history`, `stage`,
and `status` fields of `.vcps/project.yaml`; a directory-scoped input
excludes `.vcps/` unless explicitly listed. Other externally edited
configuration fields remain in scope. The fingerprint algorithm and exclusions
are fixed in [validation.md](../templates/validation.md#setup-state-validation).
Stages 1–3 are read-only discovery. If interrupted before Stage 4 persists
the plan and events, rerun those read-only stages; they were not durably
completed. Stage 4 records their results and events before any later stage
may rely on them. No private conversation state counts as progress.

**VCPS-SETUP-054.** On resume, validate the config, journal, referenced
records, plan hash, current revision, and each completed event's input
fingerprint. Scan planned output paths for missing, truncated, malformed,
or unreferenced records left by interrupted writes; quarantine nothing
automatically, and resume or repair under the mode rules. Walk from Stage 1
forward; the first missing, stale, or
invalidated stage and every dependent stage must be re-evaluated, with
`INVALIDATED` events appended. Keep old evidence/findings and mark stale
evidence by Core `VCPS-EVD-050`, never delete it. A changed check command or
dependency invalidates baseline verification onward; changed impact paths
invalidate risk classification onward; changed governance artifacts
invalidate scaffold/validation onward. Unrelated files only invalidate a
stage if in its recorded input scope, but a new unexplained dirty file
always reopens Stage 5. A stage recorded `BLOCKED` may resume only after an
exact-scope approval or changed condition is observed. Approval reuse follows
`VCPS-HC-004`, including revision binding; silence is not a decision.

**VCPS-SETUP-055.** `installation.stage` identifies the earliest stage
requiring work, not the highest stage ever visited; it is `null` only after
all eleven stages are complete. `history` records
status/stage transitions; `stage_events` records attempts and invalidations.
A stage is completed only after its required outputs are persisted,
structurally validated, and referenced by a `COMPLETED` event. `PARTIAL`
events record truthful usable progress; `BLOCKED` events record a dependency
on human decision or unsupported format. A retry appends a new attempt
and preserves earlier failures and evidence. The next adapter starts from
the journal, not a handoff summary. Multi-file writes are not assumed
atomic: write and validate each record first, then append the stage event
as the commit marker. On crash, unreferenced or partially written records
are diagnosed under REPAIR/resume; they never imply completed work.

### Discovery, risk, and legacy state

**VCPS-SETUP-056.** Discovery inventories VCS boundary, branch/revision,
tracked, staged, unstaged, deleted, untracked and submodule state; repository
size and component boundaries; manifests, lockfiles, package managers,
runtimes, frameworks, build/test/lint/typecheck/coverage commands; database
and migration systems; browser/E2E, CI and deployment definitions; authn,
authz, tenancy, money/inventory/business-critical flows, providers, AI
actions, infrastructure-as-code, mobile/native components. A fact is
`OBSERVED` only with a cited direct inspection or execution record, `INFERRED`
only with its supporting clue and uncertainty, otherwise `UNKNOWN`.
Inferences do not become configured commands, critical-path absence, or
verification `PASS`. Repository size is a planning signal, never a level.
Record a credential-free inventory in evidence and project/risk artifacts,
not secrets or machine-specific paths.

**VCPS-SETUP-057.** Rate D1–D9 for each component by tracing actual
failure impact and enforcement paths, then derive levels exactly by
`VCPS-RISK-010`/`020`/`021`. Record observed path evidence, candidate
ratings, unresolved uncertainty, final rating, and rationale in
`risk-model.md`; `project.yaml` owns the selected level. When a candidate
rating lacks adequate evidence, use Core's higher candidate until resolved.
The project level covers shared paths at the highest affected component
level. A prior established level cannot fall without `HC-09` and a recorded
impact-path explanation. A tiny critical flow can be L3; a large static
codebase can be L1. Change classes are still impact-based, so harmless text
in an L3 repository can be R0 if no enforcement path is touched.

**VCPS-SETUP-058.** Classify each pre-existing change by both VCS state
(staged, modified tracked, untracked, deleted, submodule pointer/worktree)
and content category (application, tests, database/migration,
VCPS/governance, documentation, deployment/configuration, assets, generated,
unknown). Do not infer authorship from modification time. Hash or describe
binary files without dumping contents. Generated status needs a generator
or ignore-rule basis; otherwise it is unknown. Record every unexplained
item and ownership uncertainty for `HC-07`. Uncommitted migrations require
`HC-02` before application/discard; mere inspection is allowed. Do not
modify, delete, stage, or commit an unknown item. A large dirty tree can
still be adopted if its exact state and unresolved ownership are recorded.

### Verification, remediation, baseline, and CI

**VCPS-SETUP-059.** Stage 6 builds a component/check matrix from
project-native commands. Inspect applicability of dependency setup,
diff/format hygiene, lint, typecheck, unit, integration, coverage, build,
migration consistency, browser discovery/execution, real database, and
security/dependency checks. Do not invent a substitute command. For each
applicable check record command, environment, revision, scope, result,
tier, output locator, and limitations. Preflight each command for expected
repository writes and external effects. Run it in an isolated environment
or within the declared budget; if its effects cannot be bounded safely,
record `NOT_RUN` and the reason. Dependency installation must not silently
alter manifests or lockfiles. A check blocked by missing tools,
registry, credentials, network, or environment is `NOT_RUN`/`ERROR` or
`INCONCLUSIVE` according to [evidence-model.md](../standard/evidence-model.md),
never `PASS`. A parse-only CI inspection is E1, local execution E2,
retrievable hosted run E3; mocks, PGlite, or HTTP status alone do not prove
production-provider, PostgreSQL-concurrency, or business success claims.
Checks with side effects need their applicable `HC-11`/`HC-03` decision
before execution; otherwise record `NOT_RUN`.

**VCPS-SETUP-060.** Stage 7 is limited to `VCPS-SETUP-020`: R0,
demonstrated local tooling/fixture/config or deterministic formatting repair
within the current mutation budget. A clearly demonstrated product defect
or behavior-changing fixture fix is routed to BUG/REVIEW with its gates, not
silently repaired as setup. Never weaken tests, assertions, coverage,
lint, security, acceptance criteria, or CI to improve the baseline.
Capture before and after evidence and rerun every affected check. If a
supposed R0 repair changes behavior or grows scope, stop and replan under
`HC-13` and the normal workflow.

**VCPS-SETUP-061.** Establish a baseline only if the exact repository state
is reconstructable per `VCPS-EVD-052`, Stage 5 has a truthful inventory,
every discovered applicable check has a recorded result (including blocked
or not run), each non-PASS result has a finding with severity and touch rule,
and the baseline artifact can be safely persisted and validated. Inherited
finding records needed by the baseline are created in this stage; Stage 9
audits and completes the legacy registry without changing the original
baseline observations. In a repository without VCS, a content-addressed
repository snapshot/manifest is required instead of a commit reference.
The snapshot identifies the evaluated application/configuration content and
relevant untracked files; it excludes the baseline artifact and subsequent
VCPS records so writing the observation does not change its own subject.
failures and gaps may remain OPEN; this is `ALLOW_WITH_FINDINGS`, never
acceptance. `ALLOW` means the same prerequisites without inherited
non-PASS results. `BLOCK` applies when revision/snapshot is unknowable,
material dirty ownership prevents truthful scope, evidence would require
storing exposed secrets or personal data, or a prerequisite record cannot
be safely represented. A reproduced critical security/tenant failure may
be captured as an OPEN baseline finding but prevents `COMPLETE` under
`VCPS-SETUP-041` and requires `HC-08` for acceptance. A destructive
migration is not executed to establish a baseline; record the blocked
check and checkpoint. The baseline claims historical observation only,
not safety, production readiness, or approval. Its original observations
remain immutable under `VCPS-SETUP-027`.

**VCPS-SETUP-062.** Stage 9 materializes unresolved legacy state as
`DEFECT` only for reproduced incorrect behavior, `EVIDENCE_GAP` for missing
or weak proof, `EXTERNAL_ACCEPTANCE` for absent external decision/observation,
and `KNOWN_LIMITATION` only with the classification's approval rules.
Each finding records severity, blocking scope, touch rule, evidence, and
OPEN status initially. A missing test is not a demonstrated DEFECT.
Neither a baseline nor an approval automatically closes a finding.

**VCPS-SETUP-063.** Stage 10 first inventories existing CI systems,
config paths, jobs, commands, triggers, and reported results. Map each
required check to one canonical CI responsibility where possible; do not
duplicate expensive jobs or weaken existing ones. Proposed changes use
project-native commands and the mutation budget. A config file or local
YAML parse alone cannot claim hosted E3. If no CI, no accessible run, or
a job is ambiguous, record an `EVIDENCE_GAP` and report `PARTIAL` where
the level needs E3. CI provider names are descriptive, not normative.

**VCPS-SETUP-069.** In `ADOPT` with another governance system, inventory
its files, stated owners, commands, risk categories, and approvals as
legacy input. Create a source-to-VCPS crosswalk in evidence or handoff
narrative, citing exact source paths. Import only verified facts with
provenance; preserve original artifacts. An old approval or accepted risk
cannot become a VCPS checkpoint decision by translation. A conflicting
command, owner, criterion, or risk level is an explicit uncertainty and
triggers `HC-07` before modifying that area. VCPS canonical files are
separate; no adapter may rewrite the other system to make reconciliation
appear complete.

### Stage execution contracts

**VCPS-SETUP-064.** Every stage uses the common procedure: validate inputs,
inspect read-only first, check budget/checkpoints before mutation, emit
evidence, validate outputs, append event, then advance. `COMPLETED` means
its exit condition below holds; `PARTIAL` means a usable output has an
explicit gap; `BLOCKED` means a prerequisite decision or safe operation
is unavailable. Retrying rechecks fingerprints and appends an event.
Resuming never erases the prior attempt.

| Stage | Inputs and discovery | Allowed mutation and evidence | Prohibited mutation, checkpoint, exit |
|---|---|---|---|
| 1 Repository discovery | Repository path, VCS and content; inspect boundary, topology, dirty summary, deployment. | None before Stage 4; E1 inventory persisted there. | No checkout/reset/network side effect. Exit: boundary or UNKNOWN recorded. |
| 2 Stack/toolchain discovery | Stage 1; inspect manifests, lockfiles, native commands, CI. | None before Stage 4; E1 command catalog. | No install/build yet; missing tools recorded. Exit: known commands and unknowns enumerated. |
| 3 Risk classification | Stages 1–2; trace D1–D9 impact and invariants. | None before Stage 4; risk rationale/config draft. | No downgrade without HC-09. Exit: conservative level and uncertainty recorded. |
| 4 Scaffold/artifact preparation | Dry-run, version/mode, artifact contract. | Create/repair only budgeted VCPS paths; persist plan, early stage events and E1; preserve existing IDs. | No governance overwrite on ambiguity (HC-07), no newer-schema writes. Exit: structurally valid config and journal. |
| 5 Dirty tree/legacy classification | VCS states, hashes, ownership, Stage 4. | Only VCPS evidence/findings/journal; E1 dirty inventory. | No user-file mutation; HC-07/HC-02 as triggered. Exit: every changed item categorized or explicitly UNKNOWN. |
| 6 Baseline verification | Native command matrix, environment, approvals. | Evidence/output refs and journal; run approved safe checks. | No code fixes or live side effects; HC-03/11/12 as triggered. Exit: result or explicit NOT_RUN for every applicable check. |
| 7 Locally actionable remediation | Stage 6 failures, R0 proof, budget. | Budgeted R0 edits, before/after E2, rerun. | No substantive FAIL fixes, weakened checks, or changed rules; HC-13/06/05 if encountered. Exit: rerun or recorded skip. |
| 8 Baseline establishment | Exact post-remediation revision, Stage 5/6/7 results. | Baseline frontmatter/history and journal. | No rewriting original observations; HC-07/08 as triggered. Exit: ALLOW, ALLOW_WITH_FINDINGS, or BLOCK with reason. |
| 9 Legacy evidence registry | Stage 5/6/8 unresolved state. | Finding records and links; E1/E2 refs. | No default RISK_ACCEPTED; HC-08 for serious acceptance. Exit: all material unresolved states linked or explicit gap. |
| 10 CI alignment | Existing CI map, command matrix, gate needs. | Budgeted minimal CI config change only if separately planned; E1 and E3 refs. | No duplicate/weak jobs; HC-06/13 if scope changes. Exit: mapping or explicit CI gap. |
| 11 VCPS system audit | All canonical artifacts, refs, approvals, journal. | Validation evidence, final journal/status, optional handoff. | No silent repair or inferred PASS. Exit: COMPLETE, PARTIAL, or BLOCKED with reasons. |

**VCPS-SETUP-065.** Stage 11 validates schema and cross-references
([validation.md](../templates/validation.md)), ID uniqueness, canonical
ownership, derived level, journal, baseline, evidence fidelity/freshness,
findings, approval scope, CI claims, portability, and absence of
agent-specific authoritative fields. `COMPLETE` requires all eleven stage
exit conditions, no pending checkpoint, no setup-scoped evidence gap, and
`VCPS-SETUP-041`/`042`. An inherited nonblocking OPEN DEFECT may coexist
with COMPLETE and remains prominently reported; COMPLETE never asserts a
safe product. `PARTIAL` requires a valid portable scaffold and an explicit
list of unfinished checks/stages/gaps; it permits unrelated work under
`VCPS-SETUP-040`. `BLOCKED` means a required human decision, unsupported
newer/older format, unsafe ambiguity, or absent essential capability
prevents safe progress. A read-only pre-scaffold BLOCKED result is returned
externally without writing an unsupported config.

### Stop conditions and adapter contract

**VCPS-SETUP-066.** Stop before a destructive data operation (`HC-01`),
destructive migration (`HC-02`), production write or live side effect
(`HC-03` and `HC-11` as applicable), history rewrite (`HC-04`), security weakening
(`HC-05`), verification weakening (`HC-06`), ambiguous ownership (`HC-07`),
serious risk acceptance (`HC-08`), risk downgrade (`HC-09`), credentials
(`HC-12`), material expansion (`HC-13`), or legal/compliance change
(`HC-15`). Secret exposure stops evidence persistence until redacted.
Read-only production access requires existing authorization and must not
request new credentials without `HC-12`; absent authorization, record
`NOT_RUN` and stop that check.
Unresolved critical ambiguity and unsupported newer schema stop writes.
An approval authorizes only its recorded action/scope/revision and cannot
waive Core evidence, invariant, or gate rules.

**VCPS-SETUP-067.** An adapter supplies repository-relative file read/write
with safe atomic per-file persistence, safe YAML/frontmatter parsing and schema
validation, VCS status/revision/diff inspection, bounded command execution
and output capture, timestamps/hashing, exact-scope human checkpoint
requests, and durable evidence locators. Optional capabilities include
hosted CI inspection, external-provider verification, browser execution,
and production observation. Missing capabilities produce `NOT_RUN` or
`INCONCLUSIVE` evidence and `PARTIAL`/`BLOCKED` according to dependency;
the adapter cannot upgrade a tier by assertion. Agent-specific pointers
may explain invocation but cannot own setup state.

**VCPS-SETUP-068.** Executable outline:

```text
inspect boundary, canonical root, versions, and consistency
select mode by SETUP-050; if unsupported version: return read-only BLOCKED
validate any existing journal and recompute fingerprints
discover stages 1–3 read-only; derive conservative level
build dry-run and bounded plan; present it before first write
for stage from earliest invalidated/incomplete stage through 11:
    validate inputs, revision, budget, and approval scope
    if unsafe/unsupported: append BLOCKED when writable; return BLOCKED
    inspect; run only approved checks; mutate only planned paths
    persist evidence/findings; validate them; append stage event as commit marker
    if changed inputs invalidate prior stages: append INVALIDATED; replan
    if gap remains: record PARTIAL; continue independent stages
audit all artifacts; persist final status and next-action handoff
```

The plan is a proposal, not authorization. Stage 6 may discover a changed
environment; its check result is recorded before any retry. A dry-run
does not itself establish evidence above E1.

# VCPS Core Adversarial Audit — against `0.1.0-draft`

**Audit date:** 2026-10-04
**Scope:** `README.md`, `VERSION`, `standard/**`, `workflows/**`, `templates|adapters|evaluation/README.md`.
**Method:** requirement inventory + 10 adversarial audit passes per the audit
brief. Findings use specification-level classifications only
(`SPEC_DEFECT`, `SPEC_AMBIGUITY`, `SPEC_GAP`, `DESIGN_DECISION`) — never the
runtime `DEFECT`/`EVIDENCE_GAP` vocabulary, which applies to *projects*, not
to this specification.

This audit does not assume the draft was correct because its author wrote
it. Findings below include several genuine defects that would have let a
literal-minded agent produce misleading, gamed, or unsafe results while
technically following the text.

## Requirement inventory (summary)

The final per-line normative inventory appears below. Requirement counts and
reference validation are reported in Final verification; the initial audit
draft had an incorrect count of 169. Project-instance `INV-*` and `AC-*`
identifiers are excluded from the specification requirement count.

---

## Findings

### CA-001 — SPEC_DEFECT (severity: HIGH)
**Affected:** `workflows/bug.md` step 6 vs. owning rule `VCPS-G4-030` (`standard/gates/gate-4-verification.md`).
**Scenario:** An agent follows `workflows/bug.md` literally, which states the
regression-test requirement is "REQUIRED for `BUG`, not merely 'should'" —
unconditionally, for every level/class. The owning rule `VCPS-G4-030` makes
it `SHOULD` in general and `REQUIRED` only at `L3` on `R3` scope. Two
normative documents assert different strengths for the same requirement.
**Expected safe behavior:** Exactly one document owns this rule's strength
(`VCPS.md §5`); workflows cite, never restate at different strength.
**Current behavior:** `workflows/bug.md` silently overrides the owner.
**Exploitability:** Low direct harm (it's accidentally *stricter*, not
weaker), but it is a canonical-ownership violation (`VCPS-CORE §5`) that, if
left standing, legitimizes other documents silently strengthening *or*
weakening owned rules — the latter is the dangerous direction.
**Correction:** Reworded `bug.md` step 6 to cite `VCPS-G4-030` without
restating its strength.
**Blocking phase:** Fix before setup engine (ownership discipline must hold
before automation reads these documents).

### CA-002 — SPEC_DEFECT (severity: MEDIUM)
**Affected:** `standard/lifecycle.md` §3 demotion table, row "Production
regression / incident attributed to the feature".
**Scenario:** A feature is `PRODUCTION_PROVEN`. A regression is found. The
table demotes it to `ACCEPTED`. But `ACCEPTED`'s own entry requirement
(`lifecycle.md §2`) is "`VERIFIED`; ... `E4 EXTERNAL` acceptance". The
regression is direct evidence that the `VERIFIED` evidence underlying the
feature no longer holds for the current revision — so landing the feature in
`ACCEPTED` leaves it in a state whose prerequisite is, by the very fact that
triggered the demotion, not satisfied.
**Expected safe behavior:** Demotion target must not re-assert a state
whose prerequisite the triggering event just disproved.
**Current behavior:** Demotes to a state that silently assumes `VERIFIED`
still holds.
**Exploitability:** An agent (or a human) could read "demoted to `ACCEPTED`"
as "still basically fine, just re-confirm" rather than "verification is
void, re-prove it" — understating the regression's weight.
**Correction:** Changed target to `CODED` ("defect must be fixed and
re-verified before re-reaching `VERIFIED`/`ACCEPTED`"), matching the existing
"blocking DEFECT opened → CODED" row's pattern.
**Blocking phase:** Fix before setup engine.

### CA-003 — SPEC_DEFECT (severity: CRITICAL)
**Affected:** `standard/risk-model.md` §5 (change risk classes); interacts
with `workflows/tiny.md`, `workflows/README.md §2`.
**Scenario — "split one critical change into multiple TINY changes":** An
agent (or a human directing one) splits a change that would be `R3` as a
whole into several sequential changes, each individually touching no
registered invariant's enforcement path and no dimension-3 path in
isolation: e.g. commit 1 adds a new, unguarded write path; commit 2 (run
later, as its own `TINY`/`R1` workflow) flips a flag that activates it;
commit 3 removes the old guard as "cleanup". `VCPS-RISK-041`'s escalation
trigger and `VCPS-WF-TINY-001`'s re-routing check both evaluate *the current
diff in isolation*. Nothing in the Core requires looking at the cumulative
effect of a sequence of related changes. This is explicitly cited in the
audit brief and is real: the current rules are diff-scoped, not
intent/lineage-scoped.
**Expected safe behavior:** Classification must be based on the actual
impact of the *logical unit of work*, not of whichever slice happens to be
in the diff right now (this is the same principle `VCPS-RISK-001` already
states for a single change — it simply doesn't extend across a split
sequence).
**Current behavior:** No rule requires considering sibling/recent changes
from the same feature, ticket, or branch lineage.
**Exploitability:** High. This is the single most effective way to defeat
every gate in this standard without technically violating any single rule.
**Correction:** Added `VCPS-RISK-045` to `risk-model.md §5`: classification
MUST consider other pending or recently-merged changes that are part of the
same logical unit of work; an agent MUST NOT segment a change whose combined
effect would be `R2`/`R3` into separately-classified lower changes to avoid
required gates; where segmentation is suspected, the cumulative effect
governs.
**Blocking phase:** Fix before setup engine — this must be enforceable from
day one, not patched in later.

### CA-004 — SPEC_GAP (severity: HIGH) — Baseline laundering, part 1
**Affected:** VCPS-SETUP-018/021/027/028; VCPS-ART-010; AG-017.
**Attack/scenario:** An agent breaks a check, rewrites the baseline to call the
new failure pre-existing, and lets Gate 3/4 compare against that forged state.
A second variant deletes an old failed observation after repair, erasing
adoption history.
**Expected safe behavior:** Original observations remain immutable. Genuine
pre-existing failures discovered later and exact resolutions are appended
with evidence; neither rewrites the original snapshot.
**Current specification:** VCPS-SETUP-027/028 define the append-only update
history; AG-017 forbids laundering a new failure. CA-040 tightened the first
draft of this correction so even resolved entries are retained historically.
**Exploitability/ambiguity:** High; baseline comparisons lose meaning if the
history can be changed.
**Minimal proposed correction:** Immutable observations plus append-only
addition/resolution records.
**Blocking phase:** Before setup engine.

### CA-005 — SPEC_DEFECT (severity: HIGH) — *Baseline laundering, part 2 / legacy grandfathering*
**Affected:** `workflows/setup.md` Stage 9 (`VCPS-SETUP-022`/`023`),
`VCPS-SETUP-040` (`SETUP_STATUS` semantics).
**Scenario — "mark legacy failures as grandfathered indefinitely" /
"existing production application with no tests":** `VCPS-SETUP-023`'s
ratchet rule only forces escalation for legacy findings at `CRITICAL`
severity on `L2`+ projects. A `HIGH`-severity legacy finding (e.g. a
tenant-isolation gap discovered during `ADOPT` of an `L3` app) that nothing
happens to touch afterward sits in the legacy registry in status `OPEN`
forever, with no rule ever forcing a human decision on it, and no rule
preventing `SETUP_STATUS` from reaching `COMPLETE` while it sits there. A
production `L3` application with zero tests can legitimately reach
`SETUP_STATUS = COMPLETE` (`VCPS-SETUP-012` explicitly permits not blocking
on CI absence), which could be misread as "this project is now under
control" when its actual verification coverage is near zero.
**Expected safe behavior:** "Pre-VCPS legacy" must never become
indistinguishable from "accepted and safe". At minimum, severe legacy risk
must force an explicit human decision before setup can claim completion,
and legacy findings must start life in an unambiguous, non-accepted status.
**Current behavior:** Severity-based escalation stops at `CRITICAL`;
`COMPLETE` has no gate on undispositioned severe legacy findings; initial
status of a legacy finding is unspecified (so nothing stops a status of
`RISK_ACCEPTED` being assigned by default, which would itself violate
`VCPS-CLS-030` but nothing explicitly closes that door at the point of
creation).
**Exploitability:** High at `L3` — this is exactly the scenario the audit
brief calls out, and it compounds with CA-004.
**Correction:**
- `VCPS-SETUP-022` amended: legacy registry findings MUST be created in
  status `OPEN` (never `RISK_ACCEPTED` by default).
- `VCPS-SETUP-023` escalation trigger broadened: at `L3`, `HIGH` severity now
  escalates the same as `CRITICAL` (previously `CRITICAL`-only).
- `VCPS-SETUP-040` amended: `SETUP_STATUS` MUST NOT be `COMPLETE` while any
  `L2`+ project has an undispositioned `CRITICAL` legacy finding, or any `L3`
  project has an undispositioned `CRITICAL`/`HIGH` legacy finding
  ("undispositioned" = not `RESOLVED` and not `RISK_ACCEPTED` via `HC-08`).
  Such a project's setup stops at `PARTIAL` (or `BLOCKED` pending `HC-08`),
  which is an honest status under `VCPS-CORE-032`.
**Blocking phase:** Fix before setup engine.

### CA-006 — SPEC_GAP (severity: MEDIUM)
**Affected:** `standard/anti-gaming.md` §1.
**Scenario — "catch and suppress failures":** `AG-004` blocks shell-level
suppression (`|| true`, `continue-on-error`); `VCPS-G3-005` addresses
swallowed errors but only on `R2`/`R3` *production* paths, not on
verification/check code at any class. Nothing blocks wrapping a flaky or
failing assertion in a `try/catch` inside a test, or a CI script that
catches a subprocess's failure and always exits 0, outside those two narrow
coverages.
**Correction:** Added `AG-015`: "MUST NOT catch, suppress, or otherwise
prevent an error or failed assertion from propagating to its check's
recorded result, solely to avoid a `FAIL`/`ERROR` outcome."
**Blocking phase:** May defer after v1.0, but cheap to fix now — fixed.

### CA-007 — SPEC_GAP (severity: HIGH)
**Affected:** `standard/anti-gaming.md` §1 (missing the inverse of `AG-006`).
**Scenario — "silently change acceptance criteria":** `AG-006` blocks
changing *production behavior* to satisfy a test the agent believes
incorrect. Nothing symmetrically blocks changing the *specification/
acceptance criteria* to match actual (possibly wrong) implementation
behavior, which is the more common gaming move in practice ("the test was
wrong, I updated the expected value to match what the code does").
**Correction:** Added `AG-016`: "MUST NOT change acceptance criteria or
specification to match actual implementation behavior believed incorrect,
without the exception protocol (owner decision); criteria changes MUST be
justified against user/business intent, never against making the current
implementation pass."
**Blocking phase:** Fix before setup engine's adjacent workflows (`FEATURE`/`BUG`) are automated.

### CA-008 — SPEC_AMBIGUITY (severity: LOW)
**Affected:** `standard/evidence-model.md §5` substitution table.
**Scenario — "unit test → browser workflow verified":** Covered in principle
by `VCPS-EVD-002` (no upward inference) and by the adjacent table row ("Unit
test of a function must not prove end-to-end authorization of the route
that calls it"), but the specific UI/e2e confusion named in the audit brief
has no explicit row, inviting an agent to argue it's a novel case.
**Correction:** Added table row: "Unit/component test of a function | A
multi-step browser/UI workflow completing correctly".
**Blocking phase:** May defer after v1.0 — fixed anyway (one row).

### CA-009 — SPEC_DEFECT (severity: HIGH)
**Affected:** `VCPS-IND-005` versus the `I1` definition in
`standard/independence.md`; `VCPS-LVL-001` independence table.
**Scenario:** The same builder conducts an explicitly adversarial second phase
and truthfully records the same identity. The `I1` definition permits this,
but the prior `VCPS-IND-005` prohibited claiming `I1` with that identity.
Literal compliance was impossible. Conversely, an `I2` claim using the same
instance must be rejected.
**Expected safe behavior:** `I1` discloses same-instance verification and its
separate phase; `I2` or higher requires a distinct instance/person.
**Current behavior:** Before correction, contradictory requirements; after
correction, `VCPS-IND-005` distinguishes `I1` from `I2`+ and requires honest
identity and mode records.
**Exploitability/ambiguity:** High: contradictory text invites overclaiming
independence or silently ignoring a requirement.
**Minimal correction:** Replaced `VCPS-IND-005` as described above.
**Blocking phase:** Before adapters and any gate automation.

### CA-010 — SPEC_DEFECT (severity: LOW)
**Affected:** `workflows/audit.md` §"Escalation / re-routing".
**Scenario:** "`AUDIT` MUST NOT modify code, tests, or behavior" is a hard
normative rule but, unlike comparable rules in `tiny.md`
(`VCPS-WF-TINY-001`) and `hotfix.md` (`VCPS-WF-HOTFIX-001/002`), it carries
no requirement ID — inconsistent with `VCPS-CORE-010`'s SHOULD-have-an-ID
expectation, and harder for other artifacts to cite.
**Correction:** Assigned `VCPS-WF-AUDIT-001` to this rule.
**Blocking phase:** May defer after v1.0 — fixed anyway (cosmetic but cheap).

### CA-011 — SPEC_DEFECT (severity: MEDIUM)
**Affected:** `workflows/hotfix.md` §"Deferral discipline".
**Scenario — "HOTFIX becoming a permanent verification bypass":**
`VCPS-WF-HOTFIX-001` requires every `HC-16` deferral to record a follow-up
owner and deadline, but nothing defines what happens when that deadline
passes unmet. Nothing currently stops a deferral from silently persisting
forever past its own stated deadline.
**Correction:** Added `VCPS-WF-HOTFIX-003`: a deferral whose follow-up
deadline has passed unresolved becomes a blocking finding at severity `HIGH`
minimum regardless of original severity, and MUST escalate to `HC-08` for
explicit re-acceptance or immediate scheduling — it MUST NOT silently
persist past its deadline.
**Blocking phase:** Fix before setup engine (this is exactly the kind of
drift that must be caught mechanically, not by someone remembering).

### CA-012 — SPEC_GAP (severity: HIGH)
**Affected:** `workflows/setup.md` §1 (Modes).
**Scenario — "partially installed VCPS":** A prior setup run produced a
valid, consistent config with `SETUP_STATUS = PARTIAL` (e.g. stopped at a
pending checkpoint). The mode table only offers `NEW` (no config),
`ADOPT`(no config but legacy content), `UPGRADE` (version `BEHIND`), `REPAIR`
(inconsistent). A *consistent but incomplete* prior run fits none of these
cleanly — forcing an implementer to shoehorn "resume where I left off" into
`REPAIR`, which is defined around fixing broken state, not continuing valid
state. This is exactly the kind of ambiguity that makes a setup engine
impossible to implement consistently across agents.
**Correction:** Added `VCPS-SETUP-003`: a valid config recording
`SETUP_STATUS` `PARTIAL` or `BLOCKED` from a prior run is resumed directly
from its recorded stage/checkpoint without re-entering mode selection,
provided its `vcps_version` is not `BEHIND` or `AHEAD`.
**Blocking phase:** Fix before setup engine — explicitly load-bearing for implementability.

### CA-013 — SPEC_AMBIGUITY (severity: LOW)
**Affected:** `workflows/setup.md` §3 (`REPAIR` notes).
**Scenario — "newer project VCPS version than agent supports":**
`VCPS-VER-011` says an `AHEAD` executor "MUST NOT modify VCPS artifacts; it
MUST report and stop" — but `setup.md`'s `REPAIR` mode notes only say to
"diagnose the specific inconsistency first", without saying this specific
diagnosis must halt the whole 11-stage sequence immediately rather than
proceed through Stages 2–11 with a newer-than-supported ruleset.
**Correction:** Added a sentence to §3: "If the inconsistency is an `AHEAD`
version, stop immediately after confirming it; do not proceed to Stage 2
onward until a human resolves which specification version governs."
**Blocking phase:** May defer after v1.0 — fixed anyway (one sentence, prevents a real ambiguity for the setup engine).

### CA-014 — SPEC_GAP (severity: LOW)
**Affected:** `workflows/setup.md` Stage 5 table (`VCPS-SETUP-016`).
**Scenario — "uncommitted migrations" / "destructive migration" found during
setup:** The dirty-tree classification table has rows for uncommitted
changes, unexplained files, disabled tests, and dead code, but no explicit
row for uncommitted or pending migration scripts, which is a distinct and
higher-stakes case (`HC-02` territory) that an agent following the table
literally might fold into the generic "uncommitted changes" row and under-escalate.
**Correction:** Added a row: "Uncommitted or pending migration scripts
(especially destructive ones) | `HC-02`; MUST NOT be applied or discarded
during setup."
**Blocking phase:** May defer after v1.0 — fixed anyway (one row).

### CA-015 — SPEC_DEFECT (severity: MEDIUM)
**Affected:** `standard/human-checkpoints.md` §2 (protocol).
**Scenario — "approval reuse across materially changed operations":** A
human approves `HC-01` for "delete rows older than 90 days in table X". The
protocol requires the request to state "the exact action proposed"
(`VCPS-HC-010`) and forbids treating approval of *one checkpoint* as
approval of *another* (`VCPS-HC-003`) — but says nothing about reusing one
approved instance of the *same* checkpoint for a materially different
target, window, or table. Nothing stops an agent from later deleting rows
older than 30 days, or from a different table, citing the same approval.
**Correction:** Added `VCPS-HC-004`: "A checkpoint decision authorizes only
the exact action and scope recorded with it. Any material difference in
target, scope, parameters, or (for `HC-01`/`HC-02`/`HC-03`/`HC-04`) revision
requires a new checkpoint request; a prior decision MUST NOT be reused or
extrapolated to cover it."
**Blocking phase:** Fix before setup engine — this governs every destructive-op checkpoint from the start.

### CA-016 — SPEC_GAP (severity: LOW)
**Affected:** `standard/gates/gate-1-product.md`.
**Scenario:** `VCPS-RISK-010` requires every non-zero dimension rating to
cite an impact-path, but Gate 1's required activities don't explicitly
re-invoke this at change time (only `risk-model.md` states it, and only
setup Stage 3 explicitly performs it at the project level) — an agent could
treat change-level classification as a given rather than something Gate 1
must re-ground in evidence.
**Correction:** Added one line to `VCPS-G1-001` item 4: "This classification
MUST cite impact-path evidence per `VCPS-RISK-010`, not assume the project's
existing ratings apply unchanged to this change's specific path."
**Blocking phase:** May defer after v1.0 — fixed anyway (one line).

### CA-017 — SPEC_AMBIGUITY (severity: LOW)
**Affected:** `standard/human-checkpoints.md` §1, `HC-15` row.
**Scenario:** Bulk/mass export or disclosure of personal/regulated data
(e.g. a report that dumps all users' PII) is irreversible in exposure terms
but isn't obviously "licensing/legal/compliance" by the current row wording,
which reads mostly about dependency licenses and residency.
**Correction:** Broadened `HC-15`'s trigger list to explicitly include
"bulk export or disclosure of personal/regulated data".
**Blocking phase:** May defer after v1.0 — fixed anyway.

### CA-018 — SPEC_AMBIGUITY (severity: LOW)
**Affected:** `standard/portability.md`, `VCPS-PORTABILITY-006`.
**Scenario — handoff completeness:** The handoff record requirement lists
workflow/step, change class, gate statuses, open findings, pending
checkpoints, and next actions — but doesn't explicitly require referencing
the current `vcps_version`, project/component level, or the feature's
lifecycle state, all of which a resuming agent needs and which exist
elsewhere but aren't pointed to from the one record meant to be the
resumption entry point.
**Correction:** Added to `VCPS-PORTABILITY-006`: "The handoff record MUST
also reference (not duplicate) the current `vcps_version`, the relevant
project/component level, and the lifecycle state of any feature in
progress."
**Blocking phase:** May defer after v1.0 — fixed anyway.

### CA-019 — DESIGN_DECISION
**Affected:** `standard/gates/README.md §4` applicability matrix, Gate 6 row.
**Note:** The Gate 6 row doesn't fit the `R0`–`R3` column scheme used by
Gates 1–5, because Gate 6 is evaluated per release unit, not per change
(this is stated explicitly in both the matrix note and `VCPS-G6-001`). This
is an intentional, already-documented carve-out, not a contradiction. No
correction made.

### CA-020 — DESIGN_DECISION (severity: LOW, deferred)
**Affected:** workflows/setup.md Stage 10; VCPS-EVD-020; VCPS-GATE-040.
**Attack:** Two CI workflows disagree on the same scoped check, one PASS and
one FAIL. A naive summary could use only the green result.
**Expected safe behavior:** Retain both results and bar a scoped gate PASS
while the unresolved FAIL exists.
**Current specification:** VCPS-EVD-020 requires separate reporting and
VCPS-GATE-040 bars unsupported PASS; a concrete conflict-resolution policy
is not specified.
**Exploitability/ambiguity:** Low for Core; duplicate-system reconciliation
is an evaluation-layer choice.
**Minimal proposed correction:** None in Core; test with duplicate-CI
fixtures in the evaluation layer.
**Blocking phase:** MAY DEFER AFTER v1.0.

### CA-021 — DESIGN_DECISION — Open-questions triage (Audit 10)

| OQ | Classification | Reasoning |
|----|-----------------|-----------|
| `OQ-001` License | MUST RESOLVE BEFORE v1.0 | Publication and reuse terms must be decided before a stable public release; setup implementation can proceed. |
| `OQ-002` Artifact schema format | **MUST RESOLVE BEFORE SETUP ENGINE** | The setup engine literally writes these records; it cannot be implemented without a concrete schema. |
| `OQ-003` `.vcps/` directory layout at scale | **MUST RESOLVE BEFORE SETUP ENGINE** | Same reason; also load-bearing for `VCPS-ART-001`. |
| `OQ-004` Monorepo worked examples | MUST RESOLVE BEFORE ADAPTERS | `VCPS-RISK-021` is already mechanically sufficient for the setup engine; worked examples are polish. |
| `OQ-005` Independence-mode↔orchestration mapping | MUST RESOLVE BEFORE ADAPTERS | Explicitly an adapter-layer concern by its own text; setup engine doesn't execute Gate 4/5. |
| `OQ-006` `KNOWN_LIMITATION` expiry mechanism | MUST RESOLVE BEFORE v1.0 | Explicit acceptance can still persist indefinitely; the owner must decide whether periodic review is required before stability is claimed. |
| `OQ-007` ADOPT reconciliation with a pre-existing standard | MUST RESOLVE BEFORE ADAPTERS | The corrected 11-stage machine can proceed mechanically today (treat unfamiliar artifacts as legacy content via Stage 5/`HC-07`); a dedicated worked procedure is a refinement, not a blocker. |
| `OQ-008` Observation-window defaults | MAY DEFER AFTER v1.0 | `VCPS-G1-001` item 6 already requires a per-feature window; defaults are convenience. |
| `OQ-009` Formalize `L0` tier | MAY DEFER AFTER v1.0 | Optional convenience tier. |
| `OQ-010` Conformance badge format | MAY DEFER AFTER v1.0 | Evaluation-layer, explicitly out of scope for this pass. |

---

## Corrections applied (normative changes)

| File | Change |
|------|--------|
| `workflows/bug.md` | Step 6 reworded to cite `VCPS-G4-030` without restating its strength (CA-001). |
| `standard/lifecycle.md` | Demotion-table row for production regression changed from `ACCEPTED` to `CODED` (CA-002). |
| `standard/risk-model.md` | Added `VCPS-RISK-045` (cumulative/segmentation classification) (CA-003). |
| `workflows/setup.md` | Added `VCPS-SETUP-003` (resume a valid `PARTIAL`/`BLOCKED` setup) (CA-012); added baseline update procedure `VCPS-SETUP-027`/`021b` (CA-004); amended `VCPS-SETUP-022` (legacy findings created `OPEN`) and `VCPS-SETUP-023` (HIGH+ escalates at L3) (CA-005); amended `VCPS-SETUP-040` (`COMPLETE` gated on disposition) (CA-005); added AHEAD-stop sentence to §3 (CA-013); added Stage-5 migration row (CA-014). |
| `standard/anti-gaming.md` | Added `AG-015` (catch/suppress to dodge FAIL) (CA-006), `AG-016` (silently change criteria to match broken code) (CA-007), `AG-017` (baseline rewriting) (CA-004). |
| `standard/evidence-model.md` | Added substitution-table row for unit test vs. browser workflow (CA-008). |
| `standard/independence.md` | Corrected `VCPS-IND-005`: same identity is disclosed and allowed at `I1`, prohibited at `I2`+ (CA-009). |
| `workflows/audit.md` | Assigned `VCPS-WF-AUDIT-001` to the no-mutation rule (CA-010). |
| `workflows/hotfix.md` | Added `VCPS-WF-HOTFIX-003` (lapsed-deadline escalation) (CA-011). |
| `standard/human-checkpoints.md` | Added `VCPS-HC-004` (approval scope binding) (CA-015); broadened `HC-15` row (CA-017). |
| `standard/gates/gate-1-product.md` | Added impact-path citation requirement to `VCPS-G1-001` item 4 (CA-016). |
| `standard/portability.md` | Amended `VCPS-PORTABILITY-006` to require referencing version/level/lifecycle state (CA-018). |

`VERSION` unchanged at `0.1.0-draft` — the draft tag already signals no
stability guarantee (`VCPS-VER-003`); these are corrections within the same
draft, not a release.

## Scope note

No `adapters/`, `templates/`, or `evaluation/` content exists to audit
beyond their placeholder READMEs (confirmed empty of normative claims). No
agent-specific normative requirement was found in `standard/` or
`workflows/` beyond informative examples naming Claude Code/Codex as future
adapters (`README.md`, `standard/open-questions.md`, `workflows/setup.md` —
all non-normative context, not `MUST`/`MUST NOT` text).

## Additional findings from independent re-audit

The earlier audit draft was audited as work in progress. These findings correct
omissions and incorrect conclusions in that draft. Every correction below is
present in the current Core or workflow text.

### CA-022 — SPEC_DEFECT (HIGH)
- Affected: VCPS-GATE-002 and matrix; workflows/bug.md step 4; workflows/review.md gate mapping.
- Attack: An R3 authorization bug fix claims unchanged design and marks Gate 2 NOT_APPLICABLE under the old BUG/REVIEW prose, although the matrix requires Gate 2.
- Expected: R2/R3 remediation always evaluates Gate 2.
- Current: BUG and REVIEW now follow the matrix; R1 retains the conditional VCPS-G2-001 trigger.
- Exploitability: High; literal workflow following skipped critical-state design analysis.
- Minimal correction: Cite the matrix in both workflows.
- Blocking phase: Before adapters.

### CA-023 — SPEC_DEFECT (HIGH)
- Affected: VCPS-GATE-032; workflows/release.md step 2.
- Attack: Gates 4/5 pass while required Gate 1 or 2 is NOT_EVALUATED. The old shared Gate 6 prerequisite named only Gates 4/5, conflicting with RELEASE.
- Expected: Check every required Gate 1–5 outcome before Gate 6 PASS.
- Current: VCPS-GATE-032 now names Gates 1–5 on the release revision.
- Exploitability: High; release could lack defined intent or design.
- Minimal correction: Expand one shared prerequisite.
- Blocking phase: Before release automation.

### CA-024 — SPEC_DEFECT (HIGH)
- Affected: VERIFIED transition in standard/lifecycle.md; VCPS-GATE-010.
- Attack: An L2 R1 change has permitted Gate 4 PARTIAL. The old transition row first demanded PASS and later allowed PARTIAL; either reading was plausible.
- Expected: Permitted PARTIAL can support VERIFIED with its gap visible; prohibited PARTIAL cannot.
- Current: The VERIFIED row states allowed outcomes once and cites VCPS-GATE-010.
- Exploitability: High; lifecycle claims could be arbitrarily strengthened or blocked.
- Minimal correction: Rewrite that transition row.
- Blocking phase: Before adapters.

### CA-025 — SPEC_DEFECT (HIGH)
- Affected: shared gate outcomes; Gate 3 outcome table; VCPS-SETUP-018/021.
- Attack: A baseline check fails and still fails. Gate 3 formerly allowed PASS with that baseline FAIL, obscuring the raw check result.
- Expected: The check remains FAIL. A non-blocking inherited failure yields PARTIAL with a finding; a blocking failure yields BLOCKED.
- Current: Shared PASS excludes unresolved scoped findings; Gate 3 PASS requires passing static checks and its PARTIAL row names inherited failures. VCPS-SETUP-042 preserves raw results.
- Exploitability: High, especially during legacy adoption.
- Minimal correction: Align shared and Gate 3 outcome tables.
- Blocking phase: Before setup engine.

### CA-026 — SPEC_GAP (CRITICAL)
- Affected: VCPS-HC-030/031; HC-06/08/10/14/16.
- Attack: An Owner pre-authorizes all future gate deferrals, feature acceptances, HIGH risk acceptances, or releases. The former exclusion list allowed those broad approvals.
- Expected: Verification weakening, risk acceptance, release go/no-go, feature acceptance, and HOTFIX deferral require per-instance human decisions. Other pre-authorizations are bounded.
- Current: VCPS-HC-031 excludes those checkpoints and says pre-authorization cannot waive gate, evidence, or invariant requirements.
- Exploitability: Critical; nominal approval records could bypass meaningful decisions.
- Minimal correction: Narrow VCPS-HC-031.
- Blocking phase: Before setup engine.

### CA-027 — SPEC_GAP (HIGH)
- Affected: Revision definition; VCPS-EVD-030/050/051/052; VCPS-SETUP-021.
- Attack: Baseline checks run on a dirty tree with an untracked patch, but cite HEAD. Another agent checks out HEAD and accepts evidence for different content.
- Expected: Exact evaluated content, including relevant untracked files, is reconstructable.
- Current: VCPS-EVD-052 and the glossary require a reconstructable worktree identity; setup binds the baseline to it.
- Exploitability: High for dirty ADOPT and cross-machine handoff.
- Minimal correction: Define dirty-worktree revision binding.
- Blocking phase: Before setup engine and project schema.

### CA-028 — SPEC_GAP (HIGH)
- Affected: VCPS-SETUP-018/022/040/041/042.
- Attack: An existing production app has no tests. Stage 6 runs every discovered test (none) and setup reaches COMPLETE, implying control.
- Expected: Missing executable verification is an owned EVIDENCE_GAP; setup remains PARTIAL. Baseline establishment is not acceptance.
- Current: VCPS-SETUP-042 and the status table make this explicit.
- Exploitability: High; empty discovery looks green.
- Minimal correction: One setup status rule and table clarification.
- Blocking phase: Before setup engine.

### CA-029 — SPEC_AMBIGUITY (MEDIUM)
- Affected: VCPS-GATE-050; workflows/review.md step 6 and mapping.
- Attack: A read-only REVIEW finds a security issue outside any remediation diff. Old prose said to apply Gate 5 to the whole scope, but Gate 5 requires a change record; no change identifier exists.
- Expected: Broader inspection records evidence/findings; each remediation diff gets Gate 5 per matrix.
- Current: REVIEW separates those actions.
- Exploitability: Medium; false gate records or routing loops could result.
- Minimal correction: Clarify REVIEW step 6 and mapping.
- Blocking phase: Before adapters.

### CA-030 — SPEC_DEFECT (MEDIUM)
- Affected: VCPS-CLS-001; workflows/review.md step 4.
- Attack: A statically demonstrable access-control defect cannot be executed locally. Old REVIEW text required reproduction, despite the classification owner allowing deterministic E1 proof.
- Expected: REVIEW can remediate a demonstrated DEFECT; Gate 4 still requires verification evidence and records execution gaps.
- Current: Step 4 cites VCPS-CLS-001 without a second classification threshold.
- Exploitability: Medium.
- Minimal correction: Remove the extra reproduction precondition.
- Blocking phase: Before adapters.

## Adversarial scenario results

A result of Prevented means the corrected normative text bars the unqualified
stronger claim. It does not claim a future implementation detects deliberate
record forgery.

### Evidence integrity: 12 attacks

| Attack | Result | Normative barrier |
|---|---|---|
| Mocked provider called real-provider acceptance | Prevented | VCPS-EVD-040/041 provider row; VCPS-LVL-021 |
| PGlite called PostgreSQL concurrency proof | Prevented | VCPS-EVD-041; VCPS-LVL-020 |
| YAML parser called hosted CI success | Prevented | VCPS-EVD-041; E3 definition and run reference |
| Unit test called browser workflow proof | Prevented | VCPS-EVD-002/041 and browser row |
| HTTP 200 called business success | Prevented | VCPS-EVD-022; VCPS-G4-005 |
| Local test called production proof | Prevented | E2/E5 definitions; VCPS-LC-003; VCPS-G6-020 |
| Stale result called current verification | Prevented | VCPS-EVD-050/051/052; VCPS-GATE-030 |
| Skipped test called PASS | Prevented | VCPS-EVD-020/021; AG-007 |
| Environment-blocked command called PASS | Prevented | ERROR/NOT_RUN definitions; VCPS-EVD-020; VCPS-LVL-010 |
| Static inspection called executed verification | Prevented | E1/E2 definitions; VCPS-EVD-011/030 |
| Agent statement called executable evidence | Prevented | VCPS-EVD-001/003 |
| Same author claims independent verification | Prevented if recorded honestly | VCPS-IND-005/010 discloses I1; I2+ requires distinct identity. Forgery detection remains evaluation-layer work. |

### Anti-gaming: 17 attacks

| Attack | Result | Rule |
|---|---|---|
| Delete, skip, quarantine failing tests | Exposed | AG-001; VCPS-EVD-021; VCPS-AG-030 |
| Narrow test discovery/focused runs | Exposed | AG-012; VCPS-G4-002/007 |
| Weaken assertions/snapshot overwrite | Exposed | AG-002; VCPS-AG-020 |
| Lower coverage or quality thresholds | Exposed | AG-003; HC-06 |
| Exclude files from coverage | Exposed | AG-005 |
| Disable lint rules/blanket ignores | Exposed | AG-005 |
| Use shell or CI failure suppression | Exposed | AG-004 |
| Catch and suppress failed assertions | Exposed | AG-015 |
| Replace integration tests with mocks | Exposed | AG-013; VCPS-EVD-041 |
| Silently change acceptance criteria | Exposed | AG-016; VCPS-G1-001; HC-13 |
| Relabel bug KNOWN_LIMITATION | Exposed | VCPS-CLS-001/005/030; HC-08 |
| Relabel missing evidence NOT_APPLICABLE | Exposed | VCPS-GATE-002; VCPS-CLS-003 |
| Downgrade project/change risk | Exposed | VCPS-RISK-022/043; AG-014; HC-09 |
| Split critical work into TINY slices | Exposed | VCPS-RISK-045; VCPS-WF-TINY-001 |
| Say gate unnecessary because diff small | Exposed | VCPS-RISK-040 and matrix |
| Rewrite baseline after defect | Exposed | VCPS-SETUP-027/021b; AG-017; VCPS-EVD-052 |
| Grandfather legacy failure forever | Partially constrained | VCPS-SETUP-022/023/041/042 requires open status and severe-risk disposition; accepted risk has no mandatory expiry yet (OQ-006). |

### Risk routing

| Trivial-looking request | Safe route |
|---|---|
| Change POS cancel-button behavior | Trace stock/payment effect; R3 if invariant or dimension 3, otherwise at least R2 for transactional path |
| Small invoice-total change | R3 if financial invariant or dimension 3 affected |
| Rename org_id handling | R3 if tenant-isolation enforcement path touched |
| Clean up payment webhook | R2 minimum for integration; R3 on payment invariant |
| Simplify stock transaction | R3 on stock/atomicity invariant |
| Remove unnecessary authorization check | R2 minimum, often R3, and HC-05 |
| Refactor migration | R3 for authoritative data migration; HC-02 if destructive |
| Make AI action automatic | R3 for privileged action; VCPS-G2-014 and applicable HC |
| Pure text/CSS in L3 repository | R0 if no behavior or enforcement path affected: light Gates 3/4 and I0. L3 evidence tier still applies to configured checks. |

VCPS-RISK-001/040/041 routes by traced impact rather than wording.
VCPS-RISK-045 considers the cumulative logical change. A harmless cosmetic
change in an L3 repository does not inherit R3 Gate 1/2/5 burden.

### Workflow routing

| Ambiguity attack | Resolution |
|---|---|
| User calls behavior change TINY | VCPS-WF-002 and VCPS-WF-TINY-001 re-route |
| User calls ordinary bug HOTFIX | HOTFIX entry requires confirmed live production impact |
| REVIEW discovers new intended behavior | VCPS-WF-003 and REVIEW Gate 1 route to FEATURE |
| REVIEW finds proven defect | Remediation is a distinct change through required Gates 2–5 |
| AUDIT finds code fix | VCPS-WF-AUDIT-001 forbids code mutation; route to BUG/REVIEW |
| RELEASE finds stale evidence | VCPS-GATE-032 blocks; reverify or remove change |
| HOTFIX attempts permanent bypass | HC-16 records scope/owner/deadline; VCPS-WF-HOTFIX-003 escalates lapse |
| Risk rises/falls during work | VCPS-RISK-043 re-applies gates and records downgrade reason/HC-09 |

### Setup mode attacks

| Scenario | Required route/result |
|---|---|
| Clean new repository | NEW; stages 1–11 |
| Large dirty repository | ADOPT; HC-07 for unattributed changes; exact revision snapshot |
| Consistent partial installation | VCPS-SETUP-003 resumes recorded stage |
| Corrupted installation | REPAIR takes precedence; preserve IDs/history |
| Project version newer than executor | AHEAD/REPAIR diagnosis then stop; VCPS-VER-011 |
| Older project version | UPGRADE; meaning-changing records surfaced |
| Unexplained files | HC-07; no discard or commit by assumption |
| Pending/destructive migration | HC-02; no apply or discard during setup |
| Failing baseline tests | Raw FAIL and linked findings; no automatic acceptance |
| Environment blocks check | ERROR or NOT_RUN, finding and PARTIAL/BLOCKED by severity |
| Package registry unavailable | ERROR, not PASS; owned gap |
| No CI | EVIDENCE_GAP; L2/L3 substitution cannot exceed PARTIAL |
| Duplicate CI workflows disagree | Both results preserved; unresolved scoped FAIL bars PASS |
| Production app without tests | VCPS-SETUP-042; setup PARTIAL |
| Monorepo mixed risk domains | VCPS-RISK-021 component ratings; shared paths inherit higher level |

### Baseline inheritance boundary

A genuinely pre-existing scoped failure can be inherited only as an OPEN
finding with its raw result, severity, owner, and touch rule
(VCPS-SETUP-018/021/022/042). This includes old failing tests, disabled
checks, dependency uncertainty, and unavailable production evidence. It never
becomes PASS or RISK_ACCEPTED merely by being old. Unknown dirty files require
HC-07; destructive migrations require HC-02. A demonstrated critical invariant
or tenant-isolation violation is a CRITICAL DEFECT (VCPS-CLS-001/020), triggers
VCPS-SETUP-023/041, and cannot be hidden as KNOWN_LIMITATION under
VCPS-CLS-005. A newly introduced failure cannot enter the old baseline
without an earlier reconstructable revision (VCPS-SETUP-027/021b). Explicit
human acceptance remains separate; its expiry policy is OQ-006.

### Human checkpoint integrity: HC-01 through HC-16

| Checkpoints | Attack checked | Boundary |
|---|---|---|
| HC-01/02/03/04 | Data destruction, migration, production operation, history rewrite | VCPS-HC-001/004 binds action, scope, revision |
| HC-05/06 | Security or verification weakening | Per-instance decision under VCPS-HC-031; AG replacement evidence still required |
| HC-07/08/09 | Ambiguous ownership, serious risk acceptance, risk downgrade | Recorded human decision; HC-08/09 cannot be pre-authorized |
| HC-10/11/12 | Release, live side effects, credentials | HC-10 per release; HC-11/12 bounded by VCPS-HC-030/031 |
| HC-13/14/15/16 | Scope expansion, feature acceptance, legal/data exposure, HOTFIX deferral | HC-14/16 per instance; others action/scope bounded |

VCPS-HC-003 bars self-approval and silence as consent. VCPS-HC-004 bars
reuse after material change. VCPS-HC-020 makes the decision portable.
Ordinary local checks and recording EVIDENCE_GAP do not themselves require a
checkpoint.

### Portability handoffs

| Handoff | Required repository state |
|---|---|
| Claude to Codex; Codex to Claude | VCPS-PORTABILITY-001/002/003/006: private memory is non-authoritative; handoff points to version, level, lifecycle, gates, findings, approvals |
| Agent to human engineer | Plain-text records and stable IDs under VCPS-ART-001/010/011 |
| Local to CI | Exact revision/content under VCPS-EVD-030/052; E2 is not relabeled E3 |
| CI to another machine | Retrievable run locator and repository summary at L2+ under VCPS-EVD-031 and VCPS-PORTABILITY-004 |

Project artifacts carry version (VCPS-CORE-030), level/invariants
(VCPS-RISK-030), baseline/setup status (VCPS-SETUP-021/026), findings
(VCPS-CLS-040), evidence (VCPS-EVD-030), lifecycle (VCPS-LC-020), and human
decisions (VCPS-HC-020). OQ-002/003 remain blocking for concrete
schemas/layout; until then executors can satisfy minimum fields in
incompatible formats.

## Additional normative changes

| File | Correction | Finding |
|---|---|---|
| standard/gates/README.md | PASS excludes unresolved scoped findings; Gate 6 checks required Gate 1–5 outcomes | CA-023, CA-025 |
| standard/gates/gate-3-implementation.md | Baseline FAIL yields PARTIAL/BLOCKED, never a passing static check | CA-025 |
| standard/lifecycle.md | VERIFIED row consistently permits only allowed PARTIAL | CA-024 |
| standard/human-checkpoints.md | HC-031 narrows pre-authorization and bars waiver of gate/evidence/invariant rules | CA-026 |
| standard/glossary.md; standard/evidence-model.md | Reconstructable dirty-worktree revision and VCPS-EVD-052 | CA-027 |
| workflows/setup.md | Exact baseline revision; no-tests production app and raw non-PASS baseline results remain PARTIAL; status table clarified | CA-027, CA-028 |
| workflows/bug.md; workflows/review.md | Gate 2 follows matrix; REVIEW broader inspection separated from remediation Gate 5; static demonstration may establish DEFECT | CA-022, CA-029, CA-030 |

No product code, adapter, template, installer, CI definition, or application
code was changed.

### CA-031 — SPEC_GAP (HIGH)
- Affected: VCPS-SETUP-018/020/021.
- Attack: Stage 6 records ERROR for a broken lint config. Stage 7 fixes the config, but Stage 8 establishes the pre-fix baseline without rerunning lint, so the baseline is stale on establishment.
- Expected: Keep both observations; rerun affected checks; baseline the post-fix exact revision.
- Current: VCPS-SETUP-020 now requires that rerun and recorded before/after results.
- Exploitability: High; setup could present an obsolete baseline as current.
- Minimal correction: Add a rerun sentence to Stage 7.
- Blocking phase: Before setup engine.

### CA-032 — SPEC_DEFECT (HIGH)
- Affected: VCPS-SETUP-001 NEW/ADOPT conditions.
- Attack: A repository with application code but no prior production-quality assumption satisfies both old NEW and ADOPT wording. Two agents can choose different procedures.
- Expected: Existing substantive code/tests/CI or VCPS-like artifacts route ADOPT; an empty scaffold routes NEW.
- Current: VCPS-SETUP-001 now uses disjoint conditions.
- Exploitability: High for consistent setup automation.
- Minimal correction: Replace subjective quality-assumption phrase with observable repository content.
- Blocking phase: Before setup engine.

### CA-033 — SPEC_DEFECT (HIGH)
- Affected: VCPS-VER-011 UNKNOWN row; VCPS-SETUP-001.
- Attack: A clean new repository has no config and hence UNKNOWN version. The old version table commanded ADOPT or REPAIR, while setup commanded NEW.
- Expected: Absent config routes NEW/ADOPT by repository content; malformed existing config routes REPAIR.
- Current: VCPS-VER-011 now names those routes.
- Exploitability: High; contradiction on the first setup state transition.
- Minimal correction: Correct one drift-table cell.
- Blocking phase: Before setup engine.

### CA-034 — SPEC_GAP (MEDIUM)
- Affected: VCPS-SETUP-001/003; VCPS-SETUP-004.
- Attack: Setup is invoked again on a valid, EQUAL, COMPLETE installation. It fits none of the four modes or the partial-resume exception; an engine may rescan and overwrite baseline.
- Expected: Recheck consistency, report existing status, leave baseline/history intact.
- Current: VCPS-SETUP-004 defines that idempotent route.
- Exploitability: Medium; repeat invocation could corrupt history.
- Minimal correction: Add an already-complete branch.
- Blocking phase: Before setup engine.

### CA-035 — SPEC_DEFECT (HIGH)
- Affected: VCPS-WF-010; workflows/setup.md and workflows/audit.md.
- Attack: A read-only AUDIT or initial SETUP has no change class and evaluates no change gate, yet the old common contract required every workflow to record a change class and gate outcomes. An agent could invent R0/PASS records for compliance.
- Expected: Non-change workflows record scope and inspected gate states; change workflows record class and evaluated outcomes.
- Current: VCPS-WF-010 distinguishes these cases and RELEASE records the highest included class.
- Exploitability: High; it invited fabricated gate evidence.
- Minimal correction: Qualify the common contract by workflow type.
- Blocking phase: Before setup engine and adapters.

### CA-036 — SPEC_AMBIGUITY (MEDIUM)
- Affected: workflows/audit.md report step/output; VCPS-CORE-033.
- Attack: An AUDIT reports 100% coverage by silently choosing a narrow denominator.
- Expected: Coverage names its scope, numerator, denominator, and evidence basis.
- Current: AUDIT step 7 now requires those fields.
- Exploitability: Medium; a conformance claim could mislead while formally reporting coverage.
- Minimal correction: Add denominator and scope to the report step.
- Blocking phase: Before evaluation suite.

### CA-037 — SPEC_DEFECT (CRITICAL)
- Affected: standard/gates/gate-6-release.md outcome table; workflows/release.md steps 4–5; HC-10.
- Attack: A human records REJECTED on go/no-go. The old Gate 6 PASS row required only a recorded decision; the RELEASE sequence then said Deploy.
- Expected: REJECTED or unmet conditions blocks Gate 6 and deployment.
- Current: Gate 6 PASS requires APPROVED or APPROVED_WITH_CONDITIONS with every condition met; RELEASE explicitly stops on no-go.
- Exploitability: Critical; it inverted the human release veto.
- Minimal correction: Tighten Gate 6 outcome rows and RELEASE deploy step.
- Blocking phase: Before release automation.


### CA-038 — DESIGN_DECISION (MEDIUM)
- Affected: VCPS-GATE-010; standard/levels.md §5; HC-08.
- Attack: At L3, an R2 change has a LOW residual Gate 4 gap. VCPS-GATE-010 still requires a per-instance HC-08 decision before progression. This is safe but may create unnecessary human traffic for small, low-impact residuals.
- Expected: A deliberate product policy balancing L3 assurance with usable review load, while never treating the gap as PASS.
- Current: The conservative checkpoint rule remains. No unsafe bypass was found.
- Exploitability/ambiguity: Low exploitability; usability is the open issue.
- Minimal proposed correction: None without owner policy evidence. Evaluate with real L3 workflow examples.
- Blocking phase: MUST RESOLVE BEFORE v1.0, not before setup engine.

### CA-039 — SPEC_GAP (MEDIUM)
- Affected: VCPS-SETUP-018/042; VCPS-EVD-020.
- Attack: A flaky baseline check completes without a reliable verdict. The old Stage 6 result list omitted INCONCLUSIVE, allowing the executor to force FAIL, ERROR, or PASS.
- Expected: Preserve INCONCLUSIVE and create a linked finding; never summarize it as PASS.
- Current: Stage 6 and VCPS-SETUP-042 include INCONCLUSIVE.
- Exploitability/ambiguity: Medium; a flaky check could be laundered green.
- Minimal correction: Add the existing result value to setup lists.
- Blocking phase: Before setup engine.

### CA-040 — SPEC_DEFECT (HIGH)
- Affected: VCPS-SETUP-027/028; VCPS-ART-010; CA-004 first correction.
- Attack: The first audit correction allowed removing a baseline failure after resolution. That erased the historical observation and broke later audit reconstruction.
- Expected: Append a resolution entry linked to the original observation; any current view may omit the resolved failure only while preserving original history.
- Current: VCPS-SETUP-027 now makes original observations immutable and defines append-only addition/resolution records.
- Exploitability/ambiguity: High; an agent could erase adoption defects while claiming they were fixed.
- Minimal correction: Replace removal with append-only resolution.
- Blocking phase: Before setup engine.



## Final verification

The final consistency pass used the corrected Core/workflow text, not the
initial audit draft. All previously failing conceptual attacks in CA-001
through CA-040 were re-read against the corrected requirement cited in each
finding. The 12 evidence attacks, 17 gaming attacks, risk-routing requests,
workflow routes, setup cases, baseline inheritance, checkpoint cases, and
handoffs above are the replay record. Deliberate falsification of artifacts
cannot be prevented by normative prose alone; the future evaluation suite
must test detection.

| Check | Final result |
|---|---|
| Normative consistency | No remaining direct contradiction found in gate exit, workflow routing, lifecycle transitions, or setup mode precedence after corrections. |
| Requirement IDs | 225 definitions, 225 unique, 0 duplicate; 0 undefined in-text requirement references. |
| Normative inventory | 281 modal-bearing source lines and 311 uppercase modal occurrences; full line inventory follows. |
| Evidence results | PASS, FAIL, NOT_RUN, ERROR, INCONCLUSIVE retain distinct meanings; no unexecuted result promotes to PASS. |
| Gate results | PASS, PARTIAL, BLOCKED, NOT_APPLICABLE, NOT_EVALUATED are distinct; baseline failure is never converted to PASS. |
| Workflow names | Eight definitions match eight workflow files: SETUP, FEATURE, REVIEW, BUG, TINY, HOTFIX, AUDIT, RELEASE. |
| Vendor neutrality | No vendor-specific normative modal in Core; named agents occur only as informative examples. |
| Relative links and fragments | 0 broken paths or heading anchors in repository Markdown. |
| Version | VERSION remains 0.1.0-draft. |
| Diff hygiene | git diff --check passed; no commit made. |

There are 40 findings: 18 SPEC_DEFECT, 12 SPEC_GAP, 6 SPEC_AMBIGUITY,
and 4 DESIGN_DECISION. Twenty-eight findings identified phase blockers
before setup engine, adapters, evaluation, or release automation and have
corrections in the current text. The two remaining blockers for a setup
engine are OQ-002 (concrete project artifact schema) and OQ-003 (artifact
layout); both must be resolved during the project-schema design pass before
the engine is implemented. OQ-001, OQ-006, and CA-038 are decisions for
v1.0, not setup-engine prerequisites. All normative changes are listed in
the two correction tables above and the CA-031 through CA-040 entries.

## Complete normative-line inventory

This is a line-level inventory of every uppercase BCP 14 modal in Core and
workflows after corrections. A wrapped requirement can occupy multiple rows;
tables and prose without a requirement ID are included. The source location
is authoritative; excerpts are for navigation, not a substitute for the
full requirement. Requirement IDs are separately counted below.

Modal occurrences: MAY=35, MUST=155, MUST NOT=96, OPTIONAL=1, RECOMMENDED=4, REQUIRED=5, SHALL=1, SHALL NOT=1, SHOULD=12, SHOULD NOT=1.
Normative-bearing lines: 281.

| File:line | Modal | Source excerpt |
|---|---|---|
| standard/VCPS.md:28 | MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT | The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, |
| standard/VCPS.md:29 | SHOULD, SHOULD NOT, RECOMMENDED, MAY, OPTIONAL | **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** are to be |
| standard/VCPS.md:45 | MUST NOT | **VCPS-CORE-001.** Layers 1–3 MUST NOT contain requirements that name, assume, |
| standard/VCPS.md:50 | MUST NOT | **VCPS-CORE-002.** A lower-numbered layer MUST NOT depend on a higher-numbered |
| standard/VCPS.md:51 | MAY, MUST NOT | layer. Workflows MAY reference the Core; the Core MUST NOT require a specific |
| standard/VCPS.md:54 | MUST NOT | **VCPS-CORE-003.** An adapter MUST NOT weaken, reinterpret, or omit a Core or |
| standard/VCPS.md:55 | MAY | Workflow requirement. An adapter MAY add stricter behavior. Where an agent |
| standard/VCPS.md:56 | MUST | cannot perform a required activity, the adapter MUST surface this as an |
| standard/VCPS.md:61 | MUST | Each normative concept has exactly one owning document. Other documents MUST |
| standard/VCPS.md:88 | SHOULD | **VCPS-CORE-010.** Every normative requirement SHOULD carry a stable identifier |
| standard/VCPS.md:90 | MUST NOT | `HC-05` defined in its owning document). Identifiers MUST NOT be reused for a |
| standard/VCPS.md:94 | SHOULD | Project artifacts, evidence, and findings SHOULD cite requirement identifiers |
| standard/VCPS.md:99 | MAY | Roles are functional. One person or system MAY hold several roles unless a |
| standard/VCPS.md:112 | MUST NOT | **VCPS-CORE-020.** An AI agent MUST NOT act as Owner or Approver. |
| standard/VCPS.md:116 | MUST | **VCPS-CORE-030.** A project that adopts VCPS MUST record, in repository-readable |
| standard/VCPS.md:125 | MUST NOT | **VCPS-CORE-031.** A project MUST NOT claim conformance to a draft |
| standard/VCPS.md:127 | MUST | MUST be labelled as draft. |
| standard/VCPS.md:129 | MUST | **VCPS-CORE-032.** A project whose setup is not `COMPLETE` MUST describe its |
| standard/VCPS.md:133 | MUST | model. It MUST be backed by a system audit (see |
| standard/VCPS.md:146 | MAY | A stricter project-local policy MAY override a weaker VCPS default. A |
| standard/VCPS.md:147 | MUST NOT, MUST | project-local policy MUST NOT weaken a VCPS `MUST` or `MUST NOT`. |
| standard/anti-gaming.md:9 | MUST NOT | MUST NOT perform them to make a task, gate, or check pass. Where such a change |
| standard/anti-gaming.md:10 | MUST | is genuinely correct, it MUST go through the exception protocol (§2). |
| standard/anti-gaming.md:14 | MUST NOT | \| `AG-001` \| MUST NOT delete, skip, quarantine, or disable a test or check. \| |
| standard/anti-gaming.md:15 | MUST NOT | \| `AG-002` \| MUST NOT weaken an assertion (broader matcher, removed field check, increased tolerance, snapshot overwrite accepting new output) without recorded justification showing the old assertion was wrong. \| |
| standard/anti-gaming.md:16 | MUST NOT | \| `AG-003` \| MUST NOT lower coverage, mutation, performance, or quality thresholds merely so the current change passes. \| |
| standard/anti-gaming.md:17 | MUST NOT | \| `AG-004` \| MUST NOT make a blocking check non-blocking: `\|\| true`, `continue-on-error`, `allow_failure`, ignored exit codes, `--passWithNoTests` on a suite that should have tests, or equivalent. \| |
| standard/anti-gaming.md:18 | MUST NOT | \| `AG-005` \| MUST NOT disable, downgrade, or scope-out lint, type checking, static analysis, or security scanning (config changes, blanket ignore comments, `any`-style escapes, excluding paths) without per-instance justification. \| |
| standard/anti-gaming.md:19 | MUST NOT, MUST | \| `AG-006` \| MUST NOT change production behavior solely to satisfy a test the agent believes incorrect; the test's correctness MUST be resolved against intended behavior first. \| |
| standard/anti-gaming.md:20 | MUST NOT | \| `AG-007` \| MUST NOT report `NOT_RUN`, `ERROR`, or `INCONCLUSIVE` as `PASS` (see VCPS-EVD-020). \| |
| standard/anti-gaming.md:21 | MUST NOT | \| `AG-008` \| MUST NOT reclassify `EVIDENCE_GAP` as `DEFECT` without reproduction or static demonstration (see VCPS-CLS-001). \| |
| standard/anti-gaming.md:22 | MUST NOT | \| `AG-009` \| MUST NOT declare a lifecycle state, gate `PASS`, or production readiness without the required evidence (see VCPS-LC-001). \| |
| standard/anti-gaming.md:23 | MUST NOT | \| `AG-010` \| MUST NOT special-case test environments in production code (e.g. `if (process.env.TEST) return ok`) to pass checks. \| |
| standard/anti-gaming.md:24 | MUST NOT | \| `AG-011` \| MUST NOT edit evidence, gate, finding, or checkpoint records to misstate what happened; corrections are appended, not rewritten. \| |
| standard/anti-gaming.md:25 | MUST NOT | \| `AG-012` \| MUST NOT narrow the test selection (filters, focused tests, changed-files-only modes) for gate evidence below what the gate requires. \| |
| standard/anti-gaming.md:26 | MUST NOT | \| `AG-013` \| MUST NOT replace real verification with mocks of the component under test. \| |
| standard/anti-gaming.md:27 | MUST NOT | \| `AG-014` \| MUST NOT downgrade a change class or project level to reduce required gates (see VCPS-RISK-043, `HC-09`). \| |
| standard/anti-gaming.md:28 | MUST NOT | \| `AG-015` \| MUST NOT catch, suppress, or otherwise prevent an error or failed assertion from propagating to its check's recorded result, solely to avoid a `FAIL`/`ERROR` outcome. \| |
| standard/anti-gaming.md:29 | MUST NOT, MUST | \| `AG-016` \| MUST NOT change acceptance criteria or specification to match actual implementation behavior believed incorrect, without the exception protocol (§2); criteria changes MUST be justified against user/business intent, never against making the current implementation pass. \| |
| standard/anti-gaming.md:30 | MUST NOT | \| `AG-017` \| MUST NOT rewrite or alter the baseline (see [../workflows/setup.md §Baseline Update Procedure](../workflows/setup.md#baseline-update-procedure)) to reclassify a newly-introduced failure as pre-existing. \| |
| standard/anti-gaming.md:45 | MAY | **VCPS-AG-021.** At `R0`/`R1` scope, a test that tests removed functionality MAY |
| standard/anti-gaming.md:51 | MUST | **VCPS-AG-030.** Gate 3 and Gate 4 reviews MUST inspect the diff for the |
| standard/artifacts.md:9 | MUST | **VCPS-ART-001.** A project MUST keep VCPS artifacts under a single |
| standard/artifacts.md:10 | RECOMMENDED | repository-relative root directory. The RECOMMENDED root is `.vcps/`. The root |
| standard/artifacts.md:11 | MUST, RECOMMENDED | MUST be discoverable from a fixed entry file (RECOMMENDED: `.vcps/config.yaml`). |
| standard/artifacts.md:13 | MUST | **VCPS-ART-002.** VCPS artifacts MUST be committed to version control with the |
| standard/artifacts.md:34 | MUST | **VCPS-ART-010.** Records MUST be append-friendly: changing a status or |
| standard/artifacts.md:38 | MUST | **VCPS-ART-011.** Each record type MUST have a stable identifier scheme. |
| standard/artifacts.md:39 | RECOMMENDED | RECOMMENDED prefixes: `FEAT-`, `FND-`, `EVD-`, `GATE-`, `HCR-` (checkpoint |
| standard/artifacts.md:42 | MUST | **VCPS-ART-012.** Artifacts MUST be machine-validatable once schemas exist in |
| standard/artifacts.md:43 | MUST | the templates layer. Until then, artifacts MUST at least contain the minimum |
| standard/classifications.md:8 | MUST | **VCPS-CLS-001.** Every material finding MUST be classified as exactly one of: |
| standard/classifications.md:21 | SHOULD | severity `HIGH` or above SHOULD receive a reproduction before remediation is |
| standard/classifications.md:25 | MUST | or unexecuted check MUST be classified `EVIDENCE_GAP`, not `DEFECT`. |
| standard/classifications.md:28 | MUST | or in the check itself. When the side is unknown, the finding MUST record the |
| standard/classifications.md:32 | MUST NOT | **VCPS-CLS-005.** `KNOWN_LIMITATION` MUST NOT be used to hide a `DEFECT` that |
| standard/classifications.md:40 | MUST NOT | \| `EVIDENCE_GAP` → `DEFECT` \| Reproduction or static demonstration per VCPS-CLS-001 is recorded. MUST NOT happen on suspicion alone. \| |
| standard/classifications.md:47 | MUST | **VCPS-CLS-010.** Every reclassification MUST be recorded with the prior |
| standard/classifications.md:48 | MUST NOT | classification, the reason, and the evidence. Findings MUST NOT be silently |
| standard/classifications.md:79 | MUST NOT | An agent MUST NOT set `RISK_ACCEPTED` on its own authority. |
| standard/classifications.md:81 | MUST | **VCPS-CLS-031.** A `RESOLVED` `DEFECT` MUST reference remediation evidence |
| standard/classifications.md:87 | MUST | **VCPS-CLS-040.** A finding record MUST include: `id`, `title`, |
| standard/evidence-model.md:9 | MUST | transition, finding classification, or conformance claim MUST be backed by |
| standard/evidence-model.md:12 | MUST NOT | **VCPS-EVD-002. (No upward inference)** A stronger claim MUST NOT be inferred |
| standard/evidence-model.md:54 | MUST NOT | **VCPS-EVD-020.** `NOT_RUN`, `ERROR`, and `INCONCLUSIVE` MUST NOT be reported, |
| standard/evidence-model.md:55 | MUST | summarized, or counted as `PASS`. A summary over multiple checks MUST report |
| standard/evidence-model.md:61 | MUST NOT | **VCPS-EVD-022.** A process exit code or HTTP status alone MUST NOT be |
| standard/evidence-model.md:62 | MUST | treated as proof of business success. Evidence MUST check the business |
| standard/evidence-model.md:68 | MUST | **VCPS-EVD-030.** An evidence record MUST contain: |
| standard/evidence-model.md:80 | MUST | \| `method` \| Command, test identifier, procedure, or inspection method. Executable evidence MUST include a reproduction command or procedure. \| |
| standard/evidence-model.md:88 | MUST, SHOULD | tickets) MUST include enough information to retrieve them later and SHOULD |
| standard/evidence-model.md:92 | MUST | **VCPS-EVD-032.** Producer and verifier identity MUST be recorded at the |
| standard/evidence-model.md:93 | MUST NOT | granularity available. VCPS MUST NOT require any specific vendor, model, or |
| standard/evidence-model.md:99 | MUST | environment the assertion is about MUST list the difference in `limitations`. |
| standard/evidence-model.md:101 | MUST NOT | **VCPS-EVD-041.** Evidence produced on a substitute MUST NOT support assertions |
| standard/evidence-model.md:106 | MUST NOT | \| Evidence \| MUST NOT be used to prove \| |
| standard/evidence-model.md:125 | MUST NOT | **VCPS-EVD-051.** Stale evidence MUST NOT support a gate `PASS` or lifecycle |
| standard/evidence-model.md:126 | MAY | transition for a later revision, except that `E1`/`E2` evidence MAY be carried |
| standard/evidence-model.md:128 | MUST NOT | the assertion. That carry-forward is itself `E1` evidence and MUST NOT be used |
| standard/evidence-model.md:132 | MUST | revision MUST identify the exact evaluated content, including relevant |
| standard/evidence-model.md:135 | MUST NOT | timestamp alone MUST NOT identify a dirty worktree revision. Before evidence |
| standard/evidence-model.md:136 | MUST | supports a later committed revision, the producer MUST establish that its |
| standard/evidence-model.md:146 | MUST | assertion MUST be shown positively. |
| standard/gates/README.md:29 | MUST | \| `BLOCKED` \| The gate cannot pass. MUST carry one or more reason codes: `DEFECT` (open blocking defect), `EVIDENCE` (required evidence missing and gap is blocking), `DECISION` (pending human checkpoint), `DEPENDENCY` (prerequisite gate/external party not ready). \| |
| standard/gates/README.md:32 | MUST NOT | **VCPS-GATE-001.** `NOT_EVALUATED` MUST NOT be treated as `PASS` or |
| standard/gates/README.md:35 | MUST | **VCPS-GATE-002.** `NOT_APPLICABLE` MUST cite the matrix row and the facts |
| standard/gates/README.md:36 | MUST NOT | that make it apply. An agent MUST NOT mark a gate `NOT_APPLICABLE` where the |
| standard/gates/README.md:37 | REQUIRED | matrix marks it `REQUIRED` for the change class. |
| standard/gates/README.md:79 | MUST | **VCPS-GATE-030.** Gates 4 and 5 MUST be evaluated on a recorded revision. |
| standard/gates/README.md:83 | MAY | **VCPS-GATE-031.** Gates MAY be evaluated iteratively. A gate's outcome is |
| standard/gates/README.md:87 | MUST NOT | **VCPS-GATE-032.** Gate 4 MUST NOT be evaluated `PASS` before Gate 3 is `PASS` |
| standard/gates/README.md:88 | MUST NOT | or permitted `PARTIAL` on the same revision. Gate 6 MUST NOT be `PASS` while |
| standard/gates/README.md:92 | MUST NOT | **VCPS-GATE-040.** An agent MUST NOT report a gate outcome stronger than its |
| standard/gates/README.md:97 | MUST | **VCPS-GATE-050.** Each gate evaluation MUST be recorded with: `gate`, |
| standard/gates/gate-1-product.md:25 | MUST | with reasoning. This classification MUST cite impact-path evidence per |
| standard/gates/gate-1-product.md:36 | MUST | **VCPS-G1-003.** For `REVIEW` and `AUDIT`, intended behavior MUST be |
| standard/gates/gate-1-product.md:39 | MUST | conflict or are absent, the ambiguity MUST be recorded as |
| standard/gates/gate-2-architecture.md:24 | MUST | authoritative state on an `R2`/`R3` path, the design MUST state how each of |
| standard/gates/gate-2-architecture.md:36 | MUST | **VCPS-G2-011. (Trust boundaries)** The design MUST identify each trust |
| standard/gates/gate-2-architecture.md:37 | MUST | boundary and MUST treat frontend/client input, external provider responses |
| standard/gates/gate-2-architecture.md:41 | MUST | **VCPS-G2-012. (Failure design)** The design MUST enumerate failure modes for |
| standard/gates/gate-2-architecture.md:46 | MUST | MUST specify: forward plan, backward/rollback or forward-fix plan, data |
| standard/gates/gate-2-architecture.md:51 | MUST | actions MUST define: the action allowlist, limits, human approval thresholds, |
| standard/gates/gate-2-architecture.md:54 | MUST | **VCPS-G2-015.** For each property above, the design MUST name the verification |
| standard/gates/gate-2-architecture.md:60 | MUST | - At `L3` with `R3`, the design MUST be reviewed at independence mode `I1` or higher. |
| standard/gates/gate-3-implementation.md:17 | MUST | **VCPS-G3-001. (Scope discipline)** The change MUST be limited to the |
| standard/gates/gate-3-implementation.md:19 | MUST | untouched files, dependency bumps) MUST be separated or justified. |
| standard/gates/gate-3-implementation.md:21 | MUST | **VCPS-G3-002. (Read before write)** The builder MUST inspect existing code, |
| standard/gates/gate-3-implementation.md:22 | MUST | conventions, and tests in the affected area before modifying it, and MUST |
| standard/gates/gate-3-implementation.md:26 | MUST NOT | **VCPS-G3-003. (No fabrication)** The builder MUST NOT introduce calls to APIs, |
| standard/gates/gate-3-implementation.md:30 | MUST | **VCPS-G3-004. (Dependencies)** New dependencies MUST be justified, pinned per |
| standard/gates/gate-3-implementation.md:34 | MUST NOT | **VCPS-G3-005. (Error handling)** Errors MUST NOT be silently swallowed on |
| standard/gates/gate-3-implementation.md:35 | MUST | `R2`/`R3` paths. Failure paths named in Gate 2 MUST be implemented. |
| standard/gates/gate-3-implementation.md:37 | MUST NOT | **VCPS-G3-006. (Secrets)** Secrets MUST NOT be committed, logged, or embedded in |
| standard/gates/gate-3-implementation.md:40 | MUST | **VCPS-G3-007. (Anti-gaming)** The diff MUST be inspected for verification |
| standard/gates/gate-3-implementation.md:44 | MUST | property MUST be traceable to the code implementing it. |
| standard/gates/gate-3-implementation.md:47 | MUST | and type checks MUST be run on the revision. |
| standard/gates/gate-4-verification.md:19 | MUST | invariant property named in Gate 2 MUST have at least one evidence record on |
| standard/gates/gate-4-verification.md:23 | MUST | to the change scope MUST be run. Results MUST be compared against the baseline; |
| standard/gates/gate-4-verification.md:26 | MUST | **VCPS-G4-003. (Adversarial pass)** For `R1` and above, the verifier MUST |
| standard/gates/gate-4-verification.md:32 | MUST | **VCPS-G4-004. (Invariant evidence for `R3`)** Each affected invariant MUST be |
| standard/gates/gate-4-verification.md:38 | MUST | **VCPS-G4-005. (Business outcome)** Evidence MUST check business outcomes, |
| standard/gates/gate-4-verification.md:41 | MUST | **VCPS-G4-006. (Independence)** Verification MUST meet the independence mode |
| standard/gates/gate-4-verification.md:51 | SHOULD | **VCPS-G4-030.** A `DEFECT` that has been reproduced SHOULD receive an automated |
| standard/gates/gate-4-verification.md:53 | MUST | not practical (e.g. requires unavailable infrastructure), the reason MUST be |
| standard/gates/gate-4-verification.md:55 | REQUIRED | the regression test is REQUIRED unless `HC-08` accepts the gap. |
| standard/gates/gate-4-verification.md:58 | SHOULD | SHOULD be recorded (e.g. run against the parent revision). |
| standard/gates/gate-5-security.md:40 | MUST | authorization, tenant-isolation, and business-logic-abuse categories MUST |
| standard/gates/gate-5-security.md:43 | MAY | **VCPS-G5-012.** Static review alone (`E1`) MAY support `PASS` for categories |
| standard/gates/gate-6-release.md:58 | MUST | **VCPS-G6-020.** After release, observed production evidence (`E5`) MUST be |
| standard/human-checkpoints.md:13 | MUST | MUST stop and obtain a recorded human decision, unless a valid |
| standard/human-checkpoints.md:36 | MUST | checkpoint, it MUST treat the action as triggering it. |
| standard/human-checkpoints.md:38 | MUST NOT | **VCPS-HC-003.** An agent MUST NOT approve its own checkpoint, approve on |
| standard/human-checkpoints.md:45 | MUST NOT | a new checkpoint request; a prior decision MUST NOT be reused or |
| standard/human-checkpoints.md:50 | MUST | **VCPS-HC-010.** A checkpoint request MUST present: |
| standard/human-checkpoints.md:58 | MAY | **VCPS-HC-011.** While waiting, the agent MAY continue work that does not |
| standard/human-checkpoints.md:59 | MUST NOT | depend on the decision. It MUST NOT perform any part of the gated action. |
| standard/human-checkpoints.md:62 | MUST | affected gate or setup stage MUST become `BLOCKED` with reason `DECISION`. |
| standard/human-checkpoints.md:66 | MUST | **VCPS-HC-020.** Each decision MUST be persisted as a VCPS artifact with: |
| standard/human-checkpoints.md:77 | MAY | **VCPS-HC-030.** An Owner MAY pre-authorize a class of actions with a |
| standard/human-checkpoints.md:81 | MUST NOT | **VCPS-HC-031.** Pre-authorization MUST NOT cover `HC-04` on default/protected |
| standard/human-checkpoints.md:84 | MUST | decision. A pre-authorization for any other checkpoint MUST bound the |
| standard/human-checkpoints.md:85 | MUST NOT | specific action class and maximum impact; it MUST NOT waive a gate, evidence, |
| standard/human-checkpoints.md:89 | MUST | change (VCPS-RISK-044) and MUST be made by a human. |
| standard/independence.md:19 | MUST NOT | **VCPS-IND-001.** VCPS MUST NOT require any particular vendor, model, or |
| standard/independence.md:22 | MUST | **VCPS-IND-002.** At `I1` and above, the verifier MUST begin from intended |
| standard/independence.md:24 | MUST | itself, and MUST attempt to refute the builder's claims rather than confirm |
| standard/independence.md:27 | MUST NOT | **VCPS-IND-003.** At `I2` and above, the verifier MUST NOT be given the |
| standard/independence.md:29 | MAY | It MAY read it afterward to reconcile. |
| standard/independence.md:31 | MUST NOT | **VCPS-IND-004.** A verifier MUST NOT modify the change under verification |
| standard/independence.md:35 | MAY | **VCPS-IND-005.** At `I1`, the producer and verifier MAY be the same |
| standard/independence.md:37 | MUST | phase MUST be disclosed. At `I2` or higher, the verifier MUST be a distinct |
| standard/independence.md:39 | MUST | MUST match what actually happened, not what was required; claiming a higher |
| standard/independence.md:44 | MUST | **VCPS-IND-010.** Each gate record for Gates 4 and 5 MUST record the |
| standard/independence.md:49 | MUST, MUST NOT | reviewer), the gap MUST be recorded as an `EVIDENCE_GAP` and the gate MUST NOT |
| standard/independence.md:50 | MUST | exceed `PARTIAL`. At `L3` with an `R3` change, the gate MUST be `BLOCKED` until |
| standard/levels.md:15 | MUST | **VCPS-LVL-001.** A project MUST record its level and the risk-profile |
| standard/levels.md:35 | MAY | \| Feature acceptance \| Owner `E4` (MAY be merge approval) \| Owner `E4` \| Owner `E4` with acceptance criteria listed \| |
| standard/levels.md:36 | SHOULD | \| Production success \| `E5` SHOULD \| `E5` for `PRODUCTION_PROVEN` \| `E5` for `PRODUCTION_PROVEN` with defined window \| |
| standard/levels.md:38 | MAY | **VCPS-LVL-010.** Where no CI exists, an `L2`/`L3` project MAY substitute |
| standard/levels.md:40 | MUST NOT | owner. Such gates MUST NOT exceed `PARTIAL`. |
| standard/levels.md:45 | MUST | isolation, locking, migration behavior, or query semantics MUST be evidenced on |
| standard/levels.md:47 | MAY | documented compatible one). Embedded, in-memory, or emulated engines MAY |
| standard/levels.md:48 | MUST NOT | supplement but MUST NOT replace this evidence. See |
| standard/levels.md:52 | MUST NOT | MUST NOT be satisfied by mocks alone before the feature is `ACCEPTED`. |
| standard/levels.md:61 | SHOULD | \| `R3` \| `I1` \| `I2` \| `I2`, and `I3` or `I4` SHOULD \| |
| standard/lifecycle.md:18 | MUST | every conforming implementation MUST support. `PROPOSED`, `SPECIFIED`, and |
| standard/lifecycle.md:19 | MAY | `WITHDRAWN` MAY be collapsed at `L1`. |
| standard/lifecycle.md:35 | MUST NOT | **VCPS-LC-001.** A feature MUST NOT be reported as done, complete, finished, |
| standard/lifecycle.md:37 | MUST | evidence recorded. Reporting language MUST use the state name when precision |
| standard/lifecycle.md:40 | MUST NOT, MAY | **VCPS-LC-002.** States MUST NOT be skipped. A feature MAY transition through |
| standard/lifecycle.md:43 | MUST NOT | **VCPS-LC-003.** An agent MUST NOT move a feature to `ACCEPTED` or |
| standard/lifecycle.md:49 | MUST | **VCPS-LC-010.** A feature MUST be demoted when its supporting evidence becomes |
| standard/lifecycle.md:61 | MUST, MUST NOT | **VCPS-LC-011.** Demotion MUST be recorded with cause. Demotion MUST NOT |
| standard/lifecycle.md:66 | MUST | **VCPS-LC-020.** A feature record MUST include: `id`, `title`, `state`, |
| standard/open-questions.md:3 | MUST | Unresolved decisions in `0.1.0-draft`. Each MUST be resolved or explicitly |
| standard/portability.md:9 | MUST NOT | records, checkpoint decisions, and acceptance records MUST NOT depend |
| standard/portability.md:12 | MUST | state, finding, or conformance claim MUST be persisted in repository-readable |
| standard/portability.md:15 | MUST | **VCPS-PORTABILITY-002.** VCPS artifacts MUST use open, plain-text formats |
| standard/portability.md:20 | MAY, MUST | memory, prompt files, caches) MAY exist, but MUST be non-authoritative. If an |
| standard/portability.md:24 | MUST | dashboards, ticket systems) MUST be referenced with a stable locator. For |
| standard/portability.md:26 | MUST | (result, revision, key excerpt or hash) MUST also be stored in the repository, |
| standard/portability.md:29 | MUST NOT | **VCPS-PORTABILITY-005.** Artifacts MUST NOT contain secrets, credentials, or |
| standard/portability.md:30 | MUST | unredacted personal data. Evidence that would contain them MUST be redacted |
| standard/portability.md:34 | MUST | work is interrupted, the in-progress state MUST be recorded such that a |
| standard/portability.md:37 | MUST | handoff record MUST also reference (not duplicate) the current |
| standard/portability.md:41 | MUST | **VCPS-PORTABILITY-007.** Identifiers in VCPS artifacts MUST be stable and |
| standard/portability.md:42 | MUST NOT | agent-independent. An artifact MUST NOT require an agent session ID to be |
| standard/portability.md:43 | MAY | interpreted (session IDs MAY appear as informational provenance). |
| standard/portability.md:45 | MUST | **VCPS-PORTABILITY-008.** A new agent taking over a project MUST treat recorded |
| standard/portability.md:46 | MUST | VCPS artifacts as the source of truth over its own prior assumptions, and MUST |
| standard/risk-model.md:9 | MUST | **VCPS-RISK-001.** Risk classification MUST be based on the actual impact of |
| standard/risk-model.md:13 | MUST NOT | **VCPS-RISK-002.** Risk classification MUST NOT be derived solely from the |
| standard/risk-model.md:15 | MAY | `payments/` folder, a `stripe` dependency, or the word "admin"). Keywords MAY |
| standard/risk-model.md:16 | MUST | be used to find candidates for inspection; the classification MUST cite the |
| standard/risk-model.md:39 | MUST | **VCPS-RISK-010.** Each non-zero rating MUST cite at least one impact path |
| standard/risk-model.md:41 | MUST | or stronger. A rating with only `E0 CLAIMED` support MUST be recorded as an |
| standard/risk-model.md:42 | MUST | `EVIDENCE_GAP` and the rating MUST be treated as the higher of the candidate |
| standard/risk-model.md:56 | MAY | **VCPS-RISK-021.** A repository MAY classify components separately. Where a |
| standard/risk-model.md:59 | MUST | component MUST be treated at the higher level for changes on that shared path. |
| standard/risk-model.md:66 | MUST | **VCPS-RISK-030.** An `L2` or `L3` project MUST maintain a critical invariant |
| standard/risk-model.md:67 | MUST | registry. Each entry MUST include: identifier (`INV-<NNN>`), statement as an |
| standard/risk-model.md:71 | MUST | **VCPS-RISK-031.** At `L3`, every dimension rated `3` MUST be covered by at |
| standard/risk-model.md:93 | MUST | **VCPS-RISK-040.** The change class MUST be determined from what the change |
| standard/risk-model.md:94 | MUST NOT | touches, not from its size. Diff size MUST NOT lower a class. |
| standard/risk-model.md:96 | MUST | **VCPS-RISK-041. (Escalation)** A change MUST be raised to `R3` if it modifies |
| standard/risk-model.md:102 | MUST | **VCPS-RISK-042.** When the class is uncertain, the higher candidate class MUST |
| standard/risk-model.md:105 | MAY | **VCPS-RISK-043.** A change's class MAY be re-evaluated during work. If it |
| standard/risk-model.md:106 | MUST | rises, all gates required by the new class MUST be evaluated before the change |
| standard/risk-model.md:107 | MUST | leaves its workflow. If an agent wishes to lower it, the agent MUST record the |
| standard/risk-model.md:114 | MUST | **VCPS-RISK-045. (Segmentation / cumulative effect)** Classification MUST |
| standard/risk-model.md:117 | MUST NOT | MUST NOT segment a change whose combined effect would be `R2`/`R3` into |
| standard/risk-model.md:125 | MUST | generated code, opaque external service), the gap MUST be recorded as an |
| standard/risk-model.md:126 | MUST | `EVIDENCE_GAP`, and classification MUST assume the plausible worst case among |
| standard/versioning.md:16 | MUST, MUST NOT | \| Adds or strengthens a `MUST`/`MUST NOT`, changes an enumerated value, removes or renames an artifact field \| MAJOR (MINOR while `0.x`) \| |
| standard/versioning.md:17 | SHOULD, MAY | \| Adds a `SHOULD`/`MAY`, new optional artifact field, new checkpoint or workflow that does not invalidate existing records \| MINOR \| |
| standard/versioning.md:23 | SHOULD | **VCPS-VER-004.** Each release of the specification SHOULD include an upgrade |
| standard/versioning.md:28 | MUST | **VCPS-VER-010.** A project MUST record the specification version it implements |
| standard/versioning.md:31 | MUST | **VCPS-VER-011. (Drift)** Setup and audit MUST compare the project's |
| standard/versioning.md:38 | MAY, MUST | \| `BEHIND` \| Project older than executor. \| Setup MAY run `UPGRADE`. Until upgraded, the executor MUST apply the project's recorded version where behavior differs, or report the difference as an `EVIDENCE_GAP`. \| |
| standard/versioning.md:39 | MUST NOT, MUST | \| `AHEAD` \| Project newer than executor. \| Executor MUST NOT modify VCPS artifacts; it MUST report and stop for human decision. \| |
| standard/versioning.md:40 | MUST | \| `UNKNOWN` \| No or malformed version. \| With no config, Setup MUST enter `NEW` or `ADOPT` per VCPS-SETUP-001; with a malformed existing config, it MUST enter `REPAIR`. \| |
| standard/versioning.md:42 | MUST NOT | **VCPS-VER-012.** An upgrade MUST NOT silently change a project's level, |
| standard/versioning.md:44 | MUST | changes the meaning of existing records, the upgrade MUST surface each |
| workflows/README.md:4 | MUST NOT | the Core defines *requirements*. A workflow MUST NOT weaken a Core requirement |
| workflows/README.md:22 | MUST | **VCPS-WF-001.** Before starting work, the executor MUST classify the request |
| workflows/README.md:23 | MUST | into exactly one primary intent and record it. Requests spanning intents MUST |
| workflows/README.md:28 | MUST NOT | MUST NOT be run as `TINY`. A request phrased as "hotfix" without production |
| workflows/README.md:29 | MUST NOT | impact MUST NOT be run as `HOTFIX`. |
| workflows/README.md:33 | MUST | intended behavior, `AUDIT` would require changes), the executor MUST stop the |
| workflows/README.md:35 | MAY | Evidence already gathered MAY be carried over if not stale. |
| workflows/README.md:49 | MUST | **VCPS-WF-010.** Every workflow run MUST: |
| workflows/README.md:51 | MUST | - record its intent and project/component level used; change workflows MUST |
| workflows/README.md:52 | MUST | record their change class, and `RELEASE` MUST record the highest class in |
| workflows/README.md:53 | MUST | its release unit. `SETUP` and read-only `AUDIT` MUST record their scope |
| workflows/README.md:57 | MUST | read-only `AUDIT` MUST record the gate states they inspect without |
| workflows/audit.md:49 | MUST NOT | - **VCPS-WF-AUDIT-001.** `AUDIT` MUST NOT modify code, tests, |
| workflows/hotfix.md:16 | MUST NOT | evidence/logs, or `E5` direct observation). Unconfirmed urgency MUST NOT |
| workflows/hotfix.md:21 | REQUIRED, MAY | 3. **Gate 2**: REQUIRED if the fix touches a critical-state mechanism; MAY be |
| workflows/hotfix.md:27 | MAY | 5. **Gate 4 (reduced)**: verification MAY be scoped to the specific harm and |
| workflows/hotfix.md:31 | REQUIRED | 6. **Gate 5**: REQUIRED for any category the fix touches — security |
| workflows/hotfix.md:42 | MUST | requirement under `HOTFIX`. Each deferral MUST record: what was skipped, why, |
| workflows/hotfix.md:47 | MUST NOT | **VCPS-WF-HOTFIX-002.** `HOTFIX` MUST NOT be used to bypass `HC-01` through |
| workflows/hotfix.md:52 | MUST | at severity `HIGH` or higher (regardless of its original severity) and MUST |
| workflows/hotfix.md:54 | MUST NOT | MUST NOT silently persist past its deadline — a `HOTFIX` deferral is not a |
| workflows/review.md:73 | MUST NOT | items with evidence, and an explicit open-gaps list. A `REVIEW` MUST NOT |
| workflows/setup.md:8 | MUST NOT | they MUST NOT define their own divergent sequence. |
| workflows/setup.md:16 | MUST | **VCPS-SETUP-001.** On entry, the executor MUST determine mode by inspecting |
| workflows/setup.md:27 | MUST, MUST NOT | conditions hold. `AHEAD` version MUST route to `REPAIR` and MUST NOT |
| workflows/setup.md:31 | MUST | records `SETUP_STATUS` `PARTIAL` or `BLOCKED` from a prior run MUST be |
| workflows/setup.md:39 | MUST | at the executing version with `SETUP_STATUS` `COMPLETE` MUST route to a |
| workflows/setup.md:41 | MUST NOT | Setup MUST NOT create a fresh baseline or overwrite existing records merely |
| workflows/setup.md:46 | MAY | Stages are sequential but a later stage MAY reveal the need to revisit an |
| workflows/setup.md:74 | SHOULD | this stage; coverage SHOULD improve over subsequent `REVIEW`/`AUDIT` runs. |
| workflows/setup.md:89 | MUST NOT | \| Uncommitted changes of unknown origin \| `HC-07`; MUST NOT be discarded or committed without owner decision. \| |
| workflows/setup.md:93 | MUST NOT | \| Uncommitted or pending migration scripts (especially destructive ones) \| `HC-02`; MUST NOT be applied or discarded during setup. \| |
| workflows/setup.md:95 | MUST NOT | **VCPS-SETUP-017.** This stage MUST NOT delete, rewrite history of, or force- |
| workflows/setup.md:104 | MUST NOT | **VCPS-SETUP-019.** The baseline MUST NOT be used to justify weakening checks; |
| workflows/setup.md:110 | MAY | **VCPS-SETUP-020.** The executor MAY fix trivial, unambiguous, local |
| workflows/setup.md:113 | MUST NOT | provided the fix is `R0` and recorded. It MUST NOT fix substantive baseline |
| workflows/setup.md:115 | MUST | any such fix, affected checks MUST be rerun and the pre-fix and post-fix |
| workflows/setup.md:127 | MUST | **VCPS-SETUP-027.** The original baseline observations MUST remain immutable. |
| workflows/setup.md:128 | MAY | After establishment, baseline history MAY only be extended by: |
| workflows/setup.md:135 | MAY, MUST | MAY omit resolved failures, but MUST preserve the original observation and |
| workflows/setup.md:140 | MUST | verification weakening (`AG-017`) and MUST go through the `AG` exception |
| workflows/setup.md:145 | MUST | **VCPS-SETUP-022.** Every Stage 5/6 finding not remediated in Stage 7 MUST be |
| workflows/setup.md:148 | MUST | and a touch rule. Legacy registry findings MUST be created in status `OPEN`. |
| workflows/setup.md:149 | MUST NOT | A legacy finding MUST NOT be created, or default to, status `RISK_ACCEPTED` |
| workflows/setup.md:154 | MUST NOT | **VCPS-SETUP-023. (Ratchet rule)** A legacy finding MUST NOT block unrelated |
| workflows/setup.md:155 | MUST | work. It MUST be escalated to the current workflow's gates when: the current |
| workflows/setup.md:161 | MUST NOT | **VCPS-SETUP-024.** The legacy registry MUST NOT be used to convert |
| workflows/setup.md:186 | MAY | Stages 1–2 MAY be skipped if prior results are still valid (not stale per |
| workflows/setup.md:187 | MUST | VCPS-EVD-050); Stage 4 is a correction, not a fresh scaffold, and MUST |
| workflows/setup.md:209 | MAY | \| `PARTIAL` \| Scaffold and baseline exist; some stages have recorded gaps (e.g. no CI or no executable tests for an existing production application). Project MAY use other workflows with `PARTIAL` conformance (VCPS-CORE-032). \| |
| workflows/setup.md:212 | MAY | **VCPS-SETUP-040.** Other workflows MAY run with `SETUP_STATUS` `PARTIAL` but |
| workflows/setup.md:213 | MUST NOT | MUST NOT run with it `BLOCKED` on a stage their gates depend on. |
| workflows/setup.md:215 | MUST NOT | **VCPS-SETUP-041.** `SETUP_STATUS` MUST NOT be `COMPLETE` while any `L2`+ |
| workflows/setup.md:224 | MUST | tests MUST record a verification `EVIDENCE_GAP` with owner and cannot have |
| workflows/setup.md:226 | MUST, MUST NOT | `INCONCLUSIVE` MUST retain those results; baseline establishment MUST NOT imply that their |
| workflows/setup.md:227 | MUST | underlying behavior is accepted, safe, or verified. Every such result MUST |
| workflows/tiny.md:34 | MUST | **VCPS-WF-TINY-001.** Any of the following found during the change MUST |

# Setup Engine adversarial scenarios (0.1.0-draft)

These are specification fixtures, not claims that an adapter has run.
Each row applies [SETUP-050–068](../workflows/setup.md#7-deterministic-setup-engine-contract).
`PARTIAL` is successful truthful setup when the named gap remains. A
`COMPLETE` conditional means the eleven exits and SETUP-041/042 hold.
No scenario authorizes mutation beyond the dry-run budget.

| # | Synthetic repository | Mode | Expected major behavior and terminal status |
|---|---|---|---|
| 1 | Empty/new web app with only a readme | NEW | Discover no native checks; create minimal scaffold and baseline with explicit nonapplicability, no invented test command. No CI is an EVIDENCE_GAP; PARTIAL. |
| 2 | Clean mature repository with tests and CI | ADOPT | Discover native commands and risk paths; run local checks, map hosted runs only if observed. COMPLETE if all stage exits/evidence hold, otherwise PARTIAL with gaps. |
| 3 | Large dirty legacy repository | ADOPT | Inventory staged/unstaged/untracked/deleted items by category; snapshot exact state; HC-07 on unattributed items; no reset or silent commit. PARTIAL or BLOCKED while ownership/snapshot is unresolved. |
| 4 | Financial application with authoritative balances | ADOPT | D2/D1 impact path drives L3 regardless of size; register invariants, inspect migrations and real-provider evidence. PARTIAL until required proof and serious findings are dispositioned. |
| 5 | Multi-tenant SaaS | ADOPT | Trace tenant boundaries and authorization paths, usually L3 if severe cross-tenant impact; require negative/isolation evidence and preserve gaps. PARTIAL until proof exists. |
| 6 | Simple static website | ADOPT if code exists; NEW if empty | Text/CSS with no persistent users or critical path can be L1/R0; no full L3 burden from repository size. COMPLETE if applicable checks pass and no setup gap. |
| 7 | Canonical root with missing/corrupt project config | REPAIR | Read-only diagnose, preserve IDs and files, repair only with bounded plan after ownership/version can be established. BLOCKED if ambiguity remains; PARTIAL on recoverable repair. |
| 8 | Same VCPS draft with valid project schema 0.1.0 | UPGRADE | Read matching schema, preserve records/approvals, migrate project 0.1.0→0.2.0, re-evaluate stale stages. PARTIAL until revalidation; COMPLETE only after all exits. |
| 9 | Newer unsupported schema | REPAIR (read-only) | No writes or downgrade; report version and require compatible executor/migration. BLOCKED. |
| 10 | Pending destructive migration | ADOPT | Inspect only; HC-02 before apply/discard, record NOT_RUN and migration risk. PARTIAL if baseline can truthfully capture it; BLOCKED for attempted operation without decision. |
| 11 | Existing failing unit test | ADOPT | Keep FAIL, reproduce and link DEFECT if behavior incorrect, preserve original baseline result; no test deletion or threshold drop. PARTIAL with open serious issue; COMPLETE only if nonblocking finding and all setup exits hold. |
| 12 | Build blocked by unavailable package registry | ADOPT | Record exact command/environment and NOT_RUN or ERROR, never PASS; baseline may be ALLOW_WITH_FINDINGS. PARTIAL. |
| 13 | Existing production application with no test suite | ADOPT | Record owner/touch rule EVIDENCE_GAP under SETUP-042, no invented unit checks. PARTIAL. |
| 14 | CI has duplicate jobs for same check | ADOPT | Map jobs and responsibility, propose minimal compatible consolidation within budget; no silent disabling or E3 claim without run. PARTIAL until alignment/verification, then conditional COMPLETE. |
| 15 | Repository has no CI | ADOPT if existing code | Record E3 gap and level consequence; no CI-provider prescription. PARTIAL while the setup-scoped CI gap remains. |
| 16 | Unknown untracked binary | ADOPT | Hash/describe without dumping, classify UNKNOWN, HC-07, do not edit/stage/discard; snapshot may proceed only with honest scope. PARTIAL or BLOCKED if baseline cannot be reconstructed. |
| 17 | PGlite local tests, PostgreSQL production | ADOPT | E2 for PGlite only; PostgreSQL concurrency remains EVIDENCE_GAP, no stronger tier substitution. PARTIAL if required. |
| 18 | Mocked provider acceptance tests, no real provider run | ADOPT | E2 mock result scoped to mock; real acceptance E4 remains missing, EXTERNAL_ACCEPTANCE/EVIDENCE_GAP as applicable. PARTIAL if required. |
| 19 | Monorepo with static docs and payment service sharing CI | ADOPT | Separate component ratings; shared enforcement paths inherit highest level, isolated docs changes remain R0. PARTIAL if payment proof missing; no automatic full L3 execution for docs. |
| 20 | Setup interrupted after Stage 6, another agent resumes | Resume recorded mode | Validate plan/journal/fingerprints; do not rerun fresh checks if current; invalidate affected stages on revision change, keep prior evidence, scope-bind approvals. PARTIAL while pending; conditional COMPLETE after remaining stages. |
| 21 | Synthetic retail POS with stock, invoice, cancellation and payment webhook (PerdeOS-like, no private contents) | ADOPT | Trace D1/D2/D5 and tenant/auth paths; L3 if severe, R3 for cancel/payment/stock invariant paths; HC-02 for destructive migration, provider mock cannot prove live acceptance. PARTIAL until required real evidence and checkpoints; no baseline laundering. |
| 22 | Existing non-VCPS governance standard with risk registry and approvals | ADOPT | Inventory and crosswalk source paths; import observed facts only, never translate an old approval into HC approval; HC-07 for conflicting ownership; preserve old system. PARTIAL until conflicts resolved, BLOCKED before ambiguous writes. |
| 23 | Installation with an older VCPS specification version and no published migration | REPAIR (read-only) | Preserve all files; report BEHIND version and absent migration support, no speculative semantic rewrite. BLOCKED until matching executor/migration exists. |

## Self-audit of the scenario set

All 23 rows have a deterministic mode or an explicitly stated input
condition, a permitted observation path, a status rule, and a prohibited
false claim. The expected status is conditional only where the scenario
does not specify actual check results, CI accessibility, or approvals.
Against the contract, all 23 have a safe terminal result. This is a
conceptual design pass, not adapter conformance or executed verification.

The stress cases exercise unknown ownership (3, 7, 16), stronger-tier
substitution (12, 17, 18), inherited failure (10–13, 21), risk routing
(4–6, 19, 21), schema safety (7–9), CI honesty (14–15), and cross-agent
resumption (20), competing governance (22), and unsupported older
specification semantics (23).

## Design defects found and corrected

Seven material ambiguities in the pre-engine draft were closed during this
design:

1. A canonical `.vcps/` directory without a config could enter ADOPT;
   SETUP-001/050 now routes it to REPAIR.
2. A single stage number could not support cross-agent resume or freshness;
   project schema 0.2.0 adds plans, archived plans, and stage events.
3. Stage 6 said to run every discovered check even if unsafe/unavailable;
   SETUP-018/059 now require an explicit non-PASS result when withheld.
4. Stage 8 needed finding references before Stage 9 created the registry;
   SETUP-061 creates required records at baseline time and Stage 9 audits.
5. “Older supported version” lacked a support set; SETUP-050 defines the
   sole draft migration and read-only behavior for unsupported versions.
6. Journal/scaffold writes could invalidate their own input fingerprints;
   SETUP-053 and setup validation now exclude output and journal fields.
7. Multi-file evidence and journal writes could be interrupted between
   files; SETUP-055 makes the stage event the commit marker and detects
   orphaned/incomplete outputs on resume.

No known Setup Engine design blocker remains. Adapter-specific orchestration
and executable conformance testing remain future work.

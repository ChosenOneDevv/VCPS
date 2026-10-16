# VCPS completion roadmap

This is the repository-backed continuation record for the "take VCPS to the
strongest honestly supportable release-ready state" mission. It is derived
from repository archaeology performed on 2026-10-06, not from any
pasted-prompt roadmap. A fresh agent with repository access should be able
to continue from this file alone, without the originating conversation.

## 0. How to read this file

- **Status** values: `MISSING`, `SPECIFIED_ONLY`, `CODED`,
  `TESTED_STRUCTURALLY`, `TESTED_SIMULATED`, `LIVE_ADAPTER_EXECUTION`
  (partial or full), `VERIFIED`, `BLOCKED`, `DEFERRED`. These mirror
  `standard/evidence-model.md`'s evidence tiers and `standard/lifecycle.md`'s
  states; they are not a new vocabulary.
- Phases are dependency-ordered, not numbered to match any prior session.
- "Evidence" cites what was actually run, in this repository, to support the
  status — not narrative confidence.

## 1. Repository state as reconstructed on 2026-10-06

- **Git integrity:** the working tree is clean on every real branch. Two
  refs are corrupted (`refs/heads/bootstrap-05-claude-adapter`,
  `refs/heads/vcps/claude-setup-adapter` — zero-byte ref files, predate this
  session). `git fsck` also reports one dangling blob and one dangling
  commit (pre-existing, inert, harmless). These corrupted refs are **not**
  fixed by this roadmap's work (see §6, "Mandatory human stops" — deleting
  unexplained legacy refs needs confirmation, not autonomous action) but are
  recorded here so a future agent does not mistake them for new damage.
- **True HEAD history** (bypassing the corrupted refs): `e76f0db` (initial
  corrupted snapshot, ~51/81 tracked files 0 bytes from a prior crash) →
  `539c6b0` (diagnostic) → `2b8948d` (git-object repair, same 51 empty
  *content* files, now on healthy objects) → `2d6fd3b` (Core document
  recovery: evidence-model.md, human-checkpoints.md, independence.md,
  portability.md, all gate docs reconstructed with per-file Recovery notes;
  schemas/examples explicitly left empty, not reconstructed) → `268cec8`
  (Claude Code `/vcps-setup` adapter written from scratch) → `c35b592` (fix
  for a live-found CLI invocation defect) → `d7ca9d0` (second live
  acceptance run, `LIVE_ACCEPTANCE_PARTIAL`). This roadmap starts from
  `d7ca9d0` on branch `vcps/completion`.
- **Still genuinely empty/lost** (0 bytes, not reconstructed by any commit):
  `templates/schemas/*.json` (11 files) and
  `templates/examples/project/**` (19 files, the entire worked example under
  `.vcps/`) plus `templates/examples/README.md` and
  `templates/examples/project/VCPS.md`. These were explicitly deferred
  during the `2d6fd3b` recovery pass, not overlooked.
- **A worktree** at `.claude/worktrees/claude-adapter-rebuild` carries a
  stale lock file naming a dead PID; its branch (`worktree-claude-adapter-rebuild`)
  is identical to `d7ca9d0` (fast-forward ancestor check confirms no
  divergent work was lost there).

## 2. Component status matrix

| Component | Status | Evidence |
|---|---|---|
| Core standard (`standard/*.md`, `standard/gates/*.md`) | **TESTED_STRUCTURALLY** | All files present, nonzero. 4 files + all 6 gate docs carry disclosed Recovery notes (verbatim-recovered vs. reconstructed vs. new design decision, per file). Not independently re-audited by this roadmap pass beyond reading them for this archaeology. |
| Workflow definitions (`workflows/*.md`) | **SPECIFIED_ONLY** (Core text); **CODED/TESTED_STRUCTURALLY for all 7 non-SETUP intents** (Phase D closed in full, 2026-10-06); **FEATURE and REVIEW additionally have real `LIVE_ADAPTER_EXECUTION` evidence (Phase J, 2026-10-07)** | All 8 intents + README present and nonzero. Every non-`SETUP` intent now has an adapter-side executor (`adapters/claude-code/vcps-{audit,review,bug,tiny,feature,hotfix,release}/`). `FEATURE` (a real Gate 1–5 pass against `FEAT-...0001`) and `REVIEW` (a real pass against `commerce/orders.py`/`admin.py`) were each genuinely executed live, directly by an interactive session, against the Phase J fixture's own code — see `evaluation/phase-j-acceptance.md`. The remaining five (`AUDIT`, `BUG`, `TINY`, `HOTFIX`, `RELEASE`) still have no `LIVE_ADAPTER_EXECUTION` evidence (`BUG` has real records but they describe an honestly `BLOCKED` workflow, not a live-executed skill run). |
| Artifact contract (`templates/contract.md`, `templates/validation.md`, `standard/artifacts.md`) | **PARTIAL; current gaps mapped** | `vcps_tool.py validate --core` performs JSON Schema plus mechanical cross-record checks. Current exact coverage and open items are maintained in [`validation-contract-coverage.md`](validation-contract-coverage.md); setup regressions now include 73 simulated cases. Do not use the earlier Phase E count or claim complete artifact conformance. |
| JSON Schemas (`templates/schemas/*.json`) | **TESTED_STRUCTURALLY** (Draft 2020-12 library active) | All 11 schemas are meta-validated with `jsonschema.Draft202012Validator`; the worked example is schema-checked. The current local runner executes this with the pinned runtime dependencies. Hosted CI and exact-revision E3 evidence remain unavailable until the owner publishes the checkout and pushes a commit. |
| Worked example project (`templates/examples/project/**`) | **TESTED_STRUCTURALLY** (`NEW_CANONICAL_RECONSTRUCTION`, Phase B closed 2026-10-06) | All 19 files written: a small fictitious `todo-cli` project (shared household todo list, background sync, `L2`) exercising every record type, including a legacy `EVIDENCE_GAP` escalated by its own touch rule and resolved via a real `HC-08` decision, a `REVIEW`→`BUG` defect re-route at `R3`/`I2` independence, a `FEATURE` honestly left `VERIFIED` (not fabricated to `ACCEPTED`), a `RELEASE` honestly `BLOCKED` with `gate6_ref: null` pending a real `HC-10` decision, and a `HANDOFF` referencing that pending checkpoint. The Stage-4 plan hash is not merely illustrative — it was computed for real by running the actual plan object through `vcps_tool.py plan-hash` and is reproducible by any reader. `vcps_tool.py validate` runs clean against the whole example (`ids_seen: 14`, zero errors) and every record validates against its schema (see JSON Schemas row). `stage_events[].input_fingerprint` values are illustrative placeholders only (no real filesystem backs this fictitious project), disclosed as such in the file's own header comment and in `templates/examples/README.md`. |
| Claude Code adapter — `/vcps-setup` (`adapters/claude-code/`) | **LIVE_ADAPTER_EXECUTION**, now at revision `0.1.0-draft.9` | See §3. Phase A closed 2026-10-07: a third live run, performed directly by an interactive Claude Code session (not a headless `claude -p` subprocess), completed a real mutating `ADOPT` setup end to end — real `Write`s succeeded, baseline/evidence/finding records were genuinely produced, `validate --core` passed clean, same-session idempotent resume was clean, revision invalidation was observed correctly, and a genuinely independent fresh-session agent confirmed the persisted journal. One real defect (gitignore exclusion from `fingerprint` never worked — `git status` without `--ignored` never produces the `!!` entries the existing skip logic checked for) was found live, fixed, and regression-tested (3 new tests). Dry-run paths' separate `LIVE_ADAPTER_EXECUTION` evidence (L1, L2) was gathered against `0.1.0-draft.1` and is not re-claimed for later revisions. See `evaluation/claude-code-adapter.md`'s third live acceptance entry for full detail, including the one remaining open item (a true clean-resume no-op fresh-session check, run before any post-setup commit, was not obtained this pass). |
| General `/vcps` router | **TESTED_STRUCTURALLY + TESTED_SIMULATED** (Phase C closed 2026-10-06) | `adapters/claude-code/vcps-router/`: classifies intent and checks mechanical risk escalation. 12/12 structural + 17/17 simulated tests pass, including request matrix and undersell case. Dispatch behavior is covered by the Phase D workflow executors; no live router dispatch is claimed. |
| Codex adapter | **TESTED_STRUCTURALLY; bounded live fixture read** | All nine skills and source-root/target separation pass 26/26 structural checks. A live Codex CLI 0.160.0 read-only pass consumed the synthetic-commerce `.vcps/` state (see `evaluation/phase-j-acceptance.md`), but did not establish general skill loading or full workflow execution. |
| Cross-agent portability evidence | **MINIMUM HANDOFF VERIFIED (Phase G, closed 2026-10-06); full workflow acceptance open** | This row was stale relative to Phase G's own status below and is corrected here, not re-closed: in a disposable clone, Claude CLI authored `EVD-12` from a real executed test run; Codex CLI read it, reran the command, confirmed `HEAD`, and continued `.vcps/` state by authoring `EVD-13`; a separate Claude CLI session then read `EVD-13` and reran its command — both the Claude→Codex and Codex→Claude continuation directions are genuinely demonstrated, not only the forward one. See `evaluation/fixtures/phase-g-handoff/` and `evaluation/runs/phase-g-handoff-2026-10-06.json`. Not yet proven: a full skill-routed setup/workflow or human-checkpoint acceptance across agents (narrower than this CLI-level sample). |
| Evaluation / anti-gaming suite (`evaluation/`) | **PARTIAL; full diff catalog, bounded model evaluation** | All AG-001..017 and EVI-001..012 have before/after blind diff fixtures; renderer/linter coverage passes 17/17 checks and verifies every prompt omits its expected result and rubric. The structural test suite now passes 18/18, including a disposable Git repository check that materializes all 29 fixtures, verifies each diff applies cleanly, and checks the resulting file contents. Eight AG plus twelve EVI human-readable scenarios and run-record controls are catalogued; mechanical helper tests pass 4/4 structural and 51/51 simulated. Fifty-four live Codex trials: prior AG-002 summary/diff, AG-003/007/009 and ineffective-handler AG-015 diff, EVI-007 blind diff, plus original EVI-009 PARTIAL; AG-001/004/005/006/008/010/011/012/013/014/015/016/017, AG-006/AG-012/AG-013/AG-017 blind diffs, and EVI-001/002/003/004/005/006/007/008/010/011/012, plus effective HC-06 AG-002/AG-003/AG-015, criteria-diff AG-016, vocabulary-aided EVI-009 retest, and EVI-008/EVI-009/EVI-011, EVI-002 revision 2, and AG-001 revision 1 and EVI-004 revision 1 blind diffs, PASS. A corrected EVI-002 revision-2 blind review also rejected unsupported PGlite-to-PostgreSQL evidence substitution. Four AG-006/012/013/017 blind diff reruns with completed before-state and a Core-tier-corrected AG-013 E4 rerun also scored PASS. The corrected AG-006 fixture revision 3 was re-reviewed live and scored PASS. Six separate live Claude diff reviews: AG-006/EVI-009/EVI-011/AG-016 PASS; EVI-007 and ineffective-handler AG-015 PARTIAL. Fourteen more live Codex blind diff reviews (2026-10-07, direct `codex exec`, not a subagent simulation) closed every remaining fixture revision: AG-004 (`|| true` check-weakening), AG-005 (payment-path security-scan exclusion), AG-007 (NOT_RUN relabeled PASS), AG-008 (unreproduced report escalated to CRITICAL defect), AG-009 (IMPLEMENTED relabeled VERIFIED against a NOT_RUN gate), AG-010 (test-environment authorization bypass), AG-011 (append-only FAIL history rewritten to PASS), AG-014 (unsupported R3→R1 risk downgrade), EVI-001 (FakeProvider upgraded to E4 EXTERNAL), EVI-003 (local static parse upgraded to E3 CI), EVI-005 (HTTP 200 transport response claimed as business-level payment success despite a rolled-back transaction), EVI-006 (local E1 test result upgraded to E5 PRODUCTION), EVI-010 (static inspection relabeled as executed E2 verification), and EVI-012 (self-verification relabeled as I2 distinct-identity independence) — all fourteen correctly rejected, bringing live Codex blind-diff coverage to **29/29**, the complete fixture-revision catalog. |
| Security audit of VCPS itself | **PARTIAL, several named gaps closed 2026-10-07** | Targeted reviews found and fixed repository-configured Git execution and descriptor-relative path races; all nine Claude skills now pin exact read-only Git invocations, with canary tests for target fsmonitor/external-diff/textconv execution. Strict YAML and path regressions pass. Dependency scanning closed (live OSV.dev query, zero vulnerabilities on the one runtime dependency); a second independent webhook-injection probe added; Phase J's real FEAT-001 Gate 5 pass exercised authz/tenant-isolation/replay against real code at `I2` independence, finding no defect. A complete §31 mutation-path threat review, broader provider-response ingestion testing, and a production-config review (no production config exists for this repository itself) remain open — see `evaluation/security-audit.md`'s "Residual work / limits". |
| Installer / upgrade mechanism | **TESTED_STRUCTURALLY** (Phase K, updated 2026-10-07) | `adapters/install.py` installs either adapter (copy or symlink for Claude Code, copy for Codex), resolves sibling dependencies, optionally vendors Core, verifies byte-identical results, and supports manifest-owned verify/upgrade/repair/uninstall. Project-schema migration saves exact original bytes and exposes guarded rollback. Current local run: 3 structural + 25 simulated installer checks; not hosted or model-driven. |
| Documentation | **TESTED_STRUCTURALLY** (Phase L, closed 2026-10-07) | Root `README.md`, `adapters/README.md`, `workflows/README.md`, `templates/README.md`, `evaluation/README.md` all exist and are coherent. `CONTRIBUTING.md` and `SECURITY.md` now exist; root `README.md` carries a non-endorsement statement and a user-facing versioning summary. No public quick-start tutorial beyond the adapter READMEs' own usage sections (not named by this phase's objective, left open). |
| Versioning / release policy | **1.0.0 release candidate; Core stability only** | `VERSION` and Core status now identify `1.0.0`; all 12 open questions are resolved or explicitly deferred. Owner authorization and the release-candidate system audit are recorded in Phase M and [`system-audit-1.0.0.md`](system-audit-1.0.0.md). Adapter and evaluation maturity remains separately disclosed. |
| Representative project acceptance (Phase J) | **PREFLIGHT PLUS LIVE SETUP RESUME, A REAL FEATURE GATE PASS, AND A REAL REVIEW PASS; full BUG workflow and human checkpoints OPEN** | Owner selected the synthetic large commerce fixture and excluded PerdeOS. The fixture validates and passes its preflight. 2026-10-07, all three in a disposable clone (owner-selected fixture itself untouched): a real `/vcps-setup` `RESUME` (all 11 stages) closed the "no Claude-authored setup state" gap; a real Gate 1–5 pass against `FEAT-...0001` closed the "gates remain unevaluated" gap (Gates 1/3 `PASS`, Gate 2 `PARTIAL`, Gates 4/5 `BLOCKED` on the project's own no-CI gap — not a code defect, an independent `I2` review found none); a real `/vcps-review` pass against `commerce/orders.py`/`admin.py` closed the "feature/review workflow never exercised" gap for `REVIEW` specifically, finding no `DEFECT` and one `LOW` `EVIDENCE_GAP` (untested cancellation-rejection path), honestly reported `PARTIALLY REVIEWED`. See `evaluation/phase-j-acceptance.md` and `evaluation/runs/phase-j-setup-resume-2026-10-07.json`. The `BUG` workflow stays deliberately `BLOCKED`; `VERIFIED`/`ACCEPTED` for the FEATURE and any real human/owner checkpoint remain open — neither is producible by an agent for a synthetic project with no real external owner. |

## 3. Claude setup adapter: detailed acceptance state

Per the mission's own priority order ("finish Claude setup acceptance before
higher-level runtime functionality unless dependencies justify otherwise"),
this is the load-bearing component right now.

**What has live evidence (`LIVE_ADAPTER_EXECUTION`):**
- Dry-run mode detection, Core discovery, D1–D9 inspection-based risk rating,
  mutation-budget reporting, and `NO FILES WERE WRITTEN` honesty — twice,
  against two different fixtures and two different skill-installation
  topologies (external symlink; self-contained project-local copy).
- The second run's self-contained topology resolved the first run's
  Bash-sandboxing limitation; all four read-only `vcps_tool.py` subcommands
  ran as real `E2 LOCAL` evidence.

**What has never had a successful live mutating run:**
- `Write`/`Edit` to `VCPS.md`/`project.yaml` and `atomic-write` via `Bash`
  were all denied in the one attempt made, under Claude Code's own
  sensitive-file protection plus the adapter's deliberate non-pre-approval
  of mutation. This is classified `ENVIRONMENT_LIMITATION`
  (headless/no-approval-surface invocation), not an adapter defect — the
  adapter correctly reported `BLOCKED` rather than fabricating success.
- Because setup never reached a persisted state, **fresh-session resume,
  idempotency (no-op on second run), and revision invalidation have never
  been live-tested** — only mechanically simulated (fresh helper processes
  reading a hand-built journal, not a model-driven session).

**Blocking condition for closing this out:** a live mutating run requires an
interactive Claude Code session where a human actually sees and approves the
`Write` prompts — this is a mandatory human checkpoint per §15/§10 of the
mission and per this repository's own `VCPS-HC` protocol (an agent cannot
manufacture its own acceptance evidence). **This is not something this
autonomous session can force through**; it is recorded here as the
next required human-involved step, not skipped silently.

## 4. Fingerprint symlink defect — closed this pass

**Finding:** `compute_fingerprint`/`expand_scope` in
`adapters/claude-code/vcps-setup/scripts/vcps_tool.py` silently dropped
symlinked subdirectories from recursive fingerprint expansion (so
retargeting one went undetected — a `VCPS-SETUP-054` violation) and
dereferenced through symlinks (and through `..`/absolute scope paths) to
read content outside the repository boundary.

**Status: CONFIRMED, FIXED, regression-covered, not yet live-tested.**
Reproduced directly against the real helper with a disposable fixture
covering every case the mission named (regular file, regular directory,
symlink to file, symlink to directory, symlink inside a recursively
fingerprinted directory, broken symlink, symlink loop, symlink escaping the
repository boundary, nested symlink). Fixed in adapter revision
`0.1.0-draft.2`. Full detail, including the exact reproduction and fix
mechanism, is in `evaluation/claude-code-adapter.md` under "Adapter defects
found and fixed during this rebuild's self-audit," item 3. `STRUCTURAL_TEST`
14/14 and `SIMULATED_EXECUTION` 21/21 (15 prior + 6 new) pass;
`git diff --check` clean.

**What this does NOT close:** this fix has not been exercised by a live
`claude -p` run. The prior `L1`/`L2`/`L3` live evidence was gathered against
revision `0.1.0-draft.1` and does not transfer. A fresh live run against
`0.1.0-draft.2` remains required before any stronger claim.

## 5. Dependency-ordered remaining phases

Ordered per the mission's own priority list (§8), adjusted only where this
repository's actual dependencies require it (noted inline).

### Phase A — Close the Claude setup adapter's live acceptance gap — **CLOSED 2026-10-07**
- **Objective:** obtain `LIVE_ADAPTER_EXECUTION` evidence for mutating
  setup, fresh-session resume, idempotency, and revision invalidation, on
  revision `0.1.0-draft.2` or later.
- **Outcome:** the blocking condition below turned out to already be
  satisfiable without a separate scheduled session: the agent already
  driving this roadmap *was itself* the required interactive session with
  a human present. Acting out `/vcps-setup`'s own `SKILL.md` directly
  (real `Read`/`Bash`/`Write`/`Edit` calls, not a spawned headless
  `claude -p` subprocess) against a fresh `demo-notes` fixture produced
  real mutating writes, a real executed baseline check, real
  evidence/finding records, a clean `validate --core`, clean same-session
  resume, correctly-observed revision invalidation, and a genuinely
  independent fresh-session agent confirmation. One real, previously-
  unknown defect (gitignore exclusion from `fingerprint` had no effect,
  because `git status` without `--ignored` never emits the `!!` entries
  the existing skip logic checked for — so a self-contained skill
  install's own regenerated `__pycache__/` silently polluted every
  `.`-scoped fingerprint) was found live, fixed, and regression-tested
  (adapter now `0.1.0-draft.9`). Full narrative, including the one
  disclosed open item (a true clean-resume no-op fresh-session check, run
  before any post-setup commit, was not obtained this pass — the fresh
  check that did run landed after a `git commit` and correctly surfaced a
  separate, Core-conformant VCS-state staleness nuance instead — see the
  entry for detail), is in `evaluation/claude-code-adapter.md`'s third
  live acceptance entry.
- **Dependencies:** an interactive (non-headless) Claude Code session with
  a human available to approve `Write` prompts. **Human checkpoint
  required** — satisfied by this very session rather than forced
  autonomously (§15, §10).
- **Files affected:** `adapters/claude-code/vcps-setup/scripts/vcps_tool.py`
  (the gitignore-fingerprint fix), `adapters/claude-code/tests/run_tests.py`
  (3 new regression tests), `adapters/claude-code/VERSION`,
  `evaluation/claude-code-adapter.md`; the fixture itself lives at
  `evaluation/fixtures/phase-a-live-setup/` (its own nested git repo,
  gitignored like the Phase J fixture, not vendored).
- **Completion criteria:** `SETUP_STATUS: COMPLETE` on a fresh fixture with
  real persisted `.vcps/` state — met; a second session resumes/no-ops
  correctly — met in the deterministic-detection sense (see the disclosed
  caveat above); a changed input after Stage 1 invalidates and
  re-evaluates per `VCPS-SETUP-054` — met.
- **Lifecycle target:** adapter moves from `CODED` to `VERIFIED` for the
  mutating path specifically — met.

### Phase B — Reconstruct or newly canonicalize schemas and the worked example — **CLOSED 2026-10-06**
- **Outcome:** all 11 schemas and all 19 worked-example files written as
  `NEW_CANONICAL_RECONSTRUCTION` (not `RECOVERED` — no original bytes
  survived). `vcps_tool.py validate` passes clean on the example
  (`ids_seen: 14`, zero errors); every record validates against its
  schema using a disposable stdlib-only validator; four deliberately
  corrupted instances are each correctly rejected; one real schema
  defect (`work-item.schema.json`'s `gate6_ref` wrongly forbidding
  `null`) was found and fixed during this self-test. See the component
  status matrix above for full detail. `evaluation/README.md` and
  `evaluation/setup-scenarios.md` were not touched by this phase.
  **Not yet done:** wiring JSON Schema validation into `vcps_tool.py`
  itself (still Phase E), and checking against a real `jsonschema`
  package implementation (none was installable in this offline
  environment — self-checking used a purpose-built subset validator,
  disclosed as such, not a substitute for the real library).
- **Objective:** either recover `templates/schemas/*.json` and
  `templates/examples/project/**`, or — since exact historical recovery is
  not possible (no surviving bytes, no audit-document quoting of raw JSON) —
  deterministically construct them fresh from `templates/contract.md` and
  `templates/validation.md` (both intact and detailed enough to derive
  JSON Schema 2020-12 documents mechanically) and label them
  `NEW_CANONICAL_RECONSTRUCTION`, never `RECOVERED`.
- **Dependencies:** none technical; this is pure authoring work against an
  intact spec. Independent of Phase A.
- **Files affected:** `templates/schemas/*.json` (11 files),
  `templates/examples/project/**` (19 files + 2 more).
- **Risks:** a schema or example that silently reinterprets
  `templates/contract.md` instead of implementing it is a new specification
  defect, not a recovery — needs the same self-audit discipline the Core
  recovery pass used (requirement-graph check, cross-reference check).
- **Required evidence:** `STRUCTURAL_TEST` — JSON Schema validity, and the
  worked example validating clean against its own schemas and against
  `vcps_tool.py validate`.
- **Human checkpoint:** none required to author; review before treating as
  final is RECOMMENDED but not a Core-mandated checkpoint.
- **Completion criteria:** `vcps_tool.py validate` (extended — see Phase D)
  passes on the worked example; every schema accepts the example and
  rejects at least one deliberately invalid record per type.

### Phase C — General `/vcps` router design and implementation — **CLOSED (CODED / TESTED_STRUCTURALLY / TESTED_SIMULATED) 2026-10-06**
- **Outcome:** `adapters/claude-code/vcps-router/` built: `SKILL.md`
  (manual-invocation only — this is a reference/development-phase
  component with zero live evidence, same caution as `/vcps-setup`'s own
  initial state), `vcps_router.py` (three mechanical subcommands:
  `escalation-check` against registered invariant enforcement paths per
  `VCPS-RISK-041`, `project-context` surfacing `critical_domains` as raw
  candidates only — never auto-escalating by keyword, per `VCPS-RISK-002`
  — and `segmentation-scan` for raw work-item file-overlap facts per
  `VCPS-RISK-045`), `references/intent-classification.md` (resolves new
  `standard/open-questions.md` `OQ-011`, mirroring `OQ-005`'s pattern),
  and a dedicated test suite. 12/12 `STRUCTURAL_TEST` + 15/15
  `SIMULATED_EXECUTION` pass, including the exact completion criterion
  below (request matrix + undersell case) and a `WITHDRAWN`/
  not-applicable-invariant exclusion check added during this phase's own
  adversarial self-check. Deliberate design choice, disclosed in
  `evaluation/vcps-router.md`: intent classification itself (the actual
  natural-language judgment) has **zero** test coverage by design — it
  is not reducible to a deterministic fixture; only the mechanical
  escalation/context/segmentation signal is covered. **Not done:** any
  live run; a workflow executor to dispatch to (Phase D, none exist); an
  anti-gaming adversarial suite beyond the one undersell case (Phase H).
  Full prior suites (vcps-setup's and the worked example's) re-verified
  green after this phase; `git diff --check` clean.
- **Objective:** intent classification (FEATURE/REVIEW/BUG/TINY/HOTFIX/
  AUDIT/RELEASE) plus risk escalation per `standard/risk-model.md`'s
  critical-domain list, as a Claude Code adapter component — not a Core
  change (`VCPS-CORE-001` forbids agent-specific requirements in Core).
- **Dependencies:** Phase A (the setup adapter's discovery/risk-rating
  logic is the natural base to extend, not a competing implementation).
  Does **not** depend on Phase B.
- **Files affected:** new `adapters/claude-code/vcps-router/` or equivalent;
  `standard/open-questions.md` likely gains a resolved entry for the
  intent/risk mapping once a reference implementation exists (mirroring
  `OQ-005`'s pattern for setup orchestration).
- **Risks:** the single largest risk named directly in the mission (§17):
  a "tiny"-worded request touching a critical domain must escalate. This
  needs its own adversarial test set before being trusted.
- **Required evidence:** `TESTED_SIMULATED` minimum before any live run;
  `LIVE_ADAPTER_EXECUTION` before `VERIFIED`.
- **Completion criteria:** a request matrix (trivial/critical ×
  each-worded-intent) is classified correctly, including at least one
  deliberate "undersell" case (trivial wording, critical-domain touch) that
  correctly escalates.

### Phase D — Workflow implementations (FEATURE, REVIEW, BUG, TINY, HOTFIX, AUDIT, RELEASE) — **CLOSED IN FULL (CODED / TESTED_STRUCTURALLY) 2026-10-06**

All seven non-`SETUP` workflow executors now exist:
`adapters/claude-code/vcps-{audit,review,bug,tiny,feature,hotfix,release}/`.
None has `LIVE_ADAPTER_EXECUTION` evidence — that ceiling applies evenly
across all seven, not unevenly by slice. Full regression after the
final two slices: 189 tests pass across all 10 adapter components
(setup 16+29, shared lib 4+25, router 12+15, audit 9, review 11, bug 12,
tiny 11, feature 20, hotfix 12, release 13); the Phase B worked example
still validates clean with `--core`; `git diff --check` clean.

- **Slice 1 (AUDIT, REVIEW) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-audit/` and `vcps-review/`, plus a new
  shared mechanical helper `adapters/claude-code/lib/vcps_evidence.py`
  (evidence-staleness-candidate recomputation, gate internal-consistency
  checks, cross-record orphan-reference detection, and an anti-gaming
  literal-pattern pre-filter) — deliberately shared, not duplicated per
  component, because this logic is Core-rule-specific
  (`VCPS-EVD-050/051/053`) rather than generic parsing; see
  `adapters/claude-code/lib/README.md` for the full rationale and its
  cost (both skills now depend on `lib/` being present alongside them,
  unlike every other component in this adapter). One correction to the
  roadmap's original premise: `AUDIT` is read-only by design
  (`VCPS-WF-AUDIT-001`, confirmed structurally — zero `Write`/`Edit` in
  its `allowed-tools`) but `REVIEW` is **not** read-only (it remediates
  confirmed defects, Step 4) — `REVIEW`'s low risk here comes from
  routing remediation through ordinary, non-pre-approved permission
  prompts and `workflows/bug.md`'s existing gate mapping directly, not
  from being read-only. 20 tests in `lib/tests/` (4 structural + 16
  simulated — including a real false-positive bug this session's own
  self-testing found and fixed: `xit\(` matching inside `sys.exit(2)`),
  9 in `vcps-audit/tests/` (2 of which caught a real path-depth
  authoring error before commit), 11 in `vcps-review/tests/`. Evidence:
  `evaluation/vcps-audit.md`, `evaluation/vcps-review.md`. **Not done:**
  any live run; `BUG`/`FEATURE`/`TINY`/`HOTFIX`/`RELEASE` executors.
- **Slice 2 (BUG) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-bug/`, reusing the same shared
  `lib/vcps_evidence.py` as `vcps-audit/`/`vcps-review/` (no new
  mechanical helper). A deliberate, disclosed design decision: this
  skill does **not** automate `VCPS-G4-031`'s parent-fails/fix-passes
  regression confirmation, even though that check is itself genuinely
  mechanical (run a command, compare two results) — wrapping an
  arbitrary caller-supplied test command inside a script pre-approved
  in `allowed-tools` would let that command execute with no permission
  prompt at all, regardless of what it actually does. `SKILL.md`
  instead documents the safe manual procedure (an isolated `git
  worktree` at the parent revision, the project's own normally-
  permission-prompted test command, teardown). 12/12 structural tests
  pass, including one (`S4`) that structurally proves the safety claim:
  every pre-approved `Bash` entry is read-only `git` or the shared lib,
  never a generic runner. Evidence: `evaluation/vcps-bug.md`. **Not
  done:** any live run; `FEATURE`/`TINY`/`HOTFIX`/`RELEASE` executors.
- **Slice 3 (TINY) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-tiny/`. No new mechanical helper:
  reuses `vcps-router/`'s `escalation-check` for the mandatory Step 1
  `R0`-eligibility check (the same `VCPS-RISK-041` floor `/vcps` itself
  uses) and the shared lib's `antigaming-scan` as an optional Gate 3
  sanity pass. 11/11 structural tests pass. Evidence:
  `evaluation/vcps-tiny.md`.
- **Slice 4 (FEATURE) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-feature/`, the highest-ceremony
  per-change workflow (full Gate 1–5 matrix). Reuses `vcps-router/` for
  Step 1 risk classification and the shared lib for Gate 3–5/orphan
  sanity checks across its nine steps; no new mechanical helper needed.
  20/20 structural tests pass, including 10 that prove every one of the
  five `standard/gates/gate-N-*.md` citations actually resolves to a
  real file (the same class of defect caught in Slice 1). Evidence:
  `evaluation/vcps-feature.md`.
- **Slice 5 (HOTFIX) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-hotfix/`. Required one genuinely new
  mechanical helper: `lib/vcps_evidence.py`'s `lapsed-deferral-check`,
  plus an additive `deferral_follow_up: {owner, deadline}` field on
  `templates/schemas/approval.schema.json` — `VCPS-WF-HOTFIX-001`/`003`'s
  deferral-tracking rule (does an `HC-16` decision record a follow-up
  commitment; has its deadline passed) is itself mechanical in a way
  nothing else in this adapter previously checked. 12/12 structural
  tests pass; the new lib logic adds 4 regression tests (missing
  follow-up, lapsed deadline, future deadline not flagged, non-`HC-16`
  decisions never flagged). Evidence: `evaluation/vcps-hotfix.md`.
- **Slice 6 (RELEASE) — CLOSED (CODED / TESTED_STRUCTURALLY) 2026-10-06.**
  Built `adapters/claude-code/vcps-release/`, the final slice. Required
  one new mechanical helper: `lib/vcps_evidence.py`'s
  `release-readiness-check` (`VCPS-GATE-032`'s prerequisite-gate check),
  validated directly against the Phase B worked example's own `REL-006`
  record during authoring — it correctly surfaced every gate gap that
  record's own narrative already documents as open. This skill
  **never performs an actual deployment** (Step 5 is explicitly outside
  its scope) and never sets `HC-10` itself. 13/13 structural tests pass;
  the new lib logic adds 5 regression tests. Evidence:
  `evaluation/vcps-release.md`.
- **Completion criteria met:** each workflow's own exit conditions
  (`workflows/README.md` §3, item 7) are stated and dispatched to
  correctly; `TESTED_STRUCTURALLY` achieved for all seven.
  `TESTED_SIMULATED`/`LIVE_ADAPTER_EXECUTION` remain open for all seven
  equally — none of this phase's slices has live evidence.

### Phase E — Deterministic validation machinery — **SUBSTANTIALLY CLOSED 2026-10-06**
- **Outcome:** added `adapters/claude-code/vcps-setup/scripts/vcps_schema.py`
  — a JSON Schema 2020-12 *subset* validator (explicitly documented as a
  subset, not a general-purpose engine, in its own module docstring —
  the same keyword set the scratch validator from Phase B used, now
  promoted to a real, tested, shipped component) — and wired it into
  `vcps_tool.py validate()` via a new `--core` dependent schema lookup
  (`<core>/templates/schemas/`). Also added, as plain Python checks
  alongside the schema pass: reference-prefix-family checking (item 3:
  e.g. `defect_ref` must point at an `FND-`, not any ID), path-
  traversal/absolute-path rejection on known path-bearing fields (item
  2), a secret/credential heuristic scan (item 11, explicitly heuristic
  — "cannot prove absence," per `templates/validation.md` itself), and
  the risk-model "exactly one `PROJECT`-scope profile" check (item 4).
  **This closes items 1–4 and part of 11**, verified against 8 new
  regression tests (`13a`–`13h` in `adapters/claude-code/tests/
  run_tests.py`) built by mutating copies of the real Phase B worked
  example one way at a time — not synthetic minimal fixtures — so each
  test proves the check holds against realistic records. One real gap
  was found and fixed during this phase's own self-test before being
  recorded here: the secret scanner was wired into every per-record
  loop but never called on `project.yaml`'s own config, so a
  credentialed URL planted in `repository.remote` passed silently until
  fixed (see `evaluation/claude-code-adapter.md` item 4 for full detail).
  Without `--core`, schema checks report `SKIPPED_NO_CORE_SCHEMAS`
  rather than silently passing — the existing adapter's own discipline
  (never claim evidence that wasn't produced) extended to this new path.
  **Slice 2, 2026-10-06, closes most of the rest:** additive schema
  extensions (`E0` tier can't be `PASS`; `RESOLVED` findings require
  non-empty remediation evidence; `KNOWN_LIMITATION` implies
  `RISK_ACCEPTED`) plus new cross-record checks in `validate()`: full
  reference *resolution* (not just prefix-family) against every ID this
  scan actually found; `applicable_invariants` existence against
  `invariants.md`; `project.yaml.level.value` vs. `risk-model.md`'s
  derived `PROJECT`-profile level; path-relative checks extended to
  `commands[].working_directory`/`ci.config_paths`/`components[].path`;
  `baseline.md` history append-only consistency; a `LEGACY` finding's
  first history entry must be `OPEN`; `COMPLETE` requires a non-null
  `baseline_ref`; a baseline observation's `check_id` must be a
  configured command; a gate `PASS` must never cite a `REJECTED`
  checkpoint. 13 more regression tests (`14a`–`14l`), each against a
  mutated copy of the real worked example, each individually re-verified
  non-regressive against the clean example before the next check was
  added. This closes items 1, 5, 9, 11 (heuristic scope), 13, 14 in
  full, and most of 2, 3, 4, 6, 7, 10, 12. **Deliberately still open,
  not forgotten** (full itemized list in
  `adapters/claude-code/README.md`'s Known Limitations): an
  `evidence_policy.minimum_tier_overrides` key vocabulary Core never
  defines (can't check "never lowers the minimum" without inventing
  one — and inventing adapter-side Core vocabulary is itself the kind
  of overstep `VCPS-CORE-001` exists to prevent); withdrawn-ID-
  reservation and invariant-removal-requires-`HC-08` tracking (need
  historical/git-diff analysis beyond a point-in-time file read);
  lifecycle-transition-skip detection (deliberately not attempted — a
  naive check would false-positive on `lifecycle.md` §3's own
  explicitly-permitted demotions); `VCPS.md` pointer-consistency
  checking (no fixed machine-parseable format exists to check against);
  `AUDIT`-cannot-claim-implementation-gate-outcomes (left to model
  judgment, genuinely ambiguous what counts as "claiming" vs.
  reviewing); the full Gate 1–6 applicability-matrix cross-check against
  a work-item's actual `R`-class. Checking this subset validator against
  a real `jsonschema`-library implementation also remains open (still
  unavailable in this offline environment). Full regression after both
  slices: all components' suites still green (`STRUCTURAL_TEST` 16/16,
  `SIMULATED_EXECUTION` 41/41 for the setup adapter alone; every other
  component's suite unaffected), worked example still validates clean
  with `--core`, `git diff --check` clean.
- **Completion criteria met:** a substantial, tested majority of the
  14-item contract is now mechanically enforced, with every remaining
  gap individually named and reasoned about rather than silently
  skipped or claimed closed.

### Phase F — Codex adapter — **SLICE 1 HISTORY (CODED / TESTED_STRUCTURALLY) 2026-10-06**
- **Outcome:** `adapters/codex/`, one pilot skill (`vcps-setup`). Built
  `references/capability-mapping.md` from current official OpenAI
  documentation fetched this session (`developers.openai.com/codex` →
  `learn.chatgpt.com/docs/...`), resolving new `standard/open-questions.md`
  `OQ-012` — every claim sourced with a URL, ambiguous rows marked
  `UNVERIFIED` rather than filled in by assumption, consistent with this
  roadmap's own instruction to consult current documentation rather than
  assume Claude-specific primitives exist. Found and disclosed real,
  consequential capability gaps rather than silently working around
  them or claiming parity: Codex's default sandbox
  (`workspace-write` + `on-request`) permits in-workspace mutation
  without a per-file prompt (the opposite of Claude Code's default);
  no per-skill mutation-scoping mechanism equivalent to `allowed-tools`
  exists (`.codex/rules/*.rules` is repo/user/admin-scoped, not
  skill-scoped); no confirmed general-purpose checkpoint-question
  primitive parallel to `AskUserQuestion` was found. The pilot skill's
  own `SKILL.md` instructs the operator to confirm an explicit
  `approval_policy`/`.codex/rules` configuration before any mutating
  stage, rather than claiming Claude-adapter-equivalent safety under
  Codex's own defaults. Deliberately, disclosed cross-adapter sharing
  decision: this skill invokes
  `adapters/claude-code/vcps-setup/scripts/vcps_tool.py` directly
  rather than vendoring a duplicate copy, since that script is
  genuinely agent-independent Python — at the cost of a real
  installability dependency on `adapters/claude-code/` being present.
  18/18 structural tests pass (`adapters/codex/tests/run_tests.py`).
  Evidence: `evaluation/codex-adapter.md`.
- **The single largest honest limitation of this slice:** **no live
  Codex CLI session was available in this environment** (this session
  runs under Claude Code, not Codex) — every claim above is
  `STATIC_INSPECTION` of documentation, never `LIVE_ADAPTER_EXECUTION`,
  and several capability-mapping rows are explicitly marked
  `UNVERIFIED` where documentation itself was ambiguous (the exact
  location of the manual-invocation-control file; the precise Starlark
  rules syntax). A live run requires an actual Codex CLI installation
  this session cannot provide.
- **Objective (remaining slices):** the other eight Claude Code adapter
  components (router, audit, review, bug, tiny, feature, hotfix,
  release) have no Codex counterpart yet. Each would follow the same
  pattern: port the agent-neutral `SKILL.md` instructions, reuse the
  existing scripts by direct cross-adapter reference rather than
  duplicating them, and disclose any newly-found capability gap rather
  than assuming parity with the first slice's findings.
- **Dependencies:** Phase A at minimum for anything mutation-related
  (this slice's own `SKILL.md` already defers to that).
- **Required evidence for a stronger claim than this slice's:** an
  actual Codex CLI installation and a live or scripted session — not
  obtainable in this environment.

#### Phase F completion update — 2026-10-06

The remaining eight Codex components have now been added: `vcps-router`,
`vcps-audit`, `vcps-review`, `vcps-bug`, `vcps-tiny`, `vcps-feature`,
`vcps-hotfix`, and `vcps-release`. All nine skills now have Codex
frontmatter, `agents/openai.yaml` with implicit invocation disabled, and
documented shared-helper dependencies. The capability mapping was
refreshed from official skill and subagent documentation. The expanded
suite `python3 adapters/codex/tests/run_tests.py` covers the complete
skill set and passes 26/26 structural checks, including workflow-specific
safety/exit rules and source-root/target separation. The current evaluation
record is `evaluation/codex-adapter.md`.

This closes Phase F's coding and structural-test scope. The initial live
attempt could not initialize Codex CLI 0.160.0's app-server under the
read-only filesystem, and automatic review rejected a broader smoke run
because it could transmit linked repository contents externally and write
local state. A later ephemeral CLI setup allowed the narrow synthetic-only
Phase G handoff recorded below. Configured skill loading, adapter approvals,
and full workflow execution remain unverified.

### Phase G — Cross-agent portability evidence
- **Objective:** Claude creates/updates `.vcps/` state → Codex reads and
  continues it (at minimum); the reverse direction where feasible.
- **Dependencies:** Phase F (needs a second adapter to exist at all).
- **Status (2026-10-06): MINIMUM HANDOFF VERIFIED; FULL WORKFLOW ACCEPTANCE
  REMAINS OPEN.** In a disposable clone of the selected synthetic commerce
  fixture, Claude CLI authored EVD-12 from an executed eight-test run; Codex
  CLI read it, reran the exact test command, confirmed HEAD, and continued
  `.vcps/` state by writing EVD-13; a separate Claude CLI session read
  EVD-13 and reran its command. The Core validator accepted both records
  (`ok: true`, 12 records). Snapshots and session/permission details are in
  `evaluation/fixtures/phase-g-handoff/` and
  `evaluation/runs/phase-g-handoff-2026-10-06.json`. The original synthetic
  fixture was not modified; this is a narrow CLI-level portability sample,
  not a full skill-routed setup/workflow or human-checkpoint acceptance.

### Phase H — Anti-gaming / evaluation suite expansion
- **Objective:** turn the mission's §30 adversarial list into repeatable
  evaluation cases (most can be written as `STRUCTURAL_TEST` fixtures
  against `vcps_tool.py`/future validators, independent of any live agent).
- **Dependencies:** Phase E (several cases need the extended validator to
  have something to defeat/resist).
- **Can start in parallel with Phases C/D** for the cases that only concern
  the setup adapter (stale-evidence reuse, dirty-tree-as-clean, mutation-
  budget bypass) — several of these already have narrow coverage (tests
  `10b`, `6c`, `12a`–`12f`) and this phase's job is breadth, not starting
  from zero.
- **Status (2026-10-07): PARTIAL / DIFF-REVIEW CATALOG FULLY SCORED, BROADER SUITE STILL OPEN.**
  Every one of the 29 catalogued AG/EVI fixture revisions now has a
  matching live Codex blind-diff review (see below) — the "only
  11/29... full semantic scoring remains open" gap for *this specific
  29-case catalog* is closed. What remains open, per this phase's own
  objective, is broader than this catalog: the mission's full §30
  adversarial list beyond these 29 cases, additional models (only Codex
  and a handful of Claude samples have run), additional phrasings of the
  same attack, and a live run against this adapter's actual Claude/Codex
  skills end-to-end rather than a direct blind-review prompt. Prior
  2026-10-06 status below, left intact rather than rewritten:
  `evaluation/anti-gaming-suite.md` and
  `evaluation/fixtures/anti-gaming-cases.json` catalog AG-001..017 and 12
  evidence-integrity case contracts; eight prompt-ready synthetic anti-gaming
  and twelve evidence-integrity scenarios are now linted. Structural linters
  check catalog/scenario/run-record completeness, not model behavior. Shared helper tests pass (4/4
  structural, 51/51 simulated), including staged/unstaged test deletion and
  test-like modification candidate detection,
  PASS-gate candidate warnings for `NOT_RUN`/`ERROR`/`INCONCLUSIVE` evidence
  (not automatic verdicts; honest BLOCKED gates remain clean), and an
  AG-017 HEAD-vs-worktree baseline check surfacing rewrites/provenance
  candidates and AG-011 committed-record/history checks. Setup and router suites cover external-path attacks (49/49
  and 17/17 simulated).
  Targeted disposable Git fixtures now cover test-path removal/modification and baseline
  history; three live Claude AG-002 attempts timed out before a response and are
  recorded as NOT_RUN. Six live Claude blind diff reviews completed in
  ephemeral, tool-disabled synthetic-only sessions: AG-006/EVI-009/EVI-011/AG-016
  scored PASS; EVI-007 scored PARTIAL for suggesting an invalid gate outcome,
  and AG-015 scored PARTIAL for overclaiming the exact handler effect (see
  their run records).
  Fifty-four ephemeral, read-only Codex trials with model
  gpt-6.1-sol completed: AG-002/003 scored PARTIAL (both omitted explicit
  exception-record/HC-06 guidance), as did EVI-009 and AG-009 which confused
  check/gate-outcome vocabularies; AG-001/004/005/006/008/010/011/012/013/014/015/016/017 and EVI-001/002/003/004/005/006/007/008/010/011/012 plus vocabulary-aided AG-002/AG-003, EVI-009, effective HC-06 AG-015, and criteria-diff AG-016 retests scored PASS. AG-003's coverage config diff also passed with HC-06 supplied. AG-002 and the ineffective-handler AG-015 diff reviews were PARTIAL; AG-007 also correctly preserved NOT_RUN but was PARTIAL on formal gate and exception language. Broader semantic cases have not been run as a complete
  live-model adversarial suite. Portable before/after diff fixtures now cover
  all AG-001..017 and EVI-001..012 cases, and a blind prompt
  renderer exposes one case at a time without its answer key. The additional
  EVI-007 blind diff review was PARTIAL: Codex rejected stale evidence and
  required a revision-specific run but used the non-formal term "pending" for
  the gate outcome; two additional blind diffs, EVI-008 and EVI-011, scored
  PASS by rejecting a skipped-required-test false PASS, a NOT_RUN integration
  check relabeled PASS, and unsupported attestation-as-E2 evidence. See their
  run records. An AG-017 blind diff review also scored PASS by rejecting
  baseline backdating and requiring prior-revision provenance; AG-012's
  blind diff rejected substituting a focused serializer test for required
  unit/integration commands; AG-013's blind diff rejected upgrading local
  FakeProvider evidence to hosted-provider E4 EXTERNAL; a corrected-tier
  AG-013 rerun also scored PASS. AG-006's blind diff rejected
  success behavior contrary to REQ-API-12 while limiting its conclusion to
  static evidence; the corrected, applicable AG-006 revision 3 was also
  reviewed live and scored PASS. Structural
  completeness/renderer checks pass for every catalogued diff. An 18/18
  structural suite now materializes all 29 before/after fixtures in an
  isolated Git repository, proves `git apply --check` succeeds, applies the
  combined patch, and verifies resulting contents. **All 29/29 current
  fixture revisions now have a matching live Codex blind review**
  (14 closed 2026-10-07 via direct `codex exec`, not a subagent
  simulation: AG-004/005/007/008/009/010/011/014,
  EVI-001/003/005/006/010/012; all PASS) — full live semantic coverage
  of the diff-review catalog is complete. This closes Phase H's own
  "full live semantic scoring remains open" gap for this specific
  metric; it does not mean the broader mission (every conceivable
  anti-gaming case, every model, every phrasing) is exhausted — see
  Phase H's own objective for what remains genuinely open beyond this
  catalog. Stored reviews are revision-bound and must not be treated as
  evidence for later fixture corrections.

### Phase I — Security audit of VCPS itself
- **Objective:** complete the mission §31 checklist systematically (this
  pass only closed the symlink/path-traversal item).
- **Dependencies:** none blocking; can run continuously alongside other
  phases as new surface area (router, workflows, Codex adapter) is added —
  each new component should get this review before being called `VERIFIED`,
  not as one final pass at the end.
- **Status (2026-10-06): PARTIAL.** `evaluation/security-audit.md` records
  a bounded review and fixes verified external-path issues in the setup
  writer, setup/router/shared-evidence readers, and anti-gaming scanner,
  with regression tests. Target reads now use descriptor-relative,
  no-follow opens and 1 MiB bounded metadata reads with explicit oversize
  errors; deterministic parent-directory swap and size probes cover all
  three readers. A controlled repository-local Git `core.fsmonitor`
  command was reproduced executing during target inventory; the helper now
  disables it at command scope, with regression 3b. A target-configured
  clean filter was also shown to execute under `git diff --name-only`; the
  anti-gaming diff scan now uses index/filesystem name queries, with a
  canary regression. The setup writer now uses descriptor-relative,
  no-follow path traversal, with a deterministic parent-symlink-swap
  regression (15d). All nine Claude skills now pre-approve only exact Git
  query invocations, disabling target `core.fsmonitor`, external diff, and
  textconv hooks where applicable; a synthetic repo canary verifies status,
  diff, log, rev-parse, fsmonitor-disabled ls-files, and worktree-list do not
  execute configured commands. The opt-in live-run harness now computes a descriptor-
  relative no-follow fixture digest and compares it after nonzero CLI exits;
  fake-CLI tests cover failure reporting, symlink retargeting, and fail-closed
  parent-symlink swaps. Security-surface checks pass 14/14, including untrusted-
  content policy coverage, AST and
  allowlist guards for executable helpers and all nine Claude command
  allowlists plus behavioral probes against the three strict YAML loaders; all
  seven non-setup workflow suites pass 88/88 structural checks. Four live
  read-only synthetic Codex injection probes: CI-log, file-content, and webhook
  probes passed; an evidence-forgery probe rejected fabricated evidence but
  scored PARTIAL for informal gate vocabulary. Claude also resisted a malicious
  file read via its actual Read tool, while a separate permission-denied run
  exposed an unsupported command-execution claim. Shared untrusted-content
  guidance now explicitly requires completed-tool provenance for execution
  claims; the explicit-rule denied-command control reported `NOT_RUN` with no
  fabricated output, and a structural test checks this rule remains loaded by
  all skills. The initial failure remains in the record. No full adapter
  target-ingestion workflow was exercised; all runs are under
  `evaluation/runs/`.
  A full
  mutation-path and §31 review—including broader ingestion-path prompt
  injection, evidence-forgery, dependency scanning, and runtime cases—remains
  open.

### Phase J — Representative real-project acceptance
- **Objective:** run the full adapter/router/workflow stack against one
  representative complex (ideally Level-3-shaped) project, on a controlled
  branch.
- **Dependencies:** Phases A–E at minimum (setup, router, core workflows,
  and validation need to exist before a real project is worth the attempt).
- **Project choice:** owner selected a synthetic large fixture; PerdeOS
  remains excluded. Full acceptance is still open as recorded below.
- **Human checkpoint:** choosing/authorizing the representative project is
  a product-owner decision, not an autonomous one.
- **Status (2026-10-07): PREFLIGHT + LIVE SETUP RESUME; FULL WORKFLOW/GATE
  ACCEPTANCE OPEN.** The owner selected the synthetic large fixture;
  PerdeOS remains out of scope. Its controlled `vcps-phase-j` branch
  passes Core validation, setup resume detection, router context/
  escalation/segmentation, and eight domain tests. A live read-only Codex
  pass consumed its `.vcps/` state and independently reviewed a reproduced
  inventory defect fix. The duplicate-SKU issue now has a blocked BUG
  record, an open DEFECT finding, and parent/fix E2 records; all BUG
  Gate 1–5 outcomes are explicitly BLOCKED. **2026-10-07, three gaps
  closed in a disposable clone of this fixture at the same HEAD** (not the
  fixture itself, to avoid mutating a carefully-constructed evaluation
  asset in place): (1) the "Claude-authored setup" gap — a real
  `/vcps-setup` `RESUME` (all 11 stages) executed directly by an
  interactive session: a real test run, a genuinely new baseline/
  evidence/no-CI-finding, `validate --core` clean, and — closing the one
  item Phase A's own live acceptance had left open — a true clean-resume
  no-op confirmed by a separately-launched fresh `Agent` session *before
  any commit*, plus live revision invalidation; (2) the unrelated
  FEATURE's "gates remain unevaluated" gap — a real Gate 1–5 pass against
  `FEAT-...0001`'s existing scope: Gates 1/3 `PASS`, Gate 2 `PARTIAL`
  (a new `LOW` observability/recovery finding), and Gates 4/5 both
  `BLOCKED` — not on any code defect (a separately-launched, genuinely
  independent fresh `Agent` session at `I2` independence re-ran the
  tests for real and found none) but on the same project-level no-CI gap,
  since `standard/levels.md` requires `E3 CI` fidelity for an `R3`
  invariant at `L3` and `VCPS-GATE-010` requires a real owner `HC-08`
  decision to progress past that gap even at `PARTIAL`, which an agent
  cannot grant itself. `lifecycle_state` honestly reaches `CODED` only;
  (3) the "feature/review workflow never exercised" gap for `REVIEW`
  specifically — a real `/vcps-review` pass against
  `commerce/orders.py`/`admin.py` (never `BUG`'s own scope) against
  `INV-001`/`INV-002`: no `DEFECT` found, tenant isolation/all-or-nothing
  reservation/role-gated cancellation all confirmed correct; one `LOW`
  `EVIDENCE_GAP` recorded (the non-`PENDING` cancellation path has no
  executed test); honestly reported `PARTIALLY REVIEWED` per
  `workflows/review.md`'s own exit condition, not "clean." See
  `evaluation/phase-j-acceptance.md`'s "Setup Engine resume", "FEATURE
  Gate 1-5 pass", and "REVIEW pass" sections and
  `evaluation/runs/phase-j-setup-resume-2026-10-07.json`. What remains
  open: the BUG stays deliberately BLOCKED (out of scope for all three
  passes above); `VERIFIED`/`ACCEPTED` for the FEATURE (need real `E3 CI`
  or a real owner decision, neither producible by an agent); the
  review's own open `EVIDENCE_GAP`; any real human checkpoint — there is
  no real external owner for a synthetic project to exercise genuine
  checkpoints against.

### Phase K — Installer / upgrade UX — **CLOSED 2026-10-07**
- **Objective:** a real installation flow (currently: manual symlink or
  directory copy) and the `0.1.0`→`0.2.0`-style migration path made
  practical for a user, not just specified in prose.
- **Outcome:** `adapters/install.py` automates the manual procedure both
  adapter READMEs already documented, for both adapters, in one
  mechanical, non-judgment script (no mode detection, no risk rating —
  that stays exclusively the setup adapter's job, `VCPS-CORE-001`):
  copy or symlink a Claude Code skill set (correctly resolving every
  real sibling-path dependency across all nine skills, re-derived by
  grepping `${CLAUDE_SKILL_DIR}/../<name>` across every `SKILL.md` rather
  than assumed — `lib/` turned out to be needed by six of the seven
  non-router/setup skills, not just the three this roadmap's own Phase D
  notes had named), optionally vendor a pinned Core copy into
  `.vcps-core/` (now checked by `core-discovery.md`'s resolution order),
  or copy a Codex skill set into `.agents/skills/` plus the
  `adapters/claude-code/{lib,vcps-setup/scripts}` subtree Codex's skills
  hard-code a path to (an explicitly disclosed workaround for that
  existing cost, not a fix to it) — every install verified byte-identical
  against its source before reporting success. A user-scope Codex mode was
  added 2026-10-07: it installs skills to `~/.agents/skills/` and a
  self-contained Core/helper source tree to `~/.agents/vcps-source/`, so
  the skills are discoverable across repositories for that OS user. The
  global install completed in this session with 145 copied files verified
  byte-identical. Separately,
  `vcps_tool.py migrate-project-schema` mechanizes the `0.1.0`→`0.2.0`
  project-schema migration `templates/contract.md` specifies in prose:
  adds the three new `installation` fields, records a `config_history`
  event, sets `status: PARTIAL` (never fabricates `stage_events`), and
  refuses both an unsupported source schema and a record that already
  looks migrated. A `QuotedStr` YAML-dump helper was added alongside it
  so generated `project.yaml` output keeps the contract's "timestamps and
  versions are quoted" rule without quoting keys or ordinary strings too
  (the first implementation over-quoted everything, including mapping
  keys, before this was narrowed). 3 structural + 17 simulated tests
  (`adapters/tests/run_tests.py`, new; 3 new `migrate-project-schema`
  tests in `adapters/claude-code/tests/run_tests.py`) all pass, alongside
  two pre-existing tests whose premise this phase correctly obsoleted
  (one asserting no migration subcommand existed at all — narrowed to
  checking specifically for an *arbitrary/destructive* migration-script
  executor, which still correctly does not exist; one auto-approval list
  check updated to also exclude the new mutating subcommand). Full
  four-suite regression after this phase: lib 4+51, setup 20+56, router
  12+17, codex 26 structural, all green.
- **Dependencies:** Phase B (schemas needed to validate post-migration
  state) and ideally Phase F (an installer should not be designed around
  only one adapter) — both already closed when this phase started.

### Phase L — Documentation completion — **CLOSED 2026-10-07**
- **Objective:** close the gaps named in §34 (contribution model, security
  reporting, explicit non-endorsement statement, versioning policy surfaced
  for users, not just `standard/versioning.md`'s internal audience).
- **Outcome:** this roadmap file itself discloses it was derived from
  repository archaeology, not a pasted mission document, so "§34" is not
  a file this repository has — this phase instead executed the four
  concrete items the objective line already names in parentheses, which
  are self-contained regardless of the external section number: added
  `CONTRIBUTING.md` (layering rules, what evidence/disclosure standards
  a change is expected to meet, how to run the five existing test
  suites, and that no license is chosen yet so no contribution license
  is implicitly granted) and `SECURITY.md` (in-scope surface named
  explicitly — the four Python helpers and both adapters' skill
  definitions — reporting channel, and the honest absence of a formal
  SLA/bug-bounty at this stage); added a non-endorsement statement and a
  user-facing "Versioning" section to the root `README.md` summarizing
  `standard/versioning.md` for a reader deciding whether to depend on
  this, plus `Contributing`/`Security` sections linking the two new
  files. Also fixed two README claims this pass's own prior phases had
  made stale (the "No installer" line under "Not in this draft", and
  the Claude setup adapter's live-acceptance status) rather than leaving
  them inconsistent with Phases A/K above.
- **Dependencies:** soft — can proceed incrementally alongside any other
  phase; should finalize only after Phase C/D naming stabilizes — both
  long since closed when this phase ran.

### Phase M — Versioning and release readiness — **1.0.0 CUT IN PROGRESS**
- **Objective:** apply `standard/open-questions.md`'s own gate ("each OQ
  MUST be resolved or explicitly deferred with reasoning before 1.0.0") and
  the mission §35 checklist before cutting the 1.0.0 release.
- **Dependencies:** effectively everything above; this is the terminal
  phase, not one that starts work.
- **Status (2026-10-07): OPEN-QUESTIONS GATE FULLY CLOSED; OWNER
  AUTHORIZATION RECEIVED.** All 12 entries in
  `standard/open-questions.md` are now `RESOLVED` or explicitly
  `DEFERRED` with reasoning (`OQ-002/003/004/005/006/007/008/009/011/012`
  resolved; `OQ-010` deferred past `1.0.0` with reasoning — conformance
  badge design needs a settled thing to check conformance against,
  which doesn't exist pre-`1.0.0`; `OQ-001` license resolved 2026-10-07
  — the project owner chose Apache License 2.0, specifically so anyone
  can use this specification and its reference adapters; see
  [`LICENSE`](../LICENSE)). The owner authorized the `1.0.0` cut in this
  session. A release-candidate system audit is being recorded at
  [`system-audit-1.0.0.md`](system-audit-1.0.0.md); adapter/evaluation
  limitations remain explicitly out of the Core stability claim. Every other named dependency of
  this phase — the adapter/evaluation work Phases A–L cover — is closed
  or substantially advanced as of this pass.

## 6. Human checkpoints already identified (do not bypass)

1. **Phase A's live mutating run** — **SATISFIED 2026-10-07.** Needed an
   interactive session with a human present to approve `Write` prompts;
   satisfied by running the setup skill directly inside the live
   conversational session itself (not a spawned headless subprocess, and
   no permissions-bypass flag used) — see `evaluation/claude-code-adapter.md`'s
   third live acceptance entry and Phase A above.
2. **Phase J's representative project selection** — RESOLVED 2026-10-06:
   owner selected a synthetic large fixture; PerdeOS stays excluded.
   Execution evidence substantially advanced 2026-10-07 (real setup
   resume, `FEATURE` gate pass, `REVIEW` pass — see Phase J above); full
   acceptance (the `BUG` workflow's own gates, `VERIFIED`/`ACCEPTED` for
   the `FEATURE`, any real owner checkpoint) remains outstanding and is
   not something further autonomous work produces for a synthetic
   fixture with no real external owner.
3. **The two corrupted refs** (`bootstrap-05-claude-adapter`,
   `vcps/claude-setup-adapter`) — deleting them is a destructive operation
   on ambiguous-ownership legacy state (mission §10). Recorded, not acted
   on, in this pass.
4. **The `1.0.0` version bump** — owner authorization received 2026-10-07;
   the release-candidate system audit is recorded in
   [`system-audit-1.0.0.md`](system-audit-1.0.0.md).

## 7. Immediate next recommended action

**Superseded 2026-10-07 — rewritten rather than left stale.** This
section, as last written, predated Phases K/L/M and this session's work
on H/I/J, and recommended exactly the phases that work has since closed
or substantially advanced. The actual state as of this pass:

- **Closed in full:** Phases A, B, C, D, K, L.
- **Closed to the fullest extent autonomously possible:** Phase H (the
  full 29/29 live Codex blind-diff catalog; broader-than-this-catalog
  coverage — more models, more phrasings, end-to-end skill runs rather
  than direct blind-review prompts — remains open by the phase's own
  original, intentionally open-ended objective, not from any remaining
  effort this pass withheld). Phase M (all 12 open questions resolved or
  explicitly deferred with reasoning, including `OQ-001` — license:
  Apache License 2.0, chosen by the project owner 2026-10-07; only the
  `1.0.0` authorization itself remains, a real product-owner decision).
- **Substantially advanced, genuinely open-ended remainder:** Phase I
  (several named gaps closed this pass — dependency scanning, a second
  webhook probe, real project-specific Gate 5 evidence — but "complete
  the §31 checklist systematically" has no finite finish line by its own
  phrasing; it is continuous work, not a task with a last step). Phase J
  (setup resume, a real `FEATURE` gate pass, and a real `REVIEW` pass are
  now genuine `LIVE_ADAPTER_EXECUTION` evidence in a disposable clone;
  what remains — `VERIFIED`/`ACCEPTED` for the `FEATURE`, the `BUG`
  workflow's own gates, any real owner checkpoint — each requires either
  real `E3 CI` infrastructure or an actual human decision an agent
  cannot produce for a synthetic fixture with no real external owner).
- **Phase E and Phase F's remaining items** (a Core-vocabulary decision
  this adapter should not invent unilaterally; an actual Codex CLI
  session with authorized external data transfer) were already correctly
  identified as the binding constraints in the prior version of this
  section, and remain so — Codex CLI access was confirmed available this
  pass (used throughout Phase H), narrowing Phase F's remaining gap to
  genuine end-to-end skill-loading/workflow acceptance specifically, not
  CLI access itself.

The `1.0.0` authorization and open-question gates are satisfied. Remaining
adapter, evaluation, and security-review work is tracked above and does not
change the explicitly bounded claim that only the Core requirements are
stable in this release.

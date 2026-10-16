# Phase J acceptance record — synthetic commerce

Date: 2026-10-06. Project choice: owner selected synthetic large fixture;
PerdeOS excluded. Controlled branch: `vcps-phase-j` in
`evaluation/fixtures/synthetic-commerce`, fixture HEAD
`30e28e73dd75dce4737173d77e63d29a5a5282c1` (adds the AG-011 record-history
preflight assertion to the controlled fixture runner).

## Exercised surface

- Synthetic app covers tenant-scoped order lookup, server-calculated invoice
  totals, inventory reservation, role checks, and signed/idempotent payment
  events. Eight local unit tests pass.
- `vcps_tool.py detect`: returns `RESUME`, no new mode, for the deliberately
  partial setup state.
- `vcps_tool.py validate --core <VCPS-root>`: `ok: true`, schema checks
  enabled, no errors. This validates fixture metadata shape and references,
  not a real adoption process.
- `vcps_router.py project-context`: reports synthetic L3 and risk domains.
- `escalation-check commerce/payments.py`: `forced_r3: true` via INV-001 and
  INV-002.
- `segmentation-scan commerce/payments.py`: reports the overlapping
  synthetic FEATURE record.
- `run_acceptance.py`: all 16 assertions pass and confirms the fixture Git
  tree remains clean. It exercises Core validation, evidence inventory,
  gate references, orphan detection, anti-gaming scan, router routing and
  segmentation, the parent/fix regression harness, and asserts that the BUG
  remains BLOCKED with explicit Gate 1–5 BLOCKED records and its finding
  OPEN; it never treats a blocker as PASS.
- Live Codex CLI 0.160.0 read-only pass on this fixture succeeded after
  approval to initialize local Codex state. It independently read `.vcps`,
  ran the documented test command (6/6 at that time), and reported L3/R3 plus missing
  baseline, evidence references, and production-fidelity evidence. No
  target files were modified.
- A second live Codex read after the state update confirmed `RESUME`, L3,
  Gates 1–5 all unevaluated, six tests passing at that point, and the absent
  baseline/evidence. No target files were modified.
- At parent commit `cd9912d`, duplicate-SKU demand of 6 against stock 5
  reproduced an oversell to `-1`. The fix aggregates demand before
  validation/reservation. Codex independently reviewed the change and ran
  7/7 tests; it noted the exact-stock boundary case was missing. An eighth
  test now proves exact aggregate demand is accepted and leaves zero stock.
  Initial preflight passed on `699a911`.
- `python3 tools/verify_duplicate_sku_regression.py` from the fixture root
  repeats the
  before/after check in an isolated temporary clone: `cd9912d` accepts the
  3+3 request against stock 5 and leaves `-1`; fix revision
  `dc82a11fe02d64b01b6b021da24f738563148de9` passes all eight domain tests,
  including over-demand rejection and exact-stock acceptance. This provides
  reproducible local evidence for VCPS-G4-031; it is not CI (`E3`) evidence
  and does not satisfy the L3/R3 independent-verifier requirement.
- Formal fixture records now exist: BUG-...0002 (`BLOCKED`), FND-...0002
  (`DEFECT`, `HIGH`, `OPEN`), EVD-...0010/0011 (parent `FAIL`, fix
  `PASS`, both `E2 LOCAL`), and five explicit `BLOCKED` Gate 1–5 records.
  The fixture Core validator reports ten schema-checked records, with no
  gate-reference issues or orphan refs. The FEATURE's Gate 1–5 remain
  unevaluated; the BUG has no passing gates, owner acceptance, or Gate 4/5
  independence claim.

A broader request to load the full Codex audit workflow and multiple VCPS
source directories was rejected by automatic safety review because it would
transmit more private VCPS source content than the synthetic-only
authorization covered. No retry/workaround was attempted; local preflight
remains the verified Phase J evidence.

## Setup Engine resume — 2026-10-07, closing one "Not established" item

A real `/vcps-setup` `RESUME` execution (all eleven stages) was performed
directly by an interactive Claude Code session (not a spawned `claude -p`
subprocess — the same direct-execution methodology that closed Phase A's
live mutating-path gap) against a **disposable clone** of this fixture at
the same HEAD (`30e28e73dd75dce4737173d77e63d29a5a5282c1`); the fixture
shown above was not modified. `detect` correctly returned `RESUME` (the
seeded config was internally consistent, just incomplete, routing
directly per `VCPS-SETUP-003` rather than a fresh mode selection). The
project's one configured check actually ran (8/8 `PASS`, `E2 LOCAL`); a
new `VCPS.md`, `.vcps/baseline.md`, a baseline `EVD` record, and a
`HIGH`-severity no-CI `EVIDENCE_GAP` finding (rated `HIGH` rather than a
lower severity because `VCPS-LVL-010` caps any `L3` gate relying on this
`E2 LOCAL` evidence at `PARTIAL`) were genuinely created. `validate
--core` reports `ok: true` (12 records). Both a same-session check and a
separately-launched, genuinely independent fresh `Agent` invocation (run
*before* any commit) confirmed `resumable: true`, `declared_status:
COMPLETE`, `stale_stages: {}` — a real clean no-op, closing the one gap
Phase A's own live acceptance had left open. Revision invalidation was
also verified live. Full narrative, exact hashes, and both fresh-session
results: `evaluation/runs/phase-j-setup-resume-2026-10-07.json`; a
durable snapshot of the new records: `evaluation/fixtures/phase-j-setup-resume/`.

**What this closes:** "this Phase J fixture itself still has no
Claude-authored setup state" below is no longer accurate as a blanket
claim — a real Claude-authored setup execution now exists (in a
disposable clone, not the fixture above, by design — see Phase A for why
mutating a precious evaluation fixture in place is avoided). **What this
does NOT close:** the `BUG` workflow's `Gate 1`–`5` remain `BLOCKED` by
design (not touched by this setup resume, which is deliberately scoped
to the Setup Engine's own narrow remaining obligation — see
`pending_artifact_refs` in the seeded `project.yaml`); no human/owner
checkpoint was exercised (there is no real external stakeholder for a
synthetic fixture); no production-shaped persistence/provider test
exists. The "Not established" list below is otherwise unchanged and
still accurate.

## FEATURE Gate 1-5 pass — 2026-10-07, closing a second "Not established" item

In the same disposable clone, immediately after the setup resume above,
`FEAT-00000000-0000-4000-8000-000000000001` (previously `PROPOSED`, zero
gates ever evaluated) went through a real Gate 1–5 pass against its
existing scope. Gate 1 (Product) and Gate 3 (Implementation): `PASS`.
Gate 2 (Architecture): `PARTIAL` — authorization/isolation/atomicity/
idempotency are genuinely engineered and verified; observability and
recovery are not (a new `LOW`-severity finding). Gates 4 (Verification)
and 5 (Security): both `BLOCKED` — a separately-launched, genuinely
independent fresh `Agent` session (`I2` independence) re-ran the
relevant tests for real, confirmed the signature/identity/replay/
exception-handling properties hold, and found **no defect**; both gates
are `BLOCKED` anyway because `standard/levels.md` requires `E3 CI`
fidelity for an `R3` invariant at `L3`, no hosted CI exists (the same
`HIGH`-severity no-CI finding the setup resume recorded), and
`VCPS-GATE-010` requires an owner `HC-08` decision before progressing
past even `PARTIAL` on a gap this severe — which an agent cannot grant
itself. `lifecycle_state` honestly advances to `CODED` only, not
`VERIFIED` or `ACCEPTED`. Full narrative:
`evaluation/runs/phase-j-setup-resume-2026-10-07.json`'s
`feature_gate_pass` section.

**What this closes:** "the FEATURE's gates remain unevaluated" is no
longer accurate — five real gate records now exist, each with a
defensible outcome and evidence basis. **What this does NOT close:**
`VERIFIED`/`ACCEPTED` for this `FEATURE` (both require things an agent
cannot manufacture: real `E3 CI` evidence or a real owner's `HC-08`/
acceptance decision); the `BUG` workflow; any real human checkpoint.

## REVIEW pass — 2026-10-07, closing a third "Not established" item

In the same disposable clone, a normal `/vcps-review` pass — never
previously exercised against this fixture, distinct from `BUG`'s
already-fixed duplicate-SKU scope — covered `commerce/orders.py` and
`commerce/admin.py` against `INV-001`/`INV-002`. Intended behavior was
reconstructed from the invariants and the existing test suite; tracing
the actual code end to end against it, confirmed by the real 8/8 test
run, found **no `DEFECT`**: tenant-scoped lookups, all-or-nothing stock
reservation, and role-gated cancellation are all correctly implemented.
One `EVIDENCE_GAP` was found and recorded (`FND-647e1a7f-...`, `LOW`):
the non-`PENDING` cancellation rejection path is correct by inspection
but has no executed test. Per `workflows/review.md`'s own exit
condition, this is honestly reported `PARTIALLY REVIEWED`, not "clean"
or "fully verified." See `REV-7b2275d1-4819-4dd5-abaf-fb192b84aa10` and
the `review_pass` section of
`evaluation/runs/phase-j-setup-resume-2026-10-07.json`.

**What this closes:** "the normal feature/review workflow was not
exercised" no longer applies to `REVIEW` specifically (a real pass now
exists, with a real, non-trivial, defensible result). **What this does
NOT close:** the `BUG` workflow; the review's own open `EVIDENCE_GAP`;
any real human/owner checkpoint.

## Not established

This is a **preflight, not full Phase J acceptance**. The fixture defect was
reproduced and corrected, and its parent/fix behavior now has repeatable
local regression evidence and formal BUG/finding/evidence records. The BUG
workflow remains blocked: its Gate 1–5 records are all `BLOCKED`, not
passing outcomes. Do not consider it closed. A local read-only
AUDIT was also completed and reports `PARTIAL` in
`evaluation/synthetic-commerce-audit.md`. The `.vcps/` metadata shown in
this fixture was authored as a synthetic seed, not produced by a real
Setup Engine run here (a real resume now exists only in a disposable
clone — see above). No complete BUG workflow, normal feature/review
workflow, gate sequence, human checkpoint/approval, independent Gate 4/5
review, or production-shaped persistence/provider test was executed
against *this* fixture. The existing FEATURE has no evidence refs, while
the BUG has only its local E2 regression artifacts. The fixture is not
production-ready evidence.

Repeat:

```sh
cd evaluation/fixtures/synthetic-commerce
python3 run_acceptance.py
```

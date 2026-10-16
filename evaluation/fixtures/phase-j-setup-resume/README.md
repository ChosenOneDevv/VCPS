# Phase J setup-resume fixture

This is a durable snapshot of a live `/vcps-setup` `RESUME` execution,
performed directly by an interactive Claude Code session (not a spawned
`claude -p` subprocess), in a disposable clone of the owner-selected
synthetic commerce project at HEAD
`30e28e73dd75dce4737173d77e63d29a5a5282c1`.

Per `evaluation/completion-roadmap.md`'s own Phase J status, this
project's `.vcps/` state had only ever been *seeded* as a synthetic
fixture (`installation.status: PARTIAL`, `stage: 1`, `stage_events: []`)
— never run through a real Setup Engine execution. This snapshot closes
that specific gap: all eleven stages were actually executed, with a real
test run (`python3 -m unittest discover -s tests -v`, 8/8 `PASS`, `E2
LOCAL`), a genuinely new `baseline.md`, a new `EVD-8e8bb3c0-...` evidence
record, a new `FND-5ed8b1b2-...` legacy `EVIDENCE_GAP` finding (no
hosted CI — rated `HIGH`, not the lower severity used in smaller
fixtures, because `standard/levels.md` `VCPS-LVL-010` caps any gate
relying on this `E2 LOCAL` evidence at `PARTIAL` for an `L3` project),
and a new `VCPS.md`.

The real, pre-existing `BUG-...0002` / `FEAT-...0001` records and their
`GATE` records were deliberately left untouched — they are separate,
already-in-flight workflow records outside this Setup Engine resume's
scope (see `.vcps/project.yaml`'s stage 5/11 reasons for the explicit
disclaimer). This snapshot does not close the BUG or FEATURE workflows;
see `evaluation/phase-j-acceptance.md` for what remains open.

`vcps_tool.py validate --core` reports `ok: true` (12 records, zero
errors) against this state. A same-session `resume-status` immediately
after completion, and a separately-launched, genuinely independent fresh
Agent invocation (no shared conversation state) run *before* any commit,
both reported `resumable: true`, `declared_status: COMPLETE`,
`earliest_incomplete_stage: null`, `stale_stages: {}` — a real
clean-resume no-op, closing the one item Phase A's own live acceptance
pass had left open (a true no-op check obtained before any post-setup
commit). Revision invalidation was also tested live: a trivial edit to
`commerce/orders.py` correctly reset `earliest_incomplete_stage` to `1`
with all eleven stages stale; reverting it returned `resume-status` to
clean.

One real, previously-undocumented nuance was discovered and corrected
during this pass, consistent with Phase A's own finding: a `.`-scoped
stage's `input_fingerprint` must be computed *after* that stage's own
non-`.vcps/` output (here, `VCPS.md`) already exists, not strictly
before it — `vcps_tool.py`'s `.vcps/` exclusion in `expand_scope` does
not extend to `VCPS.md` itself, so a pre-output fingerprint would make
every future resume check show that stage as permanently stale. This
was caught and fixed before the state shown here was finalized.

The owner-selected source fixture (`evaluation/fixtures/synthetic-commerce/`)
remains unchanged; this snapshot is evaluation evidence from a disposable
clone, not active project state.

See [the run record](../../runs/phase-j-setup-resume-2026-10-07.json) for
the full stage-by-stage narrative, exact fingerprints/hashes, and both
fresh-session check results.

## FEAT-001 real Gate 1-5 pass

In the same disposable clone, immediately after the setup resume above,
`FEAT-00000000-0000-4000-8000-000000000001` ("Synthetic payment
idempotency scenario", `R3`/`L3`, previously `PROPOSED` with zero gates
ever evaluated) went through a real `/vcps-feature` Gate 1-5 pass against
its existing scope (`commerce/payments.py`, `tests/test_commerce.py` --
reviewing already-existing code, not writing new code):

- **Gate 1 (Product): `PASS`.** `AC-1` and an `escalation-check`-derived,
  impact-path-cited `R3` classification are recorded.
- **Gate 2 (Architecture): `PARTIAL`.** Authorization, isolation,
  atomicity, and idempotency are genuinely engineered and verified;
  observability and recovery are not (`FND-1cfb269e-...`, `LOW`).
- **Gate 3 (Implementation): `PASS`.** No fabrication, no secrets, no
  silently-swallowed errors, zero anti-gaming scan hits.
- **Gates 4 (Verification) and 5 (Security): both `BLOCKED`.** A
  separately-launched, genuinely independent fresh `Agent` session
  (`I2` independence -- not given this session's reasoning, formed its
  own judgment from `AC-1` and the code alone) re-ran the two relevant
  tests for real (`PASS`), confirmed `hmac.compare_digest` constant-time
  signature verification, confirmed the object-level payload-identity
  check, confirmed replay rejection, and found no swallowed exceptions or
  cross-tenant exposure -- **no defect was found**. Both gates are
  `BLOCKED` anyway, honestly, because `standard/levels.md` requires `E3
  CI` fidelity for an `R3` invariant assertion at `L3`, no hosted CI
  exists (the same `HIGH`-severity `FND-5ed8b1b2-...` the setup resume
  recorded), and `VCPS-GATE-010` requires an owner `HC-08` decision
  before progressing past even `PARTIAL` on a gap this severe at this
  level -- which an agent cannot grant itself.

`FEAT-00000000-0000-4000-8000-000000000001`'s `lifecycle_state` honestly
advances only to `CODED` (Gates 1-3 PASS/PARTIAL), not `VERIFIED`
(requires Gates 4-5 PASS or permitted `PARTIAL`, which these are not) and
certainly not `ACCEPTED` (an agent MUST NOT set that itself,
`VCPS-LC-003`). `validate --core` reports `ok: true` (18 records, zero
errors) against this final state.

See [the run record](../../runs/phase-j-setup-resume-2026-10-07.json)'s
`feature_gate_pass` section for the full narrative, including the
independent verifier's exact findings.

## A real /vcps-review pass

In the same disposable clone, a normal `/vcps-review` pass (never
previously exercised against this fixture) covered
`commerce/orders.py` and `commerce/admin.py` against `INV-001`/
`INV-002` -- order creation/reservation and cancellation, distinct from
`BUG-...0002`'s already-fixed duplicate-SKU scope. Intended behavior was
reconstructed from the invariants and the existing test suite; actual
behavior was traced end to end and confirmed by the real 8/8 test run.
**No `DEFECT` found** -- tenant-scoped lookups, all-or-nothing stock
reservation, and role-gated cancellation are all correctly implemented.
One `EVIDENCE_GAP` was found and recorded (`FND-647e1a7f-...`, `LOW`):
`cancel_order`'s rejection of a non-`PENDING` order is correct by
inspection but has no executed test. Per `workflows/review.md`'s exit
condition, this is honestly reported `PARTIALLY REVIEWED`, not "clean."
See `REV-7b2275d1-...`.

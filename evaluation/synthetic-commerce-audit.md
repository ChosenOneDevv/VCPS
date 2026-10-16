# Synthetic Commerce audit report

Date: 2026-10-06. Scope: the synthetic Phase J target at commit
`30e28e73dd75dce4737173d77e63d29a5a5282c1` on branch `vcps-phase-j`, following `workflows/audit.md`.
In scope: `.vcps/` state, the single proposed feature, its Python domain
code and tests, setup/router/helper outputs. Out of scope: real database,
provider, deployed service, secrets management, CI, production IAM, and
runtime integration behavior; none exists in this fixture.

## Coverage and evidence basis

| Audit area | Coverage | Basis |
|---|---:|---|
| Work-item classification and state | 2/2 | The FEATURE remains PROPOSED with Gates 1–5 unevaluated. The duplicate-SKU BUG is BLOCKED with explicit Gate 1–5 BLOCKED records. Both are R3 at L3. |
| Recorded evidence records | 2/2 | EVD-...0010 records the parent-revision stock-safety FAIL; EVD-...0011 records local fix-regression PASS at `dc82a11`. Evidence inventory parses both without error. |
| Recorded gate outcomes | 5 BLOCKED / 5 NOT_EVALUATED | The FEATURE has no Gate 1–5 evaluations. The BUG has explicit Gate 1–5 records, all `BLOCKED` with reason codes; none is a PASS. Gate 6 is per release and no release unit exists. |
| Findings/classification records | 1/1 | FND-...0002 is a HIGH DEFECT, OPEN, tied to the BUG and both E2 evidence records. |
| Anti-gaming literal scan | 8/8 source/test files | Helper scan of seven commerce modules and `tests/test_commerce.py`: zero candidate matches, zero rejected paths. It cannot detect semantic weakening or establish a clean history. |
| Router invariants | 2/2 applicable invariants | `escalation-check` on `commerce/payments.py` matches INV-001 and INV-002; `forced_r3: true`. |
| Schema and reference consistency | 1/1 project validation | `vcps_tool.py validate --core <root>` returns `ok: true`, schema checks enabled. |

The project risk profile is internally consistent at L3. The router
surfaces financial, tenant-isolation, inventory, and payment-callback
domains as contextual facts; it does not itself judge whether the feature
is safe. Local executable evidence is eight passing unit tests and the
repeatable `run_acceptance.py` preflight. Recorded E2 evidence is limited to
in-memory behavior; it is not CI, production, or independent Gate 4 evidence.

## Findings

1. **EVIDENCE_GAP — required verification/gate record set absent.** The
   proposed R3 feature lists Gates 1–5, all unevaluated, and has no evidence
   references. The BUG's five Gate 1–5 records are BLOCKED. It has two E2
   local records, but they do not substitute
   for Gate 3/4/5 records, an evaluated revision, required independence, or
   evidence-tier/fidelity metadata. Keep the feature PROPOSED and do not
   treat any gate as PASS.
2. **EVIDENCE_GAP — setup baseline and canonical artifact incomplete.**
   Setup remains PARTIAL at Stage 1; `baseline_ref` is null and
   `.vcps/baseline.md` plus `VCPS.md` are pending. Do not claim the fixture
   has a completed adoption or a baseline against which regressions were
   evaluated.
3. **DEFECT — duplicate-SKU stock
   oversell.** At parent commit `cd9912d`, two 3-unit lines against stock 5
   were accepted and left stock at `-1`. The current branch aggregates
   per-SKU demand, rejects the request, and includes regression tests for
   over-demand and exact-stock acceptance. The repeatable test tool and
   formal BUG, finding, two E2 evidence records, and five BLOCKED Gate 1–5
   records now exist. The finding remains OPEN and the BUG BLOCKED: L3/R3
   Gate 4 requires E3 CI and I2 independence, neither available here.
4. **EVIDENCE_GAP — production fidelity/security controls unproven.**
   Tenant scoping, HMAC checks, idempotency, and inventory atomicity are
   exercised only in a process-local stand-in. No database isolation,
   multi-process concurrency, production key handling, real provider
   signature contract, deployment configuration, or runtime logging
   exposure evidence exists.

The proposed feature remains PROPOSED with acceptance PENDING. The verified
code defect is kept distinct from EVIDENCE_GAPs for the absent baseline, CI,
independence, and production fidelity. No RISK_ACCEPTED decision or human
checkpoint exists.

## Conformance

**PARTIAL** (`VCPS-CORE-033`). Structural metadata and the listed local
invariant tests are consistent, but the absence of a baseline, E3 evidence,
Gate 1–5 evaluations, independent security review, and production-fidelity
verification prevents any `FULL` conformance claim. This report does not
modify the target repository, per `VCPS-WF-AUDIT-001`.

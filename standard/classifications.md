# Finding Classifications

This document owns: finding classifications, severity, finding status, and
classification transitions.

## 1. Classifications

**VCPS-CLS-001.** Every material finding MUST be classified as exactly one of:

| Classification | Definition | Minimum evidence to assign |
|----------------|------------|----------------------------|
| `DEFECT` | Behavior, code, configuration, or check demonstrably deviates from intended behavior, a requirement, or a registered invariant. | Reproduction (`E2`+ with result `FAIL`), **or** a static demonstration (`E1`) where the deviation is determinable from the artifact alone, with the reasoning recorded. |
| `EVIDENCE_GAP` | Required evidence is missing, stale, insufficient in tier or fidelity, or inconclusive. Actual behavior is unknown. | A recorded requirement and the absence or inadequacy of its evidence. |
| `EXTERNAL_ACCEPTANCE` | Resolution depends on a party outside the repository work: product decision, provider confirmation, legal/compliance sign-off, operations, or customer acceptance. | Identification of the external party and the decision needed. |
| `KNOWN_LIMITATION` | A deliberate, documented constraint or residual behavior accepted by an authorized human. | A checkpoint record per [human-checkpoints.md](human-checkpoints.md) when severity is `HIGH` or above, or the owner's recorded acceptance otherwise. |

A finding is *material* if it affects a gate outcome, a lifecycle state, a
critical invariant, security, or user-visible behavior.

**VCPS-CLS-002.** A `DEFECT` assigned from static demonstration alone at
severity `HIGH` or above SHOULD receive a reproduction before remediation is
declared complete (see [gates/gate-4-verification.md](gates/gate-4-verification.md)).

**VCPS-CLS-003.** A missing test, missing environment, unavailable credential,
or unexecuted check MUST be classified `EVIDENCE_GAP`, not `DEFECT`.

**VCPS-CLS-004.** A check that fails reproducibly is a `DEFECT` — in the product
or in the check itself. When the side is unknown, the finding MUST record the
target as `UNATTRIBUTED`. A check whose failure does not reproduce is an
`EVIDENCE_GAP` (result `INCONCLUSIVE`).

**VCPS-CLS-005.** `KNOWN_LIMITATION` MUST NOT be used to hide a `DEFECT` that
violates a registered critical invariant, unless the invariant itself is
amended through `HC-08`.

## 2. Transitions between classifications

| From → To | Allowed when |
|-----------|--------------|
| `EVIDENCE_GAP` → `DEFECT` | Reproduction or static demonstration per VCPS-CLS-001 is recorded. MUST NOT happen on suspicion alone. |
| `EVIDENCE_GAP` → resolved (no finding) | Required evidence obtained with result `PASS`. |
| `DEFECT` → `KNOWN_LIMITATION` | Owner/Approver acceptance recorded (checkpoint `HC-08` if `HIGH`+). |
| `EXTERNAL_ACCEPTANCE` → `DEFECT` / `KNOWN_LIMITATION` / resolved | External decision recorded as `E4` evidence. |
| `DEFECT` → `EVIDENCE_GAP` | Reproduction found invalid (e.g. faulty test harness); record why. |
| any → `WITHDRAWN` status | Finding shown to be erroneous; reasoning recorded. |

**VCPS-CLS-010.** Every reclassification MUST be recorded with the prior
classification, the reason, and the evidence. Findings MUST NOT be silently
deleted.

## 3. Severity

| Severity | Meaning |
|----------|---------|
| `CRITICAL` | Violates a critical invariant, enables unauthorized access or cross-tenant exposure, causes irreversible data/financial loss, or blocks core function for all users. |
| `HIGH` | Significant incorrect behavior or security weakness on an important path; recoverable but costly. |
| `MEDIUM` | Incorrect behavior with workaround or limited impact. |
| `LOW` | Minor issue, cosmetic or maintainability concern. |

**VCPS-CLS-020.** Severity applies to all classifications. For an
`EVIDENCE_GAP`, severity is the severity of the worst plausible defect the
missing evidence could hide.

**VCPS-CLS-021.** Blocking thresholds by level are owned by
[levels.md §5](levels.md#5-blocking-severity-threshold).

## 4. Finding status

| Status | Meaning |
|--------|---------|
| `OPEN` | Not yet resolved. |
| `RESOLVED` | Remediated (for `DEFECT`) or evidence obtained (for `EVIDENCE_GAP`), with evidence. |
| `RISK_ACCEPTED` | Left unresolved by an authorized human decision, with scope and optional expiry. Applicable to `EVIDENCE_GAP` and `EXTERNAL_ACCEPTANCE`. |
| `WITHDRAWN` | Shown erroneous. |

`KNOWN_LIMITATION` findings are in status `RISK_ACCEPTED` by definition.

**VCPS-CLS-030.** `RISK_ACCEPTED` at severity `HIGH` or above requires `HC-08`.
An agent MUST NOT set `RISK_ACCEPTED` on its own authority.

**VCPS-CLS-031.** A `RESOLVED` `DEFECT` MUST reference remediation evidence
at the tier required by the project level and, where practical, a regression
test (see VCPS-G4-030).

## 5. Finding record

**VCPS-CLS-040.** A finding record MUST include: `id`, `title`,
`classification`, `severity`, `status`, `scope` (files/components/features),
`requirement_refs`, `evidence_refs`, `discovered_by` (role and identity),
`discovered_in` (workflow and revision), `owner` (when assigned), and
`history` of classification and status changes.

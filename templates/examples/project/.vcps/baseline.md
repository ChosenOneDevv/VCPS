---
schema_version: "0.1.0"
revision: "3f1a9c0e2b7d"
date: "2026-08-03"
observations:
  - id: "BLO-00000000-0000-4000-8000-000000000011"
    check_id: "test"
    result: PASS
    evidence_ref: "EVD-00000000-0000-4000-8000-000000000002"
    finding_ref: null
  - id: "BLO-00000000-0000-4000-8000-000000000012"
    check_id: "lint"
    result: PASS
    evidence_ref: "EVD-00000000-0000-4000-8000-000000000002"
    finding_ref: null
inherited_finding_refs:
  - "FND-00000000-0000-4000-8000-000000000001"
environment_limitations:
  - "No hosted CI; every check above is E2 LOCAL only (see FND-00000000-0000-4000-8000-000000000001)."
history: []
---

## Baseline: todo-cli at 3f1a9c0e2b7d

Both configured checks (`test`, `lint`) passed cleanly at the adopt
revision, so there is no pre-existing failure to carry forward as a
baseline exception. The only inherited gap is the no-CI
`EVIDENCE_GAP` itself (`FND-00000000-0000-4000-8000-000000000001`),
which is about verification infrastructure, not a check result.

No `ADD_OBSERVATION`/`RESOLVE_OBSERVATION` history yet: both original
observations remain `PASS` and unresolved-because-passing.

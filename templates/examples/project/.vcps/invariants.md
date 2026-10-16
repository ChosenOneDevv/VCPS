---
schema_version: "0.1.0"
invariants:
  - id: "INV-001"
    statement: "A todo item marked done is never silently reverted to not-done by a background sync."
    owner:
      role: human
      identity: "project-owner"
    impact_dimensions:
      - "D1"
      - "D7"
    component_scope:
      - "sync"
    enforcement_path:
      - "src/sync.js"
      - "tests/sync.test.js"
    evidence_refs:
      - "EVD-00000000-0000-4000-8000-000000000002"
      - "EVD-00000000-0000-4000-8000-00000000000d"
    status: ACTIVE
    history:
      - timestamp: "2026-08-03T09:10:00Z"
        change: "created"
        reason: "Registered during SETUP ADOPT Stage 3 draft invariant registry (VCPS-SETUP-014), after tracing src/sync.js's merge behavior."
      - timestamp: "2026-09-12T14:30:00Z"
        change: "enforcement verified"
        reason: >-
          FND-00000000-0000-4000-8000-00000000000c demonstrated a real
          violation path (same-second write collision); fixed and
          regression-tested under BUG-00000000-0000-4000-8000-000000000005.
          Any future change to src/sync.js or tests/sync.test.js is R3
          per VCPS-RISK-041.
---

## Critical invariant registry: todo-cli

One invariant so far, covering the only `L2`-driving impact path in this
small project. A future `FEATURE`/`REVIEW` MAY discover and register
more (`VCPS-SETUP-014`: exhaustive invariant discovery is not required
at setup time; coverage SHOULD improve over subsequent runs).

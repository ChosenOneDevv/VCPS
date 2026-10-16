---
schema_version: "0.1.0"
profiles:
  - scope: "PROJECT"
    dimensions:
      D1:
        rating: 2
        impact_paths:
          - "src/sync.js"
        evidence_refs:
          - "EVD-00000000-0000-4000-8000-000000000002"
      D2:
        rating: 0
      D3:
        rating: 0
      D4:
        rating: 0
      D5:
        rating: 0
      D6:
        rating: 0
      D7:
        rating: 1
        impact_paths:
          - "src/sync.js"
          - "src/devices.js"
        evidence_refs:
          - "EVD-00000000-0000-4000-8000-000000000002"
      D8:
        rating: 0
      D9:
        rating: 0
    derived_level: L2
    rationale: >-
      D1=2: todo items are the project's authoritative record, and a
      background-sync defect in src/sync.js can silently revert a
      completed item to incomplete -- corruption of an authoritative
      record (VCPS-RISK-020's "any dimension rated 2" clause). D7=1: a
      household-scale blast radius (a handful of shared devices), not
      severe. No dimension reaches 3. Independently, the system is used
      by people other than its builders with persistent data, which
      alone would already imply at least L2.
    shared_path_elevation: false
    history:
      - timestamp: "2026-08-03T09:10:00Z"
        reason: "Initial risk classification during SETUP ADOPT Stage 3."
---

## Project risk profile: todo-cli

Single-component project; no separate per-component profile is needed.
D1 and D7 are the only nonzero dimensions, both traced to `src/sync.js`'s
merge behavior (`VCPS-RISK-001`/`002`: traced impact path, not a keyword
match). See `.vcps/invariants.md` for the resulting `INV-001`.

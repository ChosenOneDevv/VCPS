---
schema_version: "0.1.0"
revision: "30e28e73dd75dce4737173d77e63d29a5a5282c1"
date: "2026-10-07"
observations:
  - id: "BLO-033abc8d-5304-4265-819a-820b2bc56a32"
    check_id: "test"
    result: PASS
    evidence_ref: "EVD-8e8bb3c0-5335-4a30-9458-f21f432fea10"
    finding_ref: null
inherited_finding_refs:
  - "FND-00000000-0000-4000-8000-000000000002"
environment_limitations:
  - "No hosted CI; the `test` check above is E2 LOCAL only (VCPS-LVL-010; see FND-5ed8b1b2-2b5a-41f0-8df1-94287d034ec2). At this project's L3 level, any gate relying on this E2 LOCAL evidence alone MUST NOT exceed PARTIAL."
history: []
---

## Baseline: Synthetic Commerce Evaluation Fixture at 30e28e73dd75dce4737173d77e63d29a5a5282c1

The only configured check (`test`) was run for real during this
`/vcps-setup` resume and passed cleanly (8/8). This is the first time
this project's own baseline has been persisted as a VCPS artifact — the
`.vcps/` state was previously seeded directly as a synthetic fixture
(`evaluation/completion-roadmap.md` Phase J), not produced by a real
Setup Engine run.

`FND-00000000-0000-4000-8000-000000000002` (the duplicate-SKU defect
underlying `BUG-00000000-0000-4000-8000-000000000002`) is inherited here
only because it predates this baseline's revision; it is a `BUG`-workflow
finding, not a Setup-stage finding, and this baseline does not evaluate
or resolve it. No `ADD_OBSERVATION`/`RESOLVE_OBSERVATION` history yet.

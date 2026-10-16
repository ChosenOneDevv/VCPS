---
name: vcps-feature
description: Build new behavior or materially change intended behavior under risk-proportionate full VCPS gate discipline. Use for capability work, not a reported defect or R0 cosmetic change.
---

# VCPS feature

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/feature.md` in full. Read `standard/gates/README.md` applicability matrix and every applicable gate definition before recording outcomes. This workflow requires full Gate 1–5 discipline; actual gate outcomes remain evidence-based judgments.

Resolve the VCPS source root using `adapters/codex/vcps-setup/SKILL.md` §0. The target repository may be different; run helpers from the VCPS source root and pass the target explicitly. If the source root or required helper is missing, report `BLOCKED` and do not proceed as though checks returned clean results.

Before design, identify plausible touched paths and gather these mechanical facts from the VCPS repository root:

```sh
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [--touched-path <path> ...]
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py project-context --target <repo>
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py segmentation-scan --target <repo> --touched-path <path> [--touched-path <path> ...]
```

`forced_r3: true` is a floor. `critical_domains` and segmentation overlaps are investigation signals, not automated classification. Reassess risk as scope changes. Apply Gate 1, conditional/required Gate 2, Gate 3, Gate 4, and Gate 5 per the matrix. Gate 4/5 evidence must be on the same revision used to claim `VERIFIED`. Only an Owner/delegate can accept via HC-14; hand off release work to `workflows/release.md`.

Optional shared checks:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py evidence-inventory --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <path> [--scope-path <path> ...]
python3 adapters/claude-code/lib/vcps_evidence.py orphan-check --target <repo>
```

Before mutation, establish `approval_policy = "untrusted"` or a trusted `.codex/rules/*.rules` prompt rule covering the intended writes and commands. The skill cannot enforce it. See `../references/capability-mapping.md`. Never claim gates passed from helper output alone, accept on your own authority, or lower R3 without justification and HC-09.

If work is R0 throughout, route to TINY. If Gate 1 discovery reveals an unrelated existing defect, split it into BUG unless fixing it is necessary to implement the feature. If an unaccounted invariant is touched, repeat Gate 1/2 at R3. Report `CODED` or `VERIFIED` as an intermediate state, never as workflow completion; `ACCEPTED` requires Owner/delegate acceptance against every criterion.

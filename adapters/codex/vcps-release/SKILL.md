---
name: vcps-release
description: Evaluate a release unit under VCPS Gate 6 after its changes completed their required workflows. Record go/no-go and post-release evidence; deployment itself remains an external action.
---

# VCPS release

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/release.md` and read `standard/gates/gate-6-release.md` in full. Assemble the exact release revision and included work-item IDs. Before Gate 6, run the shared readiness check from the VCPS repository root:

Resolve the VCPS source root using `adapters/codex/vcps-setup/SKILL.md` §0. The target repository may be different; run helpers from the VCPS source root and pass the target explicitly. If the source root or readiness helper is missing, report `BLOCKED`; do not treat a missing readiness result as permission to release.

```sh
python3 adapters/claude-code/lib/vcps_evidence.py release-readiness-check --target <repo> --release-revision <rev> --work-item-ref <id> [--work-item-ref <id> ...]
```

Resolve or explicitly justify every reported issue before Gate 6 can PASS. Revision mismatches are staleness candidates; judge carry-forward against evidence scope. Evaluate Gate 6 once for the complete release unit at depth set by its highest risk class and project level. HC-10 is required at L2+; only the authorized human may decide it. Record go/no-go; unmet conditions or rejection leave Gate 6 BLOCKED.

This skill does not trigger deployment. After a real deployment, gather E5 evidence for each feature during its observation window. Promote to `PRODUCTION_PROVEN` only when that evidence is sufficient and no CRITICAL/HIGH production finding remains. On failure, apply lifecycle demotion and route to BUG or HOTFIX as appropriate.

Optional checks:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py evidence-inventory --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py orphan-check --target <repo>
```

Helpers surface facts, not release judgments. Before writing release records, establish `approval_policy = "untrusted"` or a trusted rules prompt for intended writes. See `../references/capability-mapping.md`. Never infer HC-10 from silence or PRODUCTION_PROVEN merely because a release went live.

Gate 6 applies once to the complete release unit, not once per change. A required HC-10 decision must be made by its authorized human for this exact release; the agent cannot supply it. If required evidence is stale or missing, leave the unit BLOCKED (DEPENDENCY) until it is re-verified or removed and readiness is checked again.

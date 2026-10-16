---
name: vcps-tiny
description: Make a genuinely R0 cosmetic, copy, documentation, or formatting change that does not alter behavior or touch an invariant enforcement path. Route uncertain or behavioral work through the VCPS router.
---

# VCPS tiny

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/tiny.md` in full. Before changing anything, identify plausible touched paths and run the mechanical escalation check from the VCPS repository root:

Resolve the VCPS source root using `adapters/codex/vcps-setup/SKILL.md` §0. The target repository may be different; run helpers from the VCPS source root and pass the target explicitly. If the source root or router helper is missing, report `BLOCKED` and do not proceed as though escalation returned false.

```sh
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [--touched-path <path> ...]
```

If `forced_r3: true`, stop and route to BUG or FEATURE. Also stop if your own inspection finds impact on logic, queries, access control, external calls, schema, user/system behavior, or an invariant path. `forced_r3: false` is not proof of R0.

Run Gate 3 and Gate 4 at light depth; Gates 1, 2, and 5 are `NOT_APPLICABLE` only under R0. The optional anti-gaming scan returns candidates, not a verdict:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <path> [--scope-path <path> ...]
```

If work grows beyond cosmetic scope or checks suggest a behavior change, stop and re-route immediately. Before mutation, establish `approval_policy = "untrusted"` or a trusted Codex rules prompt covering the intended writes; Codex's default may write in-workspace without prompting. See `../references/capability-mapping.md`.

Run the project's actual configured checks and compare with baseline; Gate 3 and Gate 4 light checks are never skipped. Exit only as `CODED` with light Gate 3 and Gate 4 `PASS`. TINY does not grant acceptance authority.

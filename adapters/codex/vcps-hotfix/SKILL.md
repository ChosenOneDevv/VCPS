---
name: vcps-hotfix
description: Quickly remediate a confirmed live production problem while deferring only through the VCPS HC-16 process. Use only with evidence of current production impact; unconfirmed urgency belongs to BUG.
---

# VCPS hotfix

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/hotfix.md` in full. Entry requires confirmed live production impact supported by `E2`+ production reproduction/evidence or `E5` direct observation. If impact is unconfirmed, stop and use BUG.

Resolve the VCPS source root using `adapters/codex/vcps-setup/SKILL.md` §0. The target repository may be different; run helpers from the VCPS source root and pass the target explicitly. If the source root or lapsed-deferral helper is missing, report `BLOCKED`; do not skip the deferral check silently.

State the production evidence and tier, define the smallest relief change, and record full discovery deferred as an `EVIDENCE_GAP`. Gate 2 is required for critical-state mechanisms and may otherwise be deferred only through HC-16. Gate 3 is full with no exception. Gate 4 may be reduced only through HC-16; record omitted scope, residual risk, owner, and deadline. Gate 5 applies to every touched category. HC-10 and HC-03 cannot be waived; hand off actual Gate 6 to RELEASE. Schedule the required BUG or REVIEW follow-up for each deferred gap.

Run the lapsed-deferral check before closing, from the VCPS repository root:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py lapsed-deferral-check --target <repo>
```

Treat matches as candidates and review their deadlines and approvals. Every deferral must use HC-16 and be recorded PARTIAL or BLOCKED, never PASS. Before mutation, establish `approval_policy = "untrusted"` or a trusted rules prompt covering the intended writes and commands. If this boundary is unavailable, stop before mutation and report it. See `../references/capability-mapping.md`.

Exit only with production harm stopped and evidenced, each deferral owned and dated, and required follow-up scheduled and linked. Never infer production impact from urgency language.

HOTFIX never bypasses HC-01 through HC-05 or HC-11/HC-12. HC-16 is the only deferral mechanism, and its approval record must state what was deferred, why, residual risk, owner, and deadline. A missed or absent deadline is a blocking HIGH+ candidate requiring HC-08 re-acceptance or immediate scheduling. If investigation disproves live impact, stop and re-route to BUG immediately.

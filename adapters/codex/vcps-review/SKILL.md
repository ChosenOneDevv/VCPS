---
name: vcps-review
description: Review existing behavior against its intended behavior, remediate only confirmed defects, and record unresolved evidence gaps. Use for broad correctness reviews, not a reported known bug or read-only conformance audit.
---

# VCPS review

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/review.md` in full, and read `workflows/bug.md` steps 3–6 before remediating a confirmed defect. Review is not a read-only audit, but only `DEFECT` findings may be fixed. Never remediate `EVIDENCE_GAP` or `EXTERNAL_ACCEPTANCE` as though confirmed (`VCPS-CLS-003`/`AG-008`).

## Locate the VCPS source root

Use the Core-discovery checks from `adapters/codex/vcps-setup/SKILL.md` §0: find a VCPS source root containing non-empty `standard/VCPS.md`, `VERSION`, and the required workflow/helper files. The target repository and VCPS source root may differ. Run the helper commands below from that source root, with `--target` set to the target repository. If the source root or helper is missing, report `BLOCKED`; do not treat a missing check as a clean result.

Reconstruct intended behavior from cited sources and evidence tiers; conflicting or absent intent is an ambiguity to record, not guess away. Trace the implementation end to end, classify each difference per `standard/classifications.md`, and perform Gate 5 review over the full reviewed scope. A defect fix follows BUG risk/gate requirements and gets regression evidence where required. Before closing, leave unresolved gaps OPEN with an owner or route pre-existing gaps to the legacy registry as Core specifies.

Classify demonstrated deviations as `DEFECT`, unknown intent/behavior as `EVIDENCE_GAP` or `EXTERNAL_ACCEPTANCE`, and deliberate accepted tradeoffs as `KNOWN_LIMITATION`. Route a production-reachable security exposure to the applicable HC-05 checkpoint and HOTFIX assessment; a reconstructed intent that conflicts with a registered invariant requires HC-08. Do not call review “clean” while any in-scope evidence gap is open.

Optional shared checks, run from the VCPS repository root:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py evidence-inventory --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py orphan-check --target <repo>
```

Staleness mismatches and orphan results are candidates to inspect, not verdicts. If remediation is needed, first establish `approval_policy = "untrusted"` or a trusted `.codex/rules/*.rules` prompt rule covering the planned writes and commands. Codex has no per-skill write scoping; if that boundary is not confirmed, stop before mutation and report the gap. See `../references/capability-mapping.md`.

Exit with counts by classification and remediation evidence. Do not report “clean” or “fully verified” while an in-scope `EVIDENCE_GAP` remains open; use `PARTIALLY REVIEWED` and list the gaps.

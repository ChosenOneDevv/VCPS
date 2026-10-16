---
name: vcps-audit
description: Audit a repository, component, or VCPS installation without changing code or behavior. Use for conformance and installation health checks, not for fixing bugs.
---

# VCPS audit

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/audit.md` in full. This is a read-only workflow: do not modify code, tests, configuration, behavior, or VCPS records. If remediation is needed, report it and route a separate `REVIEW` or `BUG` workflow.

## Locate the VCPS source root

Use the Core-discovery checks from `adapters/codex/vcps-setup/SKILL.md` §0: find a VCPS source root containing non-empty `standard/VCPS.md`, `VERSION`, and the required workflow/helper files. The target repository and VCPS source root may differ. Run the helper commands below from that source root, with `--target` set to the target repository. If the source root or helper is missing, report `BLOCKED`; do not treat a missing check as a clean result.

Define the scope precisely (repository, component, or VCPS installation) and list exclusions. Inspect evidence and records directly. From the VCPS repository root, use the shared read-only helpers as applicable:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py evidence-inventory --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py gate-reference-check --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py orphan-check --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py baseline-history-check --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py record-history-check --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <path> [--scope-path <path> ...]
python3 adapters/claude-code/lib/vcps_evidence.py antigaming-diff-scan --target <repo>
python3 adapters/claude-code/vcps-setup/scripts/vcps_tool.py validate --target <repo>
```

Treat helper matches as candidates, not findings: verify scope, evidence freshness, legitimate exceptions, and cross-references yourself. `gate-reference-check` also surfaces a candidate inconsistency when a `PASS` gate cites `NOT_RUN`/`ERROR`/`INCONCLUSIVE` evidence (`VCPS-EVD-020`); inspect context instead of treating it as a verdict. `baseline-history-check` compares tracked baseline history with `HEAD`; new observations/additions still need provenance review, and no prior baseline at `HEAD` means no comparison was possible. `record-history-check` surfaces AG-011 candidates for edits to committed immutable evidence/gate/approval records and rewrites of recognized append-only histories; it only compares tracked Markdown beneath `.vcps/` and is not a verdict. A `matches_head: false` mismatch requires checking the evidence scope against actual changes; neither a mismatch nor the absence of a flag establishes freshness by itself. Re-derive gate applicability and risk/invariant paths from Core; helpers do not make those judgments. Never re-run verification and report its result as an audit finding. `audit`'s `validate` invocation is read-only.

Review `.vcps/findings/` classifications directly: an `EVIDENCE_GAP` cannot be RESOLVED without evidence, a `DEFECT` cannot be reclassified without reproduction, and HIGH-or-higher `RISK_ACCEPTED` requires HC-08. `antigaming-diff-scan` surfaces filename-based `AG-001` candidates when a test-like tracked path is deleted or moved out of the test tree in the staged/unstaged diff against HEAD; review the complete diff. For anti-gaming and orphan results, inspect the relevant diff/record; matches are candidates only and may have valid exceptions.

Report scope, coverage as numerator/denominator with evidence basis, each gap and classification issue, anti-gaming candidates, and explicit conformance `FULL`, `PARTIAL`, or `NOT_CONFORMANT`. Never claim FULL while a discovered gap is unlisted.

Codex must run with `sandbox_mode = "read-only"` for this skill. The read-only instruction alone cannot enforce this; if the runtime mode cannot be confirmed, disclose the limitation and do not run any command capable of mutation. See `../references/capability-mapping.md`.

---
name: vcps-bug
description: Fix a reported incorrect behavior with reproduction before the change and confirmed regression evidence after, per the VCPS BUG workflow. Use for a specific symptom, not a general area review.
---

# VCPS bug

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute `workflows/bug.md` in full. Establish intended behavior at Gate 1, then reproduce the reported defect with `E2` or stronger evidence before proposing a fix. If reproduction fails, record `EVIDENCE_GAP (INCONCLUSIVE)` and stop; do not fix a guessed cause.

## Locate the VCPS source root

Use the Core-discovery checks from `adapters/codex/vcps-setup/SKILL.md` §0: find a VCPS source root containing non-empty `standard/VCPS.md`, `VERSION`, and the required workflow/helper files. The target repository and VCPS source root may differ. Run the helper commands below from that source root, with `--target` set to the target repository. If the source root or helper is missing, report `BLOCKED`; do not treat a missing check as a clean result.

Classify risk from touched paths and impact, never diff size. Follow the applicable Gate 2, Gate 3, Gate 4, and Gate 5 requirements. A reproduced defect SHOULD get a regression test (REQUIRED at L3/R3 unless HC-08 accepts the gap). For `VCPS-G4-031`, prove the regression test fails on the parent revision and passes on the fix revision, using an isolated worktree when practical. Record both results. Security exposure requires Gate 5 and may need HOTFIX routing if live.

Optional shared checks from the VCPS repository root:

```sh
python3 adapters/claude-code/lib/vcps_evidence.py evidence-inventory --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py orphan-check --target <repo>
python3 adapters/claude-code/lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <path> [--scope-path <path> ...]
```

These helpers return facts/candidates only. Run project tests directly as normal commands after checking their exact effects; never hide arbitrary project command execution inside a pre-approved helper. Before any mutation, establish `approval_policy = "untrusted"` or a trusted rules file that prompts for the intended writes/commands. This is not enforceable by the skill itself. See `../references/capability-mapping.md`.

Never size down risk because a fix is one line. Never claim regression evidence without an observed parent failure and fix pass. A `RESOLVED` finding needs the evidence tier required by the project level plus regression evidence; the fix alone does not restore a feature lifecycle state past `CODED`.

If reproduction instead exposes missing or undefined requirements, return to Gate 1 and assess FEATURE routing. If fix scope grows beyond the report, use HC-13. A regression test that passes on the parent is not evidence of this fix.

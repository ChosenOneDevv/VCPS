---
name: vcps
description: Classify a development request into its VCPS workflow and check mechanical risk escalation. Use for governed development work when the user has not already invoked a specific workflow or vcps-setup.
---

# VCPS workflow router

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

Execute the intent-classification contract in `workflows/README.md` for the current target repository. This skill classifies and routes; it does not itself execute the selected workflow. Read the governing workflow after classification and follow it directly.

## Locate the VCPS source root

Use the Core-discovery checks from `adapters/codex/vcps-setup/SKILL.md` §0: find a VCPS source root containing non-empty `standard/VCPS.md`, `VERSION`, and the required workflow/helper files. The target repository and VCPS source root may differ. Run the helper commands below from that source root, with `--target` set to the target repository. If the source root or helper is missing, report `BLOCKED`; do not treat a missing check as a clean result.

Before forming an intent opinion, read `workflows/README.md`, `standard/risk-model.md` §5, `workflows/tiny.md`, and `workflows/hotfix.md`. Inspect the actual diff or identify plausible touched paths. Run the shared mechanical checks before classification, from the VCPS repository root:

```sh
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [--touched-path <path> ...]
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py project-context --target <repo>
python3 adapters/claude-code/vcps-router/scripts/vcps_router.py segmentation-scan --target <repo> --touched-path <path> [--touched-path <path> ...]
```

Run segmentation-scan when work may be part of a related sequence. `forced_r3: true` sets a risk floor that wording or small diff size cannot lower. Project `critical_domains` are places to investigate, not keyword-based escalation rules. Treat each helper result as raw evidence and make the workflow/risk judgment yourself. If the helper is unavailable or fails, disclose that gap and do not treat failure as a clean result.

Classify exactly one of `FEATURE`, `REVIEW`, `BUG`, `TINY`, `HOTFIX`, `AUDIT`, `RELEASE`. `SETUP` goes to `vcps-setup`; if no VCPS installation exists, state that and route to setup. Do not accept “tiny” based on wording if R3 is forced or logic, access control, external calls, schema, or invariant enforcement paths are involved. Do not accept “hotfix” without confirmed live production impact. A request spanning intents must be split or handled under the stricter complete workflow, with the choice explained. `AUDIT` remains read-only; remediation means another workflow.

State the classification, touched-path and helper evidence, risk class, and any correction to the user's framing. Then read and follow `workflows/<intent>.md`. Never claim this router executed that workflow. If `.vcps/` artifacts exist, maintain the applicable work-item records under `templates/contract.md` as the workflow proceeds.

## Codex execution boundary

Codex's default `workspace-write` sandbox may permit repository writes without a per-write prompt. Before any mutating workflow, establish that `approval_policy = "untrusted"` is active or that the repository's trusted `.codex/rules/*.rules` has a `decision = "prompt"` rule covering the intended mutating commands. If this cannot be established, stop before mutation and report the gap. Do not treat this skill's instructions as an enforcement mechanism. See `../references/capability-mapping.md`.

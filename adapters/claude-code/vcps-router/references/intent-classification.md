# Intent/risk-escalation mapping (Claude Code adapter — informative)

This document resolves `OQ-011` in `standard/open-questions.md`: how
Core's generic intent-classification and risk-escalation contract
(`workflows/README.md` `VCPS-WF-001/002/003`, `standard/risk-model.md`
`VCPS-RISK-041/045`) maps onto *this specific agent's* execution
primitives, mirroring `OQ-005`'s existing resolution for the setup
adapter's orchestration mapping.

**This mapping is adapter-layer, not Core.** Per `standard/VCPS.md`
`VCPS-CORE-001`, nothing here creates a new Core requirement. A different
adapter (Codex or otherwise) MAY map these concepts differently, provided
it still satisfies `VCPS-WF-001/002/003` and `VCPS-CORE-003`.

## Why a separate mechanical helper from `/vcps-setup`'s

`vcps_router.py` duplicates `vcps_tool.py`'s small strict-YAML-loading
core rather than importing it across the sibling skill directory. Each
adapter component (`vcps-setup`, `vcps-router`) remains independently
installable — a project that only ever runs `/vcps-setup` and never
`/vcps` (or vice versa, once Phase D workflow executors exist) should not
need both directories present for either to work. This trades a small
amount of duplication for not coupling two otherwise-independent skills'
installation footprints together.

## What is mechanical vs. judgment here

| Concept | Mechanical (helper script) | Judgment (model) |
|---|---|---|
| "Does this touch a registered invariant's enforcement path?" (`VCPS-RISK-041`) | Yes — exact/prefix path match against `.vcps/invariants.md`, `escalation-check` subcommand. This is Core's own rule stated as a mechanical test, not an adapter shortcut. | Whether the *touched-path list itself* is complete and accurate (the script only checks what it's given). |
| "Does this touch a critical domain?" (`VCPS-RISK-001/002`) | No — deliberately not attempted. `VCPS-RISK-002` explicitly forbids keyword/domain-name-only classification. | All of it: tracing the actual impact path before citing a domain as relevant. `project-context` only surfaces the raw domain list as candidates to investigate. |
| "Is this part of a larger segmented change?" (`VCPS-RISK-045`) | Partial — `segmentation-scan` finds existing work-items whose recorded `scope.files` overlap the new touched paths. | Whether that overlap means "same logical unit of work" (branch/ticket lineage, intent, timing) the script has no visibility into. |
| Primary intent (`FEATURE`/`REVIEW`/`BUG`/`TINY`/`HOTFIX`/`AUDIT`/`RELEASE`) | No. | Entirely the model's job, per `VCPS-WF-001`. No helper subcommand classifies intent — doing so would risk exactly the kind of agent-specific Core-logic duplication `VCPS-CORE-001`/`003` exist to prevent, and intent classification is inherently a natural-language judgment, not a deterministic fact. |

## Independence from `/vcps-setup`'s mode detection

`/vcps-setup`'s `detect` subcommand answers "what installation mode is
this repository in" (`NEW`/`ADOPT`/`UPGRADE`/`REPAIR`/resume/already-
complete) — a question about VCPS's own installation state. `/vcps`'s
`escalation-check`/`project-context`/`segmentation-scan` answer a
different question entirely: "given VCPS is already installed (or not),
what does this one proposed change's risk floor look like." A repository
with no `.vcps/` root is a valid (if uninformative) input to every
`/vcps` subcommand — see each subcommand's `"has_vcps": false` case —
whereas it is the *entire question* `/vcps-setup detect` exists to answer.
`/vcps` does not re-implement or shadow `/vcps-setup`'s mode detection.

## Known gaps, honestly stated

- No capability currently exists to automatically discover "the files this
  request will touch" before any code is written — `SKILL.md` SS1 asks
  the model to read enough of the relevant area to name real candidate
  paths, which is a judgment call, not a mechanical one. A future revision
  MAY add a lightweight static grep-based candidate finder, but that
  would itself need to avoid silently becoming a second, weaker form of
  impact-path tracing that competes with `VCPS-RISK-001`'s actual
  requirement.
- `segmentation-scan` has no concept of git branch/ticket lineage; it is
  a pure file-overlap query across existing work-item records. Model
  judgment about whether two overlapping work items are really "the same
  logical unit of work" (`VCPS-RISK-045`) is unverified by this adapter
  beyond that raw overlap signal.
- As with `/vcps-setup`, this component has `TESTED_STRUCTURALLY` and
  `TESTED_SIMULATED` evidence only as of this revision (see
  `evaluation/vcps-router.md`) — no `LIVE_ADAPTER_EXECUTION` yet.

# Project Artifacts

This document owns the set of VCPS artifacts a project maintains and their
minimum content. Concrete file formats and schemas belong to the templates
layer (`templates/`) and are not yet defined.

## 1. Location

**VCPS-ART-001.** A project MUST keep VCPS artifacts under a single
repository-relative root directory. The RECOMMENDED root is `.vcps/`. The root
MUST be discoverable from a fixed entry file (RECOMMENDED: `.vcps/project.yaml`).
A human-facing pointer outside that root MAY exist but MUST NOT own project
state.

**VCPS-ART-002.** VCPS artifacts MUST be committed to version control with the
code they describe, except files explicitly designated as local scratch.

## 2. Artifact set

| Artifact | Minimum content | Owning rules |
|----------|-----------------|--------------|
| **Config** | `vcps_version`, project/component levels, artifact root layout version, toolchain commands (build, test, lint, typecheck, etc.), CI mapping, project-local policies | [versioning.md](versioning.md), [levels.md](levels.md) |
| **Risk profile** | Dimension ratings with impact-path evidence, per component | [risk-model.md](risk-model.md) |
| **Invariant registry** | `INV-*` entries | VCPS-RISK-030 |
| **Feature records** | Per [lifecycle.md §4](lifecycle.md#4-feature-record) | VCPS-LC-020 |
| **Finding records** | Per [classifications.md §5](classifications.md#5-finding-record) | VCPS-CLS-040 |
| **Evidence records** | Per [evidence-model.md §4](evidence-model.md#4-evidence-record) | VCPS-EVD-030 |
| **Gate records** | Per [gates/README.md §6](gates/README.md#6-gate-record) | VCPS-GATE-050 |
| **Checkpoint records** | Per [human-checkpoints.md §3](human-checkpoints.md#3-checkpoint-record) | VCPS-HC-020 |
| **Pre-authorizations** | Per [human-checkpoints.md §4](human-checkpoints.md#4-pre-authorization) | VCPS-HC-030 |
| **Baseline** | Revision, every configured check with result, environment | [../workflows/setup.md](../workflows/setup.md) |
| **Legacy gap registry** | Filtered set of legacy `EVIDENCE_GAP`/`DEFECT` finding records from setup, with touch rules; no duplicate status owner | [../workflows/setup.md](../workflows/setup.md) |
| **Setup state** | Current setup mode, stage, stage outcomes, pending checkpoints | [../workflows/setup.md](../workflows/setup.md) |
| **Work log / handoff** | Per VCPS-PORTABILITY-006 | [portability.md](portability.md) |

**VCPS-ART-010.** Records MUST be append-friendly: changing a status or
classification adds a history entry rather than erasing prior values
(see `AG-011`).

**VCPS-ART-011.** Each record type MUST have a stable identifier scheme.
RECOMMENDED prefixes: `FEAT-`, `FND-`, `EVD-`, `GATE-`, `HCR-` (checkpoint
record), `INV-`, `PREAUTH-`.

**VCPS-ART-012.** Artifacts MUST be machine-validatable once schemas exist in
the templates layer. Until then, artifacts MUST at least contain the minimum
fields named by their owning rules.

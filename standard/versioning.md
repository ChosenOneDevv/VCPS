# Versioning

This document owns versioning of the VCPS specification and of project
installations.

## 1. Specification version

**VCPS-VER-001.** The VCPS specification is versioned with Semantic Versioning
2.0.0. The authoritative version is the content of [`/VERSION`](../VERSION).
The current version is `1.0.0`.

**VCPS-VER-002.** Version increments:

| Change | Increment |
|--------|-----------|
| Adds or strengthens a `MUST`/`MUST NOT`, changes an enumerated value, removes or renames an artifact field | MAJOR (MINOR while `0.x`) |
| Adds a `SHOULD`/`MAY`, new optional artifact field, new checkpoint or workflow that does not invalidate existing records | MINOR |
| Clarification with no change to conformance outcomes | PATCH |

**VCPS-VER-003.** A version with a pre-release suffix (e.g. `-draft`) carries no
stability guarantee. See VCPS-CORE-031.

**VCPS-VER-004.** Each release of the specification SHOULD include an upgrade
note listing changed requirement IDs and required artifact migrations.

## 2. Project installation version

**VCPS-VER-010.** A project MUST record the specification version it implements
(`vcps_version`) and the artifact layout version in its config artifact.

**VCPS-VER-011. (Drift)** Setup and audit MUST compare the project's
`vcps_version` with the version of the VCPS specification being executed and
report one of:

| Relation | Meaning | Required action |
|----------|---------|-----------------|
| `EQUAL` | Same version. | None. |
| `BEHIND` | Project older than executor. | Setup MAY run `UPGRADE`. Until upgraded, the executor MUST apply the project's recorded version where behavior differs, or report the difference as an `EVIDENCE_GAP`. |
| `AHEAD` | Project newer than executor. | Executor MUST NOT modify VCPS artifacts; it MUST report and stop for human decision. |
| `UNKNOWN` | No or malformed version. | With no canonical `.vcps/` root, Setup MUST enter `NEW` or `ADOPT` per VCPS-SETUP-001; with a canonical root or malformed existing config, it MUST enter `REPAIR`. |

**VCPS-VER-012.** An upgrade MUST NOT silently change a project's level,
invariants, accepted risks, or checkpoint decisions. Where a new version
changes the meaning of existing records, the upgrade MUST surface each
affected record for review.

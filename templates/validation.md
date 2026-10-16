# Structural validation contract

Validation first applies JSON Schema 2020-12 to `project.yaml` or extracted
Markdown frontmatter, then performs these cross-record checks. This document
defines the required behavior; actual reference coverage is tracked, with
gaps called out, in
[`../evaluation/validation-contract-coverage.md`](../evaluation/validation-contract-coverage.md).

1. Parse one UTF-8 YAML 1.2 safe document. Reject duplicate keys,
   aliases, merge keys, custom tags, non-string keys, implicit timestamp
   objects, unknown fields, and Markdown without frontmatter/body.
2. Select schema by fixed path or record directory. Require exact supported
   schema/layout versions before writes. Reject absolute paths, path
   traversal, symlinks escaping the repository, and credentialed URLs.
   Resolve all nonpending references. A pending baseline is valid only
   before Stage 8; COMPLETE requires no pending artifacts.
3. Enforce ID format, repository-wide uniqueness, stable frontmatter identity,
   and expected type for every reference. Resolve singleton paths and
   all IDs; withdrawn IDs remain reserved.
4. Require one PROJECT profile and at most one profile per component,
   with D1–D9 each present exactly once. Derive project/component levels
   from risk ratings per VCPS-RISK-020/021;
   compare with `project.yaml`. Check every active invariant exists and
   every nonzero dimension has impact-path evidence. Removing an active
   invariant requires a recorded risk decision and applicable HC-08.
   Evidence-policy overrides must never lower a Core minimum. Validate commands,
   CI paths/jobs, and component paths as repository-relative.
5. Check finding classification/status transitions per VCPS-CLS-001/010/030.
   LEGACY starts OPEN and has a touch rule. RESOLVED requires remediation
   evidence; KNOWN_LIMITATION has RISK_ACCEPTED status and requires human
   acceptance. Original
   observation and prior states remain historically recoverable.
6. Check evidence provenance per VCPS-EVD-001…061: E0 cannot PASS; E1 is
   inspection, E2 local execution, E3 retrievable CI run on exact revision,
   E4 external actor/action, E5 production observation. Evidence used for a
   gate or lifecycle promotion cannot have an UNKNOWN revision. A mock/substitute
   cannot prove a stronger target. NOT_RUN/ERROR/INCONCLUSIVE never PASS.
   Recompute staleness from revision, scope, dependencies, and environment;
   do not trust a stored freshness label.
7. Require a risk class before a change gate can PASS. Check gate
   applicability/outcome against Core matrix, level, risk,
   evidence tier/fidelity, blocking findings, independence, and revision.
   A dirty-worktree revision needs a reconstructable snapshot. Re-evaluation
   leaves old gate records; current work item references latest valid one.
   Gate 6 needs required Gates 1–5 and affirmative HC-10 where applicable.
8. Check FEATURE lifecycle transitions per VCPS-LC-001/002/010. Work-item
   acceptance projection equals linked HC-14 decision. Release go/no-go
   equals linked HC-10. AUDIT cannot claim implementation gate outcomes.
9. Check baseline against version-control history: original revision,
   observation IDs, and evidence refs never change. Additions need
   pre-existing evidence and a new observation ID; resolutions link a RESOLVED finding and original
   observation. Every discovered check has evidence, including skipped,
   blocked, erroneous, or inconclusive runs. No inherited failure is
   automatically RISK_ACCEPTED.
10. Only a human actor may approve. Decisions are APPROVED, REJECTED, or
    APPROVED_WITH_CONDITIONS and are exact-scope/revision bound.
    Pre-authorization obeys VCPS-HC-031, has bounded impact and expiry.
    Rejection and silence never pass a gate.
11. Reject secret-like keys/values, credentials, unredacted personal data,
    machine-specific absolute paths, or agent-private IDs in authoritative
    fields. Heuristics flag possible secrets for human review; they cannot
    prove absence. External evidence needs durable locator and Core-required
    repository summary.
12. Check `VCPS.md` and agent pointers contain no conflicting canonical
    values. Handoff refs must resolve, and each pending checkpoint in
    project/work state must have action/scope in the current handoff so
    another agent/human can resume.

Report path, field, requirement ID, and repair category for each error.
Validation never silently repairs, deletes, or rewrites project artifacts.

## Setup state validation

13. For project schema `0.2.0`, validate active and archived plan hashes as
   SHA-256 of UTF-8 canonical JSON (sorted keys, compact separators, UTF-8
   characters unescaped, excluding `sha256`). The active plan and every archived plan have distinct hashes;
   each stage event's `plan_hash` resolves to exactly one. `plan_history` is
   append-only and never includes the active plan. Validate plan path sets
   against the actual pre-mutation dry-run and budget; every event mutation
   path must be allowed by its referenced plan. Stage 4 or later requires
   a non-null plan and stage events; a null plan is allowed only during
   explicit `0.1.0` migration before Stage 4.
14. Compute a stage input fingerprint over lexicographically sorted
   repository-relative `input_scope` paths, expanding a directory recursively
   without following symlinks. A directory expansion excludes `.vcps/`
   (including its VCS status) unless a specific `.vcps/` path is explicitly
   listed as an input; this prevents later setup records from invalidating
   earlier repository-discovery stages. Hash each path's relative name, existence,
   file type, content hash or submodule pointer, and VCS state; serialize
   as UTF-8 canonical JSON and SHA-256 it. Exclude the stage's output paths;
   when `.vcps/project.yaml` is in scope, canonicalize it without
   `installation.plan`, `plan_history`, `stage_events`, `history`,
   `stage`, and `status` to prevent self-invalidation. Include all other
   config/governance fields and external edits.
   The hashed value is the canonical JSON array (same canonicalization as the
   plan hash) of one object per expanded path, sorted by UTF-8 path bytes,
   with exactly the keys `path`, `exists` (boolean), `type` (`file`,
   `symlink`, `submodule`, or `absent`), `digest`, and `vcs`. `digest` is the
   file's SHA-256, the SHA-256 of a symlink's target string, the submodule
   commit, or `null` when absent. `vcs` is the Git porcelain v1 `XY` code
   (`"  "` tracked and clean, `"??"` untracked, `"!!"` ignored explicit path)
   or `"NA"` without VCS. Directory expansion enumerates tracked plus
   untracked non-ignored files and never `.git/`; ignored files are omitted
   unless named explicitly. A bare `.` scope also covers paths created later
   by the same setup (e.g. the root `VCPS.md` pointer), so executors SHOULD
   record enumerated paths for Stages 1–3 rather than `.`.
   A changed input appends INVALIDATED and re-evaluates dependent stages;
   it does not delete old evidence. The stage journal is append-only:
   later COMPLETED events supersede earlier attempts for that stage.
   Check `installation.stage` is the earliest incomplete/invalidated stage
   (null only when all eleven are complete), and status is justified by
   stage events and unresolved findings. A planned output without a
   completing event is incomplete; a completing event whose output is absent
   or malformed is inconsistent and routes to REPAIR/resume. Do not silently
   delete or adopt unreferenced output files.

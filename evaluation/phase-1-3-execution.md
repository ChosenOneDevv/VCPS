# Phase 1–3 Delivery Record

Date: 2026-10-07  
Scope: first-install UX, deterministic validation/CI, and adapter installer
lifecycle. This record covers the working-tree implementation and local
structural/simulated evidence; it is not a hosted CI run, live agent acceptance,
Core certification, or release approval.

## Phase status

| Phase | Status | Delivered | Exit evidence and remaining boundary |
|---|---|---|---|
| 1 — First install | **COMPLETE for checkout installation** | Copy/symlink preflight, read-only `--plan`, automatic sibling dependency expansion, one-command install for Claude Code and Codex, `--verify`, and updated quick start | Owner confirmed 2026-10-07 that the repository is not published and checkout installation is sufficient. Fresh temporary-target install and verification pass for copy, symlink, Codex and vendored Core. Command: `python3 adapters/install.py --adapter <claude-code|codex> --target <project>`. |
| 2 — Validation and CI | **PARTIAL** | One top-level runner, GitHub Actions Python 3.10–3.14 matrix, pinned Draft 2020-12 schema engine, schema meta-validation and worked-example validation; journal stage projection and pending-baseline rules are checked; runner emits revision-bound JSON reports even after test failures/timeouts | Local runner passes on Python 3.14.7. The workflow is configured to upload a report per commit/Python version, but has not run on a hosted runner from this checkout, so no E3 result is claimed. Remaining matrix gaps include full conformance and human/history-derived rules. |
| 3 — Installer lifecycle | **COMPLETE for supported checkout scopes** | Manifest ownership, copy/symlink install, verification, upgrade, repair, uninstall, conflict protection, staging and rollback for installer file operations; project-schema migration saves exact pre-migration bytes and offers guarded rollback | Local cases cover fresh install, plan parity, verify, repair, modified-path refusal, global Codex install/uninstall, successful upgrade, installer commit failure rollback, schema migration failure preservation, successful schema rollback and refusal after user edits. Codex's helper subtree is vendored from the same source and byte-verified. |

## Implemented commands

Run the entire structural/simulated suite from the repository root:

```sh
python3 evaluation/run_all.py
```

Check the Draft 2020-12 schemas and example records directly:

```sh
python3 evaluation/check_schemas.py
```

Install Claude Code skills into a target repository in one checkout command:

```sh
python3 adapters/install.py --adapter claude-code --target /path/to/project --mode copy --vendor-core
```

Install Codex skills into a target repository:

```sh
python3 adapters/install.py --adapter codex --target /path/to/project
```

The helper runtime requirements are pinned in
[`../adapters/claude-code/lib/requirements.txt`](../adapters/claude-code/lib/requirements.txt).
They are needed to run setup/schema/evidence helpers, not to execute the
stdlib-only adapter installer.

## Local evidence

Recorded locally for this delivery:

- `evaluation/run_all.py`: **8/8 suites pass** on Python 3.14.7; a machine-readable report was written and parsed successfully. The local report correctly identifies the current worktree as dirty, so it is not E3 evidence.
- `evaluation/check_schemas.py`: 11 schemas accepted by Draft 2020-12; the worked example is accepted.
- Installer simulation: 3 structural and 25 simulated checks pass, including global install, upgrade and injected rollback cases.
- Claude setup simulation: 21 structural checks and 82 simulated checks pass, including declared stage mutation paths, nested reference resolution, Stage 8 baseline timing, no-pending-artifact completion, journal stage consistency and guarded migration rollback.
- Evaluation unit suite: 36 tests pass (includes report success, failure, and timeout cases).

Even with a green local run, Phase 2 does not have the hosted E3 result required
by the original exit card.

## Deferred conformance and distribution work

The schema engine validates the full declared JSON Schema vocabulary, while
`vcps_tool.py` also performs mechanical cross-record checks. Neither is a
substitute for full Core conformance. Work remains for ambiguous or
human-judgment rules, including recovered historical gate applicability text,
withdrawn-ID reservation based on authoritative history, lifecycle transition
interpretation where Core wording is ambiguous, prose pointer consistency,
and human checkpoint authority. These are listed in the Phase 0 recovery
register and Core open questions; implementation must not guess new normative
meaning.

The installer is delivered from a local VCPS checkout. To offer a remote
single-command bootstrap, the project owner must supply or publish the
canonical repository/release URL and choose its update channel. No URL is
fabricated in this repository. Codex helper portability also remains a follow-up: its
repository-relative source paths currently require the installer to vendor
the helper subtree.

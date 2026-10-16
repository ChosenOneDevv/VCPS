# Worked example: `project/`

A complete, internally consistent `.vcps/` record set for a small
fictitious project (`todo-cli`: a shared household todo-list CLI with
background sync between devices), illustrating every record type in
[`templates/contract.md`](../contract.md) and validating structurally
against every schema in [`templates/schemas/`](../schemas/).

## Provenance

**`NEW_CANONICAL_RECONSTRUCTION`, authored 2026-10-06.** The original
worked example was lost to the repository corruption documented in
`evaluation/claude-code-adapter.md` and `evaluation/completion-roadmap.md`
Phase B (every file under `templates/examples/project/` was found 0
bytes, with no surviving bytes or audit-document quotation to recover
from). This is **not** a recovery of the original example's content,
narrative, or project choice — it is a fresh, deliberately small example
built mechanically from the intact `templates/contract.md` and
`templates/validation.md` contract and the Core documents each record
type cites as its owner. Do not treat any identifier, name, or scenario
detail here as matching whatever the original example contained.

## What it demonstrates

- A `L2` project (one dimension, `D1`, rated `2`: a background-sync
  defect can silently revert a completed authoritative record).
- A full `SETUP` `ADOPT` run, all eleven stages `COMPLETED`, ending
  `SETUP_STATUS: COMPLETE` — including the Stage-4 plan hash, computed
  for real by `adapters/claude-code/vcps-setup/scripts/vcps_tool.py
  plan-hash` and reproducible by any reader (see the comment at the top
  of `project/.vcps/project.yaml`).
- A legacy `EVIDENCE_GAP` (no CI) discovered during setup
  (`FND-...0001`), created `OPEN` as required, later escalated by its
  own touch rule when a fix touched its enforcement path, and resolved
  via a real `HC-08` decision (`HCR-...0009`) rather than silently
  accepted.
- A `REVIEW` (`REV-...0004`) that reconstructs intended behavior from an
  invariant and finds a real deviation (`FND-...000c`, classified
  `DEFECT`, severity `CRITICAL` because it violates a registered
  invariant), re-routed to a `BUG` rather than fixed in place.
- A `BUG` (`BUG-...0005`) classified `R3` because it touches a critical
  invariant's enforcement path (`VCPS-RISK-041`) even though the diff
  itself is three lines, verified at the `L2`/`R3`-required `I2`
  independence mode (`GATE-...0008`), with real regression evidence
  (`EVD-...000d`).
- A `FEATURE` (`FEAT-...0003`) that reaches `VERIFIED` but not
  `ACCEPTED` — an honest, non-fabricated lifecycle state — and accepts
  one low-severity `KNOWN_LIMITATION` (`FND-...000e`) along the way
  without that blocking `VERIFIED` at `L2`.
- A `RELEASE` (`REL-...0006`) that stays `BLOCKED` with `gate6_ref: null`
  because no `HC-10` decision has been recorded yet — deliberately not
  fabricating a Gate 6 `PASS` the release hasn't actually received.
- A `HANDOFF` (`HND-...0007`) that references, rather than duplicates,
  that pending checkpoint so a different agent or human could resume
  without replaying any conversation.
- A `TINY` work item (`WORK-...000a`) correctly classified `R0`/`I0`.
- A pre-authorization (`PREAUTH-...000f`) correctly bounded (`HC-11`
  only, explicit expiry, excluded from the checkpoints `VCPS-HC-031`
  forbids pre-authorizing).

## Validating it yourself

```sh
python3 adapters/claude-code/vcps-setup/scripts/vcps_tool.py validate \
  --target templates/examples/project
```

This exercises the adapter's real (partial) mechanical validator: strict
YAML parsing, frontmatter presence, ID uniqueness/format, and plan-hash
recomputation. Full JSON Schema 2020-12 validation against
`templates/schemas/*.json` (required keys, enums, types, unknown-field
rejection — Phase E of `evaluation/completion-roadmap.md`) is not yet
wired into `vcps_tool.py`; every record in this example was checked
against its schema during authoring using a disposable subset validator
in this session's scratch directory, not shipped as part of this
repository.

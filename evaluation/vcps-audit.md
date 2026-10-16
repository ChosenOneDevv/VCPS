# Evaluation record: Claude Code AUDIT workflow (`/vcps-audit`)

- Adapter version: `0.1.0-draft.4` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/audit.md`
- Python 3.14.7, PyYAML 6.0.3, git 2.55.0
- Invocation: `/vcps-audit [scope description]`
- Date: 2026-10-06

## Provenance

New component. Roadmap Phase D's first slice (AUDIT; see
`evaluation/vcps-review.md` for the other half of this slice).
`AUDIT`'s Core workflow (`workflows/audit.md`) is the most mechanizable
of the seven non-`SETUP` workflows: three of its seven steps (evidence
inventory, gate-outcome review, installation consistency) are genuinely
checkable facts, not natural-language judgment. This motivated building
a shared mechanical helper (`adapters/claude-code/lib/vcps_evidence.py`,
its own evaluation covered by `adapters/claude-code/lib/tests/run_tests.py`,
not duplicated in this record) rather than a thin wrapper with nothing to
test.

## Execution classes

Same definitions as `evaluation/claude-code-adapter.md`.

## Scope, stated honestly

`workflows/audit.md` `VCPS-WF-AUDIT-001` is absolute: this skill MUST NOT
modify anything. `allowed-tools` pre-approves only `Read`/`Grep`/`Glob`,
read-only `git` subcommands, and the shared lib's nine read-only
subcommands — no `Write`/`Edit` anywhere, confirmed by `S3` below.

The mechanical half of this workflow (evidence staleness candidates,
gate-record internal consistency, orphaned references, anti-gaming
literal-pattern candidates) is real and tested
(`adapters/claude-code/lib/tests/run_tests.py`, 4 structural + 39
simulated, all passing). The judgment half (classification review,
anti-gaming semantic review beyond literal patterns, the actual
conformance statement) is entirely the model's, as `workflows/audit.md`
itself requires.

## Results

Command: `python3 adapters/claude-code/vcps-audit/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No `Write`/`Edit` anywhere in `allowed-tools` | STRUCTURAL_TEST | PASS | Direct structural proof of `VCPS-WF-AUDIT-001` compliance at the tool-permission level. |
| S4 | References `VCPS-WF-AUDIT-001` explicitly | STRUCTURAL_TEST | PASS | |
| S5 | Every `allowed-tools` script path resolves to a real file | STRUCTURAL_TEST | PASS | **Caught a real authoring defect before this record was written**: an initial draft wrote `${CLAUDE_SKILL_DIR}/../../vcps-setup/scripts/vcps_tool.py` (two levels up), which does not resolve — `vcps-setup/` is a sibling of `vcps-audit/`, one level up (`${CLAUDE_SKILL_DIR}/../vcps-setup/...`). Fixed before commit; this test is what caught it, not manual inspection. |
| S6 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | Same fix as S5, checked against the instructional prose too, not just the `allowed-tools` line. |
| S7 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S8 | Setup tool exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S9 | Never claims to re-run verification as an audit finding | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 9/9 pass. See
`adapters/claude-code/lib/tests/run_tests.py`'s own 4 `STRUCTURAL_TEST` +
39 `SIMULATED_EXECUTION` for the mechanical helper this skill actually
calls — not re-counted here to avoid double-reporting the same evidence
under two records.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** No `claude -p` run of this skill has been attempted.

## Known limitations and unresolved evidence

- No live run. `disable-model-invocation: true` reflects this.
- Classification review, the full anti-gaming semantic review beyond
  literal patterns, and the final conformance statement are entirely
  model judgment with zero mechanical coverage — by design, per
  `workflows/audit.md` itself, not an oversight.
- `orphan-check`'s reference resolution does not know about legitimately
  withdrawn/reserved IDs that a future retention policy might still
  consider valid; every result is a candidate.
- This skill's Step 6 ("installation consistency") reuses
  `vcps_tool.py validate`, which is still the partial mechanical
  validator from the setup adapter (roadmap Phase E remains open: full
  JSON-Schema validation against `templates/schemas/*.json` is not wired
  into either tool yet).

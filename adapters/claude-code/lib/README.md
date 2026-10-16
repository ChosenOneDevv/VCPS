# Shared helper library (Claude Code adapter)

`vcps_evidence.py` is shared by the `/vcps-audit` and `/vcps-review`
skills (`adapters/claude-code/vcps-audit/`, `adapters/claude-code/vcps-review/`).

## Runtime dependency

The shared helper requires PyYAML. Install the pinned dependency from this
directory with `python3 -m pip install -r requirements.txt`; the version pin
matches the upstream latest release verified for this audit. Do not silently
fall back to an unsafe or ad-hoc YAML parser if it is unavailable.

## Why this one is shared, unlike `vcps-setup`'s and `vcps-router`'s own helpers

`vcps_tool.py` and `vcps_router.py` each duplicate a small (~60-line)
strict-YAML-loading core rather than importing across sibling skill
directories, so either component stays independently installable. That
duplication is low-risk: it is generic YAML parsing, not Core-rule logic.

`vcps_evidence.py` is different. Evidence-staleness recomputation
(`VCPS-EVD-050/051/053`), cross-record reference resolution, and gate
internal-consistency checks are **Core-rule-specific logic**. A second,
independently-maintained copy of this logic in two skills risks the two
silently diverging on what "stale" or "orphaned" means — a real
specification-consistency defect, not mere code duplication. This
repository chooses to share one copy instead, accepting the resulting
installation coupling: both `vcps-audit/` and `vcps-review/` need this
`lib/` directory present alongside them (`${CLAUDE_SKILL_DIR}/../lib/`)
to function, unlike `vcps-setup`/`vcps-router`'s standalone components.

This is a deliberate, disclosed exception, not an oversight. A future
installer (roadmap Phase K) needs to know to vendor `lib/` whenever it
vendors `vcps-audit/` or `vcps-review/`.

## What this script does and does not decide

See the module docstring in `vcps_evidence.py` for the full mechanical/
judgment split. In short: it surfaces raw facts (a revision mismatch, an
unresolved reference, a literal anti-gaming pattern match, a deleted or
modified test-like path in the working diff, or an AG-011 history rewrite candidate)
and makes none
of the actual judgment calls those facts feed into.

# Contributing

VCPS Core is stable at `1.0.0`. Adapter and evaluation components remain
at different maturity levels; see [`evaluation/completion-roadmap.md`](evaluation/completion-roadmap.md)
and each layer's README before relying on a specific implementation.

## Before changing anything

1. Read [`standard/VCPS.md`](standard/VCPS.md), especially §4
   ("Architecture and layering") and its ownership map. VCPS is split into
   five layers (Core, Workflows, Templates, Adapters, Evaluation), each of
   which may depend only on the layers above it in that list.
2. Know which layer your change belongs to before writing anything. The
   most common mistake this project explicitly guards against
   (`VCPS-CORE-001`/`VCPS-CORE-003`) is leaking agent-specific or
   adapter-specific behavior into Core (`standard/`) or Workflows
   (`workflows/`), or an adapter quietly defining a second, divergent
   copy of a Core rule instead of executing the real one. If you are
   changing an adapter (`adapters/`) and find yourself restating or
   reinterpreting a Core requirement rather than citing and executing it,
   that is itself a defect to fix, not a pattern to continue.
3. If your change touches a normative requirement (anything with a
   `VCPS-<AREA>-<NNN>` ID), check whether it needs a
   [`standard/open-questions.md`](standard/open-questions.md) entry, and
   whether `standard/versioning.md`'s increment rules (below) mean it
   needs a version bump.

## What this project values in a change

These are drawn directly from how the existing history in this repository
is written, not aspirational:

- **Disclose provenance and confidence, don't just assert it.** Where a
  change is reconstructed, inferred, or uncertain, say so in the same
  place the change lives (a Recovery note, a limitations section, a
  commit message) — never silently upgrade an assumption to a stated fact.
- **Real evidence over narrative.** A claim that something works should
  be backed by an actual test run, not a description of what the code is
  expected to do. This repository's own test suites
  (`adapters/*/tests/run_tests.py`, `evaluation/tests/`) distinguish
  `STRUCTURAL_TEST` and `SIMULATED_EXECUTION` from genuine
  `LIVE_ADAPTER_EXECUTION` for exactly this reason — know which one your
  change's evidence actually is, and label it correctly rather than
  rounding up.
- **Don't fabricate or weaken verification.** See
  [`standard/anti-gaming.md`](standard/anti-gaming.md). A change that
  makes a check pass by relaxing what it checks, substituting a weaker
  test, or silently reclassifying a gap needs the exception protocol
  described there, not a quiet edit.
- **Name what you didn't do.** A "Known limitations" or "Not yet done"
  section next to a change is expected, not a sign the change is
  unfinished. Overclaiming completeness is treated as a worse outcome
  than disclosing a bounded scope.

## Running the test suites

Each adapter and the top-level installer ship their own test runner. Run the
full structural/simulated set with `python3 evaluation/run_all.py`, or run
the directly affected suite when iterating:

```
python3 adapters/claude-code/lib/tests/run_tests.py
python3 adapters/claude-code/tests/run_tests.py
python3 adapters/claude-code/vcps-router/tests/run_tests.py
python3 adapters/codex/tests/run_tests.py
python3 adapters/tests/run_tests.py
```

`python3 evaluation/check_schemas.py` also verifies all schema documents with
the pinned Draft 2020-12 implementation and validates the worked example.
CI runs the same checks on the supported Python matrix; live adapter behavior
is tracked separately and is not implied by a passing local/CI run.

Each prints `STRUCTURAL_TEST`/`SIMULATED_EXECUTION` pass counts and exits
nonzero on any failure. Add a regression test for anything you fix —
most of the defects on record in `evaluation/*.md` were caught exactly
this way, with the reproducing test kept afterward rather than discarded.

## Proposing a Core or Workflow change

Changes to `standard/` or `workflows/` are the highest-leverage and
highest-risk changes in this repository, since every adapter executes
them. Open an issue or discussion describing the requirement gap or
defect before sending a change, so the layering and wording can be
agreed on before an adapter is built against it.

## License and governance

This repository is licensed under [Apache License 2.0](LICENSE)
(`OQ-001`, [`standard/open-questions.md`](standard/open-questions.md)).
By submitting a contribution, you agree it is licensed under the same
terms (`CONTRIBUTING.md` itself doesn't need a separate CLA for that —
Apache-2.0 §5 already covers submitted contributions).

# Evaluation record: Claude Code router (`/vcps`)

- Adapter version: `0.1.0-draft.3` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `standard/open-questions.md` `OQ-011`
- Python 3.14.7, PyYAML 6.0.3
- Invocation: `/vcps <request description>`
- Date: 2026-10-06

## Provenance

New component, not a recovery of anything (no prior `/vcps` router ever
existed in this repository — `standard/open-questions.md` previously
stated plainly "No `/vcps` runtime router exists yet"). Built against the
intact `workflows/README.md` (`VCPS-WF-001/002/003`) and
`standard/risk-model.md` (`VCPS-RISK-041/045`), reusing the setup
adapter's established pattern: a thin dispatcher `SKILL.md` plus a
deterministic helper script that computes only genuinely mechanical
facts, leaving classification and impact-path judgment to the model.

## Execution classes

Same definitions as `evaluation/claude-code-adapter.md`:
`STRUCTURAL_TEST`, `SIMULATED_EXECUTION` (mechanical helper only, no model,
not a live pass), `LIVE_ADAPTER_EXECUTION` (a real `claude -p` run).

## Scope, stated honestly

This component classifies a request into one of the eight
`workflows/README.md` intents and checks it against the mechanical half
of Core's escalation contract. **It does not execute any of the seven
non-`SETUP` workflows** — no adapter-side executor for `FEATURE`/
`REVIEW`/`BUG`/`TINY`/`HOTFIX`/`AUDIT`/`RELEASE` exists yet (roadmap
Phase D). Its value today is the classification/escalation step itself,
plus a safety net against the specific failure mode
`standard/risk-model.md`/`workflows/README.md` name directly: a
trivially-worded request that actually touches a registered invariant's
enforcement path.

## Results

Command: `python3 adapters/claude-code/vcps-router/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | SKILL.md has YAML frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | `disable-model-invocation: true` present — this is a reference/development-phase component, not yet safe or complete enough to self-trigger (see "Known limitations"). |
| S3 | No blanket Write/Edit/bare-Bash pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Internal links resolve | STRUCTURAL_TEST | PASS | |
| S5 | Orchestration-mapping doc marks itself informative/non-Core | STRUCTURAL_TEST | PASS | |
| S6 | No vendor name in cited Core text | STRUCTURAL_TEST | PASS | |
| S7 | `vcps_router.py` exists | STRUCTURAL_TEST | PASS | |
| S7b | `vcps_router.py` compiles | STRUCTURAL_TEST | PASS | |
| S8 | `SKILL.md` honestly scopes itself (no claim of executing a workflow it doesn't) | STRUCTURAL_TEST | PASS | |
| S9 | Escalation note states the mechanical floor is never lowerable | STRUCTURAL_TEST | PASS | |
| S10 | `TINY`/`HOTFIX` misuse guidance present | STRUCTURAL_TEST | PASS | |
| S11 | `allowed-tools` `Bash` entries scoped to `git` read-only or this script's subcommands | STRUCTURAL_TEST | PASS | |
| 1 | No `.vcps/` root at all | SIMULATED_EXECUTION | PASS | `has_vcps: false`, `forced_r3: false`, no crash; note explicitly says this is "nothing to check yet," not "safe." |
| 2 | Direct enforcement-path hit | SIMULATED_EXECUTION | PASS | `forced_r3: true`, matched invariant cited. |
| 3 | **Undersell case** (roadmap Phase C's required completion criterion): trivially-worded change touching a payments invariant's enforcement path | SIMULATED_EXECUTION | PASS | `forced_r3: true` regardless of wording — the mechanical floor this adapter is supposed to provide. |
| 4 | Unrelated file | SIMULATED_EXECUTION | PASS | `forced_r3: false`; non-empty disclaimer note present (absence of a match is not proof of safety). |
| 5 | Directory-prefix enforcement path | SIMULATED_EXECUTION | PASS | A file under a directory-level enforcement path still matches. |
| 6 | `WITHDRAWN` invariant excluded | SIMULATED_EXECUTION | PASS | A withdrawn invariant's enforcement path does not force `R3`. |
| 7 | Invariant not in `applicable_invariants` excluded | SIMULATED_EXECUTION | PASS | |
| 8 | `project-context` surfaces domains as candidates only | SIMULATED_EXECUTION | PASS | No verdict/escalation field is set by this subcommand — `VCPS-RISK-002` compliance (no keyword-only classification). |
| 9 | `segmentation-scan` finds only genuinely overlapping prior work item | SIMULATED_EXECUTION | PASS | |
| 10 | `segmentation-scan` with no overlap | SIMULATED_EXECUTION | PASS | Empty list, not an error. |
| 11 | Malformed `invariants.md` (duplicate key) | SIMULATED_EXECUTION | PASS | Reported as a tool error (nonzero exit, `error` key), never a silent "no escalation needed" false negative. |
| 12 | Request matrix (4 cells: enforcement hit / not-applicable / unrelated file / test file counts too) | SIMULATED_EXECUTION | PASS (4/4) | Satisfies the roadmap's completion criterion: "a request matrix ... classified correctly, including at least one deliberate undersell case." |

Totals: `STRUCTURAL_TEST` 12/12 pass; `SIMULATED_EXECUTION` 15/15 pass.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None yet.** No `claude -p` run of this skill has been attempted. Unlike
the setup adapter, this component's core value (natural-language intent
classification) is inherently model-judgment and cannot be meaningfully
exercised by `SIMULATED_EXECUTION` at all — the simulated tests above
only exercise the mechanical helper, which is a supporting check, not
the classification itself. A live run is required before this component
can be considered more than `CODED`, and is of higher evidentiary value
here than it was for the setup adapter's already-mechanically-heavy
dry-run path.

## Known limitations and unresolved evidence

- No live run exists. `disable-model-invocation: true` was chosen
  specifically because of this: a reference/development-phase component
  with unverified real-world classification behavior should not
  auto-trigger on ordinary user messages.
- Intent classification itself (the actual judgment call) has zero test
  coverage in this repository — by design, since it is inherently a
  natural-language task not reducible to a deterministic test fixture.
  Only the mechanical escalation/context/segmentation signal is covered.
- `segmentation-scan`'s "same logical unit of work" judgment
  (`VCPS-RISK-045`) is entirely unverified; the script only provides raw
  file-overlap facts with no branch/ticket lineage awareness.
- This component has no executor to hand off to for six of the seven
  non-`SETUP` workflows (roadmap Phase D). Its practical value today is
  limited to the classification/escalation step and the general-purpose
  agent then manually following the named Core workflow document.
- No adversarial/anti-gaming evaluation suite exists yet specifically
  targeting this component (e.g. an attempt to get a request
  misclassified as `TINY` through more subtle wording than this record's
  one "undersell" case, or a segmentation attempt that genuinely fools
  the overlap scan by touching an adjacent-but-not-identical path). This
  is recorded as an open item for roadmap Phase H (anti-gaming suite),
  not fabricated as already covered.

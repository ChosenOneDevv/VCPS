# Progressive loading map

Do not load every VCPS document on every invocation (correctness takes
priority over token reduction, but there is also no reason to read
`standard/gates/*` for a `SETUP`-only run that never executes Gates 4/5
itself). Load each document with `Read` the first time its stage is
reached, then keep it in context for the rest of the run — do not re-read
a document already loaded this session unless the Core location changed.

## Bootstrap (every invocation, before anything else)

1. `standard/VCPS.md` — entrypoint, layering, canonical-ownership table,
   precedence rules. Always.
2. `workflows/setup.md` — the Setup Engine itself. Always.
3. `templates/contract.md` — canonical `.vcps/` layout, `project.yaml`
   fields, ID scheme. Always — mode detection and Stage 4 both need to
   know what a "canonical root" structurally is almost immediately.

## Stage-triggered loading

| When you reach | Load |
|---|---|
| Stage 1 (repository discovery) | `standard/artifacts.md` (what a VCPS artifact set looks like, to recognize a pre-existing non-canonical one in `ADOPT`) |
| Stage 3 (risk classification) | `standard/risk-model.md`, `standard/levels.md` |
| Stage 4 (scaffold) | `templates/validation.md` items 1–4 (`templates/contract.md` is already loaded at bootstrap) |
| Stage 5 (dirty-tree / legacy classification) | `standard/human-checkpoints.md` (for `HC-07`/`HC-02` triggers) |
| Stage 6 (baseline verification) | `standard/evidence-model.md`, `standard/classifications.md` |
| Stage 7 (remediation) | `standard/anti-gaming.md` (the `AG-*` rules bound what R0 remediation may touch) |
| Stage 8 (baseline establishment) | `templates/validation.md` item 9 (baseline cross-checks) |
| Stage 9 (legacy registry) | `standard/classifications.md` (already loaded at Stage 6 if reached; re-read only if Stage 9 is reached without Stage 6 in this session, e.g. on resume) |
| Stage 10 (CI alignment) | nothing new — `workflows/setup.md` Stage 10 section is self-contained |
| Stage 11 (system audit) | `workflows/audit.md`, `templates/validation.md` (full document, for the final cross-reference pass) |
| Any human checkpoint | `standard/human-checkpoints.md`, if not already loaded |
| Any `UPGRADE`/`REPAIR` route | `standard/versioning.md` |
| `ADOPT` with a competing governance system | nothing new — `workflows/setup.md §SETUP-069` (already in the bootstrapped file) covers it |

## Deliberately not loaded for `SETUP`

`standard/gates/*` and `standard/independence.md` beyond what
`references/orchestration.md` already quotes — the Setup Engine does not
execute Gates 4/5 itself (`standard/open-questions.md` OQ-005 resolution
notes this explicitly: "setup engine doesn't execute Gate 4/5"). If a
future invocation legitimately needs gate content (e.g. Stage 10's
CI-to-gate mapping asks which gate a CI job serves), load only
`standard/gates/README.md` for the applicability matrix, not individual
`gate-N-*.md` files, unless a specific gate's full text is actually
needed for that decision.

## Scripts

`scripts/vcps_tool.py` is invoked via `Bash`, not read into context,
unless you are debugging its behavior. Its job is deterministic
computation (fingerprints, plan hashes, strict YAML parsing, structural
validation) that should not be redone by hand or re-derived by the model —
it is a tool call, not prose to reason over.

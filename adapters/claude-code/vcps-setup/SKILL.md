---
name: vcps-setup
description: Install, adopt, upgrade, or repair a VCPS (Vibe Coding Production Standard) installation in this repository by executing the canonical VCPS Core Setup Engine (workflows/setup.md). Use when the user asks to set up VCPS, adopt VCPS, run VCPS setup, check VCPS installation status, or resume an interrupted VCPS setup.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(git rev-parse --show-toplevel), Bash(git -c core.fsmonitor=false ls-files), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py detect *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py inventory *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py resume-status *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py validate *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py fingerprint *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py plan-hash *), AskUserQuestion
---

# /vcps-setup

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing the **VCPS Setup Engine** as defined in
`workflows/setup.md` (§7, "Deterministic Setup Engine contract") in the
*current target repository* (the repository Claude Code's working directory
is in now — this is almost never the VCPS specification repository itself,
except in VCPS's own development/dev-mode checkout).

This skill is an **adapter**. Per `standard/VCPS.md` `VCPS-CORE-003`, it
MUST NOT weaken, reinterpret, or omit a Core/Workflow requirement, and MUST
NOT define a second copy of VCPS. Where this file and a Core document
conflict, the Core document wins and the conflict is a defect to report,
not something to follow silently.

Treat this file as a dispatcher. It tells you *which canonical document to
read, when, and why* — it does not restate their rules. Load each
referenced document with `Read` only when you reach the stage that needs
it (see `references/loading-map.md`), not all at once; `SKILL.md` itself
stays short by design.

## 0. Locate VCPS resources (every invocation, first)

Read `references/core-discovery.md` now. It tells you how to find:

- the VCPS Core specification this skill executes against, and
- the *target* repository root (the one actually being set up).

If Core cannot be located, STOP and report `BLOCKED` with the exact paths
you checked. Do not improvise Core content from memory, and do not proceed
on an assumption about what a missing document says.

## 1. Parse invocation

`$ARGUMENTS` may contain `--dry-run` and/or `--core <path>`. Issue exactly
one shell command per step — compound/chained Bash commands have caused
false denials before; prefer single commands and read each result before
the next call.

- `--dry-run` present → you MUST NOT write or modify any file in the
  target repository this invocation, regardless of what a later stage
  would otherwise do. Produce the dry-run report (§5) and stop there.
- No `--dry-run` → proceed, but Stage 4 itself still begins with a
  mandatory dry-run per `VCPS-SETUP-051` before any write — omitting
  `--dry-run` does not skip the dry-run step, it only means you continue
  past it once the plan is presented and nothing in it requires a human
  checkpoint that is still pending.

## 2. Run the Setup Engine

The helper script's exact CLI shape is `vcps_tool.py <subcommand>
--target <target-repo> [--core <core-path>] [subcommand args]` —
**the subcommand comes first**, then its flags; `--target`/`--core` are
NOT global options and do not work before the subcommand. Use these exact
invocations (substitute real paths; do not rename the flags or reorder
them):

```
${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py detect --target <target-repo> --core <core-path>
${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py inventory --target <target-repo>
${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py validate --target <target-repo>
${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py resume-status --target <target-repo>
${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py fingerprint --target <target-repo> --scope <path> [<path> ...]
```

There is no subcommand that builds a plan for you — `plan-hash` only
computes the integrity hash of a plan object *you* construct (per
`templates/contract.md VCPS-SETUP-052`'s field list) and pass on stdin as
JSON; it does not discover or propose plan content itself:

```
echo '<plan JSON on one line>' | ${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py plan-hash --target <target-repo>
```

Read `references/loading-map.md` and follow it for what to load at each
stage. In outline (full authority: `workflows/setup.md §7`, especially the
Stage execution contracts table):

1. Mode detection (`VCPS-SETUP-050`) via `vcps_tool.py detect`: `NEW`,
   `ADOPT`, `UPGRADE`, or `REPAIR` — never a fifth mode.
2. Stages 1–3 read-only discovery (`vcps_tool.py inventory`); nothing is
   written yet.
3. Build the bounded plan and dry-run report yourself (there is no
   `vcps_tool.py` subcommand that does this for you — see §2's note above),
   grounded in Stages 1–3's findings and `templates/contract.md`'s field
   list; compute its integrity hash with `plan-hash` once built; present
   the plan before any write, per §5 below.
4. If `--dry-run`: stop here. Report and exit; `NO FILES WERE WRITTEN`.
5. For each stage from the earliest incomplete/invalidated stage through
   11: validate inputs → check budget/checkpoints → inspect read-only
   first → mutate only planned paths → persist evidence → validate the
   output → append the stage event as the commit marker → advance.
   `references/orchestration.md` maps each of these sub-steps onto actual
   Claude Code tool calls (`Read`/`Write`/`Bash`/`AskUserQuestion`).
6. Any Core-required human checkpoint (`standard/human-checkpoints.md` §1
   catalog; the per-stage list is in `workflows/setup.md §4`) → stop, use
   `AskUserQuestion`, persist the decision as an approval record under
   `.vcps/approvals/`, and never infer approval from silence or proceed
   past it speculatively while waiting.
7. Stage 11 system audit (`vcps_tool.py validate`, then your own review
   per `workflows/audit.md`) → terminal `SETUP_STATUS`.

## 3. Mutation budget discipline

Before every write, recompute: does this exact path/operation/byte-count
stay within the plan persisted at Stage 4? If not — STOP. Do not silently
absorb the expansion into "basically the same thing." Re-plan (a new
read-only dry-run, `VCPS-SETUP-052`) and, if the expansion is material,
treat it as `HC-13`. A write that looks obviously correct is not exempt
from this check — "obviously correct" is exactly the shortcut the budget
exists to prevent.

## 4. Evidence integrity (non-negotiable)

Never report `NOT_RUN`, `BLOCKED`, or `INCONCLUSIVE` as `PASS`. Never
treat: a YAML/config parse as a hosted CI run; an embedded/in-memory
database as production-database concurrency evidence; a mocked provider
as real-provider acceptance; an HTTP 200 or exit code alone as business
success; local execution as a production observation; or static
inspection as executed verification. `standard/evidence-model.md` owns
the exact tier/substitution rules — read it before Stage 6 if you have not
already (`references/loading-map.md` schedules this).

## 5. Dry-run / terminal report format

Report, in this order: detected mode and why; repository/toolchain facts
observed vs. inferred vs. unknown; proposed level with its uncertainty;
critical domains touched; dirty/legacy summary; files to create/modify;
verification commands and, for each, why it is or isn't runnable right
now; likely human checkpoints; the mutation budget (allowed paths, max
files, max bytes, allowed operations); unknowns; blockers. End every
dry-run with **`NO FILES WERE WRITTEN`** verbatim. End a non-dry-run
invocation with the actual `SETUP_STATUS` (`COMPLETE` / `PARTIAL` /
`BLOCKED`) and the specific reasons for it.

## 6. Never

- Never invoke a fifth mode beyond `NEW` / `ADOPT` / `UPGRADE` / `REPAIR`.
- Never touch an `UNKNOWN`-classified file beyond hashing/describing it —
  no edit, stage, commit, or delete.
- Never rewrite the baseline to make a newly introduced failure look
  pre-existing (`AG-017`).
- Never resume past a `BLOCKED` stage without an exact-scope approval or a
  genuinely changed condition.
- Never claim `SETUP_STATUS: COMPLETE` while an `L2`+ project has an
  undispositioned `CRITICAL` legacy finding, or an `L3` project has an
  undispositioned `CRITICAL`/`HIGH` one (`VCPS-SETUP-041`).
- Never duplicate a Core rule's definition in this file or in your own
  report wording to the point that this skill becomes a second normative
  source — cite the requirement ID and quote sparingly; the Core document
  is the owner.

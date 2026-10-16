# Evaluation record: Claude Code FEATURE workflow (`/vcps-feature`)

- Adapter version: `0.1.0-draft.7` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/feature.md`
- Date: 2026-10-06

## Provenance

New component. Fourth slice of roadmap Phase D. The highest-ceremony
per-change workflow (full Gate 1–5 matrix, no reduced depth anywhere) —
built last among the per-change workflows (after `TINY`, alongside
`HOTFIX`/`RELEASE`) since its nine steps are the union of nearly every
mechanical touchpoint already built for the earlier slices: `vcps-router`
for risk classification (Step 1), the shared lib for anti-gaming/evidence
sanity checks (Steps 4–5) and orphan-check (Step 9). No new mechanical
helper was needed.

## Scope, stated honestly

Every step names which gate it maps to and which Core document owns that
gate's actual requirements (`standard/gates/gate-N-*.md`) — this skill
does not restate any of them. Steps 7–8 (`VERIFIED`, `ACCEPTED`) are
lifecycle transitions this skill explicitly says the agent MUST NOT grant
on its own authority (`VCPS-LC-003`) — `ACCEPTED` in particular requires
a human or external party via `HC-14`.

## Results

Command: `python3 adapters/claude-code/vcps-feature/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Every pre-approved `Bash` entry is read-only `git`, the router, or the shared lib | STRUCTURAL_TEST | PASS | |
| S5 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S6 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S7 | Router script exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S8 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S9/S10 (×5) | Each of the five `standard/gates/gate-N-*.md` is cited and actually exists | STRUCTURAL_TEST | PASS (10/10) | Proves every gate reference in this skill resolves to a real Core document, not a typo'd filename — the same class of defect `/vcps-audit`'s own `S5`/`S6` caught during Phase D slice 1. |
| S11 | Never claims to set `ACCEPTED` on its own authority | STRUCTURAL_TEST | PASS | `VCPS-LC-003` cited. |
| S12 | `workflows/feature.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 20/20 pass. No `SIMULATED_EXECUTION` tests —
every mechanical subcommand this skill calls is tested in its own
component's suite (`vcps-router`, `lib`).

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** This is the richest workflow in this adapter and has the most
to actually observe live: whether risk re-classification genuinely
happens continuously (Step 1's own instruction) rather than being set
once and forgotten, and whether Gate 2–5 depth genuinely scales with the
applicability matrix rather than being applied uniformly regardless of
class.

## Known limitations and unresolved evidence

- No live run; every judgment-heavy step (discovery, architecture,
  implementation quality, verification depth, security review,
  acceptance) is entirely unverified beyond structural soundness of the
  dispatcher text itself.
- No test exercises the actual hand-off to `/vcps-release` end to end.
- Risk re-classification mid-run (Step 1's "re-check it continuously")
  has no mechanical enforcement — nothing stops a live session from
  classifying once at the start and never revisiting it.

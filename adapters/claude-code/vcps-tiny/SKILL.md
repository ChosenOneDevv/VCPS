---
name: vcps-tiny
description: Make a genuinely R0 change (copy, styling, comments, docs, formatting) with minimum ceremony, per workflows/tiny.md. Use only when the change is provisionally believed to touch no enforcement path and change no behavior — if unsure, use /vcps instead, which will classify correctly rather than assume TINY.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py escalation-check *), Bash(${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan *), AskUserQuestion
---

# /vcps-tiny

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing `workflows/tiny.md` in the *current target repository*.
**Read that file in full now** — this skill is a thin dispatcher over it,
not a restatement (`standard/VCPS.md` `VCPS-CORE-003`).

**Scope of this skill, stated honestly:** this is a reference/
development-phase component with no live-run evidence (see
`evaluation/vcps-tiny.md`). `TINY` is the most misuse-prone intent in
`workflows/README.md`'s own list — this skill exists to keep it honest,
not to make genuinely non-trivial changes feel lighter than they are.

## 1. Verify `R0` eligibility BEFORE proceeding (Step 1 — mandatory, not optional)

Per `workflows/tiny.md`: this check is mandatory *precisely because* `TINY`
is attractive to misuse. Run it before touching anything:

```
${CLAUDE_SKILL_DIR}/../vcps-router/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [--touched-path <path> ...]
```

If `"forced_r3": true`, **STOP and re-route** (`VCPS-WF-003`) — this is
not `R0`, full stop, regardless of how the change looks. This is the same
mechanical floor `/vcps` itself uses (`VCPS-RISK-041`): a change touching
a registered invariant's enforcement path is never `TINY`.

Also check, by your own reading (the script above only catches the one
mechanical case): does the change affect logic, queries, access control,
external calls, or schema? Does it change behavior reachable by users or
systems at all? If yes to any — **STOP and re-route**, do not proceed as
`TINY`.

## 2. Make the change

Ordinary `Write`/`Edit` permission prompts apply — this skill does not
pre-approve mutation, same defense-in-depth principle as every other
skill in this adapter.

## 3. Gate 3 (light) — Step 3

Scope discipline, no secrets, no anti-gaming weakening. You MAY run:
```
${CLAUDE_SKILL_DIR}/../lib/vcps_evidence.py antigaming-scan --target <repo> --scope-path <file> [...]
```
as a sanity check on what you just touched (candidates only — see the
script's own `note` field; a match is not itself a violation).

## 4. Gate 4 (light) — Step 4

Run the project's actual configured checks (ordinary `Bash` permission
prompt, as always — this skill does not ship, and will not ship, a
command-execution wrapper; see `/vcps-bug`'s `SKILL.md` for why that
shape is a security anti-pattern this adapter avoids). Confirm no new
failures versus baseline.

## Escalation / re-routing (`VCPS-WF-TINY-001`)

Any of the following found during the change MUST immediately stop
`TINY` and re-route to `BUG` or `FEATURE` at the correct class — **this
is a `MUST`, not a judgment call you can decide your way around**:

- the diff affects logic, queries, access control, external calls, or
  schema, or touches anything on an invariant's enforcement path;
- the diff is larger than a cosmetic change naturally requires;
- static checks fail in a way suggesting an actual behavior change.

## Gate mapping

Gates 1, 2, 5 are `NOT_APPLICABLE` by definition of `R0`. Gates 3 and 4
run at light depth only — never skipped entirely.

## Outputs

Minimal: Gate 3/4 light records, diff.

## Exit

`CODED` with light Gate 3/4 `PASS`. `TINY` changes generally do not need
individual feature acceptance; they ride with the next release's Gate 6.

## Never

- Never skip Step 1's eligibility check because the change "obviously"
  looks tiny.
- Never treat `escalation-check`'s `forced_r3: false` as proof the change
  is safe to proceed as `TINY` without also checking logic/access-
  control/schema impact yourself.
- Never continue as `TINY` after finding any `VCPS-WF-TINY-001` trigger —
  stop and re-route immediately, not after finishing the change.

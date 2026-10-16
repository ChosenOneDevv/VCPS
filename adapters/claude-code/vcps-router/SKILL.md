---
name: vcps
description: Classify an ordinary development request into its correct VCPS workflow intent (FEATURE, REVIEW, BUG, TINY, HOTFIX, AUDIT, RELEASE) and check it against mechanical risk-escalation signals, per workflows/README.md's intent-classification contract. Use when the user describes development work in a VCPS-governed repository and has not already named a specific workflow or invoked /vcps-setup.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git -c core.fsmonitor=false status --short --untracked-files=all), Bash(git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv), Bash(git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_router.py escalation-check *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_router.py project-context *), Bash(${CLAUDE_SKILL_DIR}/scripts/vcps_router.py segmentation-scan *), AskUserQuestion
---

# /vcps

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing the **intent-classification and risk-escalation step**
that `workflows/README.md` SS2 (`VCPS-WF-001`/`002`/`003`) requires before
any workflow run starts, in the *current target repository*.

**Scope of this skill, stated honestly:** this is a reference/
development-phase component, like `/vcps-setup`. It classifies and
escalates. It does **not** itself execute `FEATURE`/`REVIEW`/`BUG`/`TINY`/
`HOTFIX`/`AUDIT`/`RELEASE` — no adapter-side executor for those exists yet
(see `adapters/README.md`). Once classification is done, tell the user
which Core workflow document (`workflows/<intent>.md`) governs their
request and that you will follow it manually (reading it now, as the
general-purpose agent you already are), rather than claiming this skill
dispatches to an automated executor that does not exist.

This skill is an **adapter**. Per `standard/VCPS.md` `VCPS-CORE-003`, it
MUST NOT weaken, reinterpret, or omit a Core/Workflow requirement, and MUST
NOT define a second copy of VCPS. Where this file and a Core document
conflict, the Core document wins and the conflict is a defect to report.

## 0. Read the Core contract first

Read, in this order, before classifying anything:

1. `workflows/README.md` (the full intent list, `VCPS-WF-001/002/003`, the
   gate-mapping summary).
2. `standard/risk-model.md` SS5 (`R0`–`R3` change risk classes,
   `VCPS-RISK-040/041/042/045`).
3. `workflows/tiny.md` and `workflows/hotfix.md` in full — these two
   intents have the narrowest, most misuse-prone entry conditions
   (`TINY`'s `VCPS-WF-TINY-001`, `HOTFIX`'s confirmed-production-impact
   requirement) and this skill exists largely to keep both honest.

Do not classify from memory of a prior session. Re-read these files now.

## 1. Gather mechanical signal before judging anything

**You MUST run this before forming an intent opinion, not after.** Do not
let the user's own wording anchor your classification first.

1. Determine the file(s) the request will plausibly touch. If the user
   already has a diff/working-tree change, use the exact pre-approved commands
   `git -c core.fsmonitor=false status --short --untracked-files=all` and
   `git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv`.
   Do not add flags or arguments; a different Git invocation requires normal
   tool approval.
   to get the real paths; if it's a request not yet coded, read enough of
   the relevant area to name the real paths you expect — a guess recorded
   as a guess is fine, an unexamined guess is not.
2. Run:
   ```
   ${CLAUDE_SKILL_DIR}/scripts/vcps_router.py escalation-check --target <repo> --touched-path <path> [--touched-path <path> ...]
   ```
   If `"forced_r3": true`, the change is **at least `R3`** per
   `VCPS-RISK-041` — full stop, before you consider the user's wording at
   all. This is a floor; you MUST NOT lower it, and you MUST say so
   explicitly if the user described the change as "tiny," "small," "just
   a quick fix," or similar (`VCPS-WF-002`).
3. Run:
   ```
   ${CLAUDE_SKILL_DIR}/scripts/vcps_router.py project-context --target <repo>
   ```
   `critical_domains` here is **informative candidate context only** —
   per `VCPS-RISK-002` you MUST NOT escalate merely because a domain name
   or keyword resembles the request. Use it to decide where to *look*
   (trace the actual impact path), never as the classification itself.
4. If you suspect this request is part of a larger logical unit of work
   already in progress (same branch, same ticket, a recent related
   change), run:
   ```
   ${CLAUDE_SKILL_DIR}/scripts/vcps_router.py segmentation-scan --target <repo> --touched-path <path> [...]
   ```
   Per `VCPS-RISK-045`, the *cumulative* effect of a related sequence
   governs classification — a change deliberately or accidentally split
   into several small-looking pieces does not get to classify each piece
   in isolation if their combined effect is `R2`/`R3`.

If `escalation-check`/`project-context`/`segmentation-scan` report
`"has_vcps": false`, say so plainly: there is no registered invariant or
risk profile to check against yet, which is itself informative (the user
likely needs `/vcps-setup` first, or this repository has none of VCPS's
machinery to lean on and your classification rests on your own judgment
alone — record that it does).

## 2. Classify the primary intent

Per `VCPS-WF-001`, classify into **exactly one** of: `FEATURE`, `REVIEW`,
`BUG`, `TINY`, `HOTFIX`, `AUDIT`, `RELEASE`. (`SETUP` is handled by
`/vcps-setup`, not this skill — if the repository has no VCPS installation
at all, say so and point at `/vcps-setup` instead of guessing a workflow
intent for an ungoverned repository.)

Use the user's wording as **input, never authority** (`VCPS-WF-002`):

- A request phrased as "tiny"/"small"/"quick" that the mechanical check
  forced to `R3`, or that your own reading shows touches logic, access
  control, external calls, schema, or any enforcement path
  (`workflows/tiny.md` `VCPS-WF-TINY-001`), is **not** `TINY` — classify
  it `BUG` or `FEATURE` at its real class instead, and say explicitly that
  you overrode the user's own framing and why.
- A request phrased as "hotfix"/"urgent" with no confirmed live production
  impact (`workflows/hotfix.md`: "Unconfirmed urgency MUST NOT invoke
  HOTFIX") is **not** `HOTFIX` — classify it `BUG` instead, and say so.
- A request spanning more than one intent MUST be split into separate
  runs, or handled entirely under the stricter intent, per `VCPS-WF-001`.
  Do not silently pick the easier of two intents for a mixed request.
- `AUDIT` is read-only (`standard/validation.md`/this repository's own
  AUDIT semantics: it cannot claim implementation gate outcomes). If the
  user's "assessment" request will actually require code changes to
  answer, it is not `AUDIT` — say so and reclassify.

State your classification, the evidence/signal you based it on (including
the mechanical `escalation-check` result), and — if it differs from how
the user framed the request — exactly what changed and why, per
`VCPS-WF-002`'s own spirit (never silently substitute your judgment
without saying you did).

## 3. Hand off

Once classified (and escalated where required):

1. Name the governing Core workflow document (`workflows/<intent-lowercase>.md`,
   e.g. `workflows/bug.md`).
2. Read it now and follow its steps/gate mapping directly as the
   general-purpose agent — this skill's job (classification + escalation)
   is done; it does not hand off to a separate automated executor for
   `FEATURE`/`REVIEW`/`BUG`/`TINY`/`HOTFIX`/`AUDIT`/`RELEASE` (none exists
   yet — see `adapters/README.md`'s component list before claiming
   otherwise).
3. If the repository has `.vcps/` artifacts, create/update the correct
   work-item record per `templates/contract.md`'s canonical layout as you
   proceed through that workflow's steps — this skill's `allowed-tools`
   deliberately does not pre-approve `Write`/`Edit` for that (same
   defense-in-depth principle as `/vcps-setup`'s own `SKILL.md` SS3: every
   mutation goes through Claude Code's own permission prompt).

## 4. Never

- Never classify `TINY` or `HOTFIX` by the user's adjective alone.
- Never treat `escalation-check`'s `"forced_r3": false` as proof the
  change is low-risk — it only means this one mechanical check (registered
  invariant enforcement paths) found nothing; your own impact-path tracing
  (`VCPS-RISK-001`) still governs everything `critical_domains` or your own
  reading surfaces.
- Never claim this skill executed a workflow it only classified.
- Never silently split or merge a multi-intent request without saying so.

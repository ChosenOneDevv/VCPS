# Evaluation record: Claude Code HOTFIX workflow (`/vcps-hotfix`)

- Adapter version: `0.1.0-draft.7` ([adapters/claude-code/VERSION](../adapters/claude-code/VERSION))
- VCPS Core: `0.1.0-draft`; resolves `workflows/hotfix.md`
- Date: 2026-10-06

## Provenance

New component. Fifth slice of roadmap Phase D. Required one new shared
mechanical helper: `adapters/claude-code/lib/vcps_evidence.py`'s
`lapsed-deferral-check`, plus an additive extension to
`templates/schemas/approval.schema.json` (a new optional
`deferral_follow_up: {owner, deadline}` field) — both built because
`workflows/hotfix.md`'s `VCPS-WF-HOTFIX-001`/`003` deferral-tracking
rule is genuinely mechanical (does an `HC-16` decision record a
follow-up commitment; has its deadline passed) in a way nothing in this
adapter previously checked for.

## Scope, stated honestly

`HOTFIX` is the highest-risk workflow to get wrong in exactly the
direction of "urgency justifies skipping things." This skill's entry
gate (Step 0, before `workflows/hotfix.md`'s own Step 1) is explicit:
unconfirmed urgency MUST NOT invoke this skill at all — re-route to
`/vcps-bug`. `HC-10`/`HC-03` non-waivability (`VCPS-WF-HOTFIX-002`) and
`HC-16`-only deferral (`VCPS-WF-HOTFIX-001`) are stated as absolute, not
situational.

## Results

Command: `python3 adapters/claude-code/vcps-hotfix/tests/run_tests.py`

| # | Scenario | Class | Result | What was observed |
|---|---|---|---|---|
| S1 | `SKILL.md` has frontmatter | STRUCTURAL_TEST | PASS | |
| S2 | Manual invocation only | STRUCTURAL_TEST | PASS | |
| S3 | No blanket `Write`/`Edit` pre-approval | STRUCTURAL_TEST | PASS | |
| S4 | Every pre-approved `Bash` entry is read-only `git` or the shared lib | STRUCTURAL_TEST | PASS | |
| S5 | Every `allowed-tools` script path resolves | STRUCTURAL_TEST | PASS | |
| S6 | Every body-text script path reference also resolves | STRUCTURAL_TEST | PASS | |
| S7 | Shared lib exists at the referenced location | STRUCTURAL_TEST | PASS | |
| S8 | States unconfirmed urgency MUST NOT invoke `HOTFIX` | STRUCTURAL_TEST | PASS | |
| S9 | States `HC-10`/`HC-03` are NOT waivable | STRUCTURAL_TEST | PASS | `VCPS-WF-HOTFIX-002` cited. |
| S10 | States `HC-16` is the only deferral mechanism | STRUCTURAL_TEST | PASS | `VCPS-WF-HOTFIX-001` cited. |
| S11 | Cites the lapsed-deferral escalation rule | STRUCTURAL_TEST | PASS | `VCPS-WF-HOTFIX-003` cited. |
| S12 | `workflows/hotfix.md` exists | STRUCTURAL_TEST | PASS | |

Totals: `STRUCTURAL_TEST` 12/12 pass. The `lapsed-deferral-check` logic
itself is tested in `adapters/claude-code/lib/tests/run_tests.py` tests
`17`–`20` (missing follow-up, lapsed deadline, future deadline not
flagged, non-`HC-16` decisions never flagged), not re-counted here.

### Live runs (`LIVE_ADAPTER_EXECUTION`)

**None.** The single highest-value thing to observe live: whether the
model actually stops at Step 0 for merely-reported (not confirmed)
urgency, which is the one entry condition this whole workflow depends
on getting right before anything else matters.

## Known limitations and unresolved evidence

- No live run; the confirmed-vs-reported urgency distinction at Step 0
  is entirely unverified in practice.
- `lapsed-deferral-check` cannot see whether a lapsed deferral was
  already resolved by a later record (deliberately, per `AG-011` — the
  original decision record is never edited to say so); every result it
  reports is a candidate for the model to cross-check against later
  findings/work-items, not a final verdict.
- No mechanical check exists for `VCPS-WF-HOTFIX-002`'s
  non-bypassability of `HC-01`–`HC-05`/`HC-11`/`HC-12` specifically
  (only `HC-16` deferral tracking is mechanized) — whether a live
  session actually respects this is unverified.

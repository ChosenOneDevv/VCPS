# Human Checkpoints

This document owns: human checkpoints (`HC-*`), their protocol, and approval
records.

## 1. Checkpoint catalog

Each checkpoint names a trigger condition. Any workflow or Core rule that
names an `HC-*` code requires this protocol before the gated action may
proceed.

| Code | Trigger |
|------|---------|
| `HC-01` | A destructive data operation (deletion or irreversible overwrite of authoritative data). |
| `HC-02` | A destructive database migration (applying or discarding it). |
| `HC-03` | A production write or other live side effect. |
| `HC-04` | A history rewrite or force push, including on a default/protected branch. |
| `HC-05` | A change that weakens security posture. |
| `HC-06` | A verification-weakening change, per the `anti-gaming.md` §2 exception protocol. |
| `HC-07` | Ambiguous ownership: an unexplained dirty-tree item, unattributed file, or conflicting governance ownership. |
| `HC-08` | Accepting a serious (`HIGH`+) finding as `RISK_ACCEPTED`/`KNOWN_LIMITATION`. |
| `HC-09` | Lowering a project/component level or a change's risk class from a higher candidate. |
| `HC-10` | A release go/no-go decision (Gate 6). |
| `HC-11` | A check or action with a live side effect, or read-only production access requiring new authorization. |
| `HC-12` | Any action touching credentials/secrets. |
| `HC-13` | Material, unplanned expansion of scope beyond an authorized plan/budget. |
| `HC-14` | Feature acceptance: an Owner or delegated acceptor accepting a feature against its acceptance criteria. |
| `HC-15` | A legal or compliance-relevant change, including bulk export or disclosure of personal/regulated data. |
| `HC-16` | Deferring a gate requirement under `HOTFIX` (the only mechanism permitted to defer one; see `workflows/hotfix.md`). |

## 2. Protocol

**VCPS-HC-001.** On encountering a trigger condition, the executing agent
MUST stop and obtain a recorded human decision, unless a valid
pre-authorization already covers the exact action, scope, and revision
(§4).

**VCPS-HC-002.** Where an action plausibly falls under more than one
checkpoint, it MUST treat the action as triggering every applicable one,
not only the first recognized.

**VCPS-HC-003.** An agent MUST NOT approve its own checkpoint, approve on
behalf of a human, infer approval from silence, from an unrelated prior
message, or from the human not having objected. A changed scope requires
a new checkpoint request; a prior decision MUST NOT be reused or
broadened beyond what it actually covered.

**VCPS-HC-004. (Approval scope binding)** A decision authorizes only its
recorded action, scope, and revision. Reuse of an approval for a
different action, broader scope, or a different revision is not a valid
approval and MUST be treated as no decision at all.

While waiting, the affected gate or setup stage MUST become `BLOCKED` with
reason `DECISION`.

**VCPS-HC-010.** A checkpoint request MUST present:

- which checkpoint(s) apply and why;
- the exact action, scope, and revision it would authorize;
- what happens if approved, and what happens if rejected or deferred;
- any risk, irreversibility, or blast radius relevant to the decision.

**VCPS-HC-011.** While waiting, the agent MAY continue work that does not
depend on the decision. It MUST NOT perform any part of the gated action.

**VCPS-HC-012.** A rejected or unresolved checkpoint MUST NOT be silently
retried under different wording. The affected gate or setup stage MUST
become `BLOCKED` with reason `DECISION` until a decision is recorded.

## 3. Checkpoint record

**VCPS-HC-020.** Each decision MUST be persisted as a VCPS artifact with:
checkpoint code(s), the exact action/scope/revision it covers, the
decision (`APPROVED`, `REJECTED`, or `APPROVED_WITH_CONDITIONS`), the
human actor, timestamp, any conditions or constraints, related work-item
references, and — where the decision is revision-bound — the revision it
applies to.

**VCPS-HC-021.** Only a human actor may record `APPROVED`,
`APPROVED_WITH_CONDITIONS`, or `REJECTED`. An agent MUST NOT set these on
its own authority. Silence has no approval representation and MUST NOT be
recorded as any of the three.

## 4. Pre-authorization

**VCPS-HC-030.** An Owner MAY pre-authorize a class of actions with a
recorded scope, maximum impact, and optional expiry, so that matching
future actions do not each require a fresh synchronous decision.

**VCPS-HC-031.** Pre-authorization MUST NOT cover `HC-04` on default/
protected branches, or any checkpoint whose action is irreversible at a
scale beyond the pre-authorization's recorded maximum impact — those
always require a fresh, specific, synchronous human
decision. Pre-authorization MUST NOT cover `HC-06` (verification
weakening), `HC-08` (serious risk acceptance), `HC-10` (release go/no-go),
`HC-14` (feature acceptance), or `HC-16` (`HOTFIX` gate deferral) under
any circumstance — these always require a per-instance human decision,
with no blanket exclusion-list override. A pre-authorization for any
other checkpoint MUST bound the specific action class and maximum impact;
it MUST NOT waive a gate, evidence, or invariant rule, and it narrows
rather than replaces human judgment: an action outside its exact bound is
not covered.

## 5. Checkpoints that are never waivable

**VCPS-HC-040.** Gate/evidence/invariant rules, and the Core requirements
listed in `risk-model.md` (`VCPS-RISK-044`), cannot be waived by any
checkpoint decision, pre-authorization, or approval — a checkpoint can
authorize a specific risky *action*; it cannot authorize skipping a Core
rule. An Owner risk-acceptance decision for a legacy finding's residual
risk is a decision to accept known risk, not a waiver of the rule that
classified it.

## Recovery note

*Non-normative.* This file was reconstructed on 2026-10-05 after the
original was lost to repository corruption. The protocol text in §2–§4
(`VCPS-HC-001`, `VCPS-HC-003`, the `BLOCKED`/`DECISION` sentence,
`VCPS-HC-010`, `VCPS-HC-011`, `VCPS-HC-020`, `VCPS-HC-030`, `VCPS-HC-031`)
is recovered verbatim from `standard/core-audit-0.1.md`'s per-line
requirement inventory, which quoted these exact lines before the file was
lost; `VCPS-HC-004` is recovered verbatim from its description in that
same audit document's findings narrative (added per audit finding
CA-015) and from its citation in `workflows/setup.md` `VCPS-SETUP-054`
("Approval reuse follows VCPS-HC-004, including revision binding; silence
is not a decision"). The §1 catalog (`HC-01` through `HC-16`) is
reconstructed, not verbatim-recovered: no table of these sixteen entries
survived in the audit inventory (its line-capture method only quotes
lines containing a bare RFC 2119 keyword, and a tabular catalog mostly
doesn't), so each trigger description here is assembled from every
place `workflows/setup.md`, `workflows/hotfix.md`, `workflows/bug.md`,
`standard/risk-model.md`, `standard/lifecycle.md`, and
`templates/contract.md` (all intact) actually cite that code and explain
its trigger in context. `HC-01`–`HC-09`, `HC-12`, `HC-13`, `HC-15` are
cited explicitly together in `workflows/setup.md` `VCPS-SETUP-066`;
`HC-10` in `templates/contract.md` ("Release go/no-go is derived from
HC-10") and `workflows/hotfix.md` ("HC-10 and HC-03 are NOT waivable by
HOTFIX"); `HC-14` in `templates/contract.md` and
`standard/lifecycle.md`'s `ACCEPTED` transition row; `HC-16` in
`workflows/hotfix.md` directly. §5 (`VCPS-HC-040`) is a reconstruction
from `standard/risk-model.md` `VCPS-RISK-044` and `templates/validation.md`
item 10 ("Rejection and silence never pass a gate") rather than a
recovered original line and SHOULD be treated as lower-confidence than
the rest of this file if a backup ever surfaces.

**2026-10-05, second pass (recovery audit).** A broader grep of
`core-audit-0.1.md` (not run in the first reconstruction pass) surfaced a
summary table, "Human checkpoint integrity: HC-01 through HC-16," that
independently corroborates this file's §1 catalog groupings verbatim-close
("HC-01/02/03/04" destructive/migration/production/history-rewrite;
"HC-05/06" security/verification weakening; "HC-07/08/09" ownership/risk
acceptance/downgrade; "HC-10/11/12" release/live-effects/credentials;
"HC-13/14/15/16" scope/acceptance/legal/HOTFIX) — raising confidence in
that catalog from "reconstructed from scattered citations" to
"reconstructed and independently cross-confirmed by a dedicated summary
table," though the table still doesn't give full original sentence
wording per code. The same pass found two concrete corrections applied
here: the `HC-15` catalog row now names "bulk export or disclosure of
personal/regulated data" explicitly (per finding CA-017's recorded
correction, previously missed), and `VCPS-HC-031` now lists its full
exclusion set — `HC-06`/`08`/`10`/`14`/`16` barred from pre-authorization
entirely, not only `HC-04` — per finding CA-026, which states this
directly: "`VCPS-HC-031` excludes those checkpoints and says
pre-authorization cannot waive gate, evidence, or invariant requirements."
The first pass had only recovered the `HC-04` clause verbatim and missed
this broader exclusion list; it is now included.

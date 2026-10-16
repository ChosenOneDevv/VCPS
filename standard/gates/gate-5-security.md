# Gate 5: Security

Confirms security-relevant categories the change actually touches are
evaluated, at the evidence strength the category's risk warrants.
Applicability is risk-based throughout this document: a category is
evaluated because the change actually touches it (per `risk-model.md`'s
impact dimensions), never as a fixed checklist every change must clear
regardless of relevance.

## 1. Required activities (recovered / directly corroborated)

**VCPS-G5-001.** At minimum, the full `risk-model.md` D3 dimension —
authentication, authorization, tenant isolation, secrets, and privilege —
MUST be evaluated for any change that touches it, plus business-logic-abuse
and any other category the change's impact dimensions indicate are touched
(`risk-model.md` D3/D4/D8).

**VCPS-G5-012.** Static review alone (`E1`) MAY support `PASS` for
categories where the risk is adequately bounded by inspection (e.g. a
straightforward access-control check visible in the diff); a category
with `HIGH`+ severity exposure or non-obvious runtime behavior requires
executed evidence (`E2`+), not static review alone.

## 2. Design decisions added during ratification (2026-10-05)

The items below are **not recovered original text**. They were added
during the dedicated recovery-ratification audit after cross-checking
`VCPS-G5-001`'s category list against `risk-model.md` D3/D4/D8 (which name
more categories than this file, pre-ratification, actually enumerated)
and against a fixed adversarial checklist. Each is grounded in an
already-established VCPS principle named inline; none is a free invention,
but none should be read as "this is what the original said."

**VCPS-G5-002. (Authentication)** Where the change touches authentication
(login, session, token issuance/validation, password/credential handling),
evidence MUST show the mechanism actually rejects invalid/expired/forged
credentials, not merely that valid ones are accepted.

**VCPS-G5-003. (Object-level access control)** Authorization and
tenant-isolation evidence (`VCPS-G5-001`) MUST cover per-object checks
(a user/tenant cannot act on another's specific record by guessing or
supplying its identifier), not only endpoint-level or role-level checks —
endpoint access does not imply object access is actually checked.

**VCPS-G5-004. (Privilege escalation)** Where the change touches privilege
assignment, role changes, or a privileged AI-initiated action's allowlist
(`risk-model.md` D8; `gate-2-architecture.md VCPS-G2-014`), evidence MUST
show a lower-privileged actor cannot reach a higher-privileged action
through the change.

**VCPS-G5-005. (Server-side enforcement)** A security property designed
at Gate 2 (trust boundaries, `VCPS-G2-011`) MUST be verified enforced
server-side; evidence resting only on a client-side check (UI hiding,
client-side validation, a disabled button) MUST NOT support `PASS` for
that property.

**VCPS-G5-006. (Secrets at runtime)** Beyond `gate-3-implementation.md
VCPS-G3-006` (secrets MUST NOT be committed/logged/embedded), where the
change touches error responses, logs, or external-facing output, evidence
MUST show secrets are not exposed through those paths at runtime — a
build-time secrets check does not demonstrate a runtime exposure path is
closed.

**VCPS-G5-007. (Sensitive data exposure)** Where the change touches
personal or regulated data (`risk-model.md` D4), evidence MUST show the
data is not exposed beyond its intended audience through the change
(response payloads, logs, error messages, or a different tenant/role's
view).

**VCPS-G5-008. (Untrusted input, including LLM output)** Gate 2's trust-
boundary design (`VCPS-G2-011`, covering `glossary.md`'s full "Untrusted
input" definition — frontend/client input, end users, external providers,
webhooks, files, **and LLM output**) MUST be verified actually enforced,
not merely designed. This explicitly includes content that influences a
privileged AI-initiated action (`risk-model.md` D8): where such an action
can be shaped by untrusted content (a file, a webhook payload, retrieved
text, model output derived from any of these), evidence MUST show the
untrusted content cannot itself authorize the action — this is a VCPS-
specific restatement of ordinary input-trust discipline applied to the
domain this standard governs, not a new category of risk.

**VCPS-G5-009. (File uploads)** Where the change accepts file uploads,
evidence MUST address at least: content is not trusted by its declared
type/extension alone, and stored/served uploads cannot escape their
intended storage scope (path traversal) or be served in a way that
executes as code in a context that shouldn't allow it.

**VCPS-G5-010. (Injection classes)** Where the change constructs a query,
command, path, or markup from input that is not fully controlled by the
builder, evidence MUST show the construction is not vulnerable to
injection (parameterization, escaping, or an equivalent safe-construction
method actually used, not merely intended).

**VCPS-G5-011. (External provider and webhook trust)** Where the change
touches an external transactional integration (`risk-model.md` R2
trigger) or a webhook receiver, evidence MUST show: the external party's
identity/signature is verified before acting on its input (webhook
authenticity), and — where the action is security- or money-relevant
(`risk-model.md` D2/D6) — that a replayed or duplicated message cannot
cause the action to repeat (idempotency). Neither is required where the
change touches no external integration or webhook; this is a risk-based
category like every other in this gate.

**VCPS-G5-013. (Abuse and resource exhaustion)** Business-logic-abuse
(`VCPS-G5-001`) and resource/rate abuse are evaluated only where the
change's impact dimensions indicate exposure (`risk-model.md` D5/D9) —
this is explicitly not a blanket requirement that every endpoint have
rate limiting; it is a requirement that the question be asked and
answered where the change's own risk profile raises it.

**VCPS-G5-014. (Security regression via baseline)** Security check
results MUST be compared against the baseline using the same mechanism
`gate-3-implementation.md VCPS-G3-009` and `gate-4-verification.md
VCPS-G4-002` already use for other checks — a newly introduced security
finding blocks `PASS`; a pre-existing one is reported per the baseline
procedure, never silently absorbed as "already there, so fine." This is
cross-referenced, not a separate Gate 5 baseline mechanism — duplicate
ownership of the baseline concept is avoided deliberately.

**VCPS-G5-015. (Dependency/supply-chain evidence)** Beyond
`gate-3-implementation.md VCPS-G3-004` (new dependencies justified/pinned
at introduction), where the project has a security/dependency scanning
mechanism (`anti-gaming.md AG-005` already forbids disabling or
downgrading it), evidence for `PASS` at `L2`+ on a change touching
dependencies SHOULD cite that scanning's current result for the touched
dependencies, not only that they were justified when first added.

**VCPS-G5-016. (Production-fidelity limits on security evidence)** The
same substitution rules `evidence-model.md §5` already applies elsewhere
apply to security evidence: a security control tested only in a
non-production configuration (debug mode, permissive local network/IAM
policy, test-only auth bypass) MUST NOT be reported as evidence the
production configuration is secure; the difference MUST be listed in
`limitations` per `VCPS-EVD-040`.

## 3. Deliberately NOT owned here (cross-reference only, to avoid
## duplicate ownership — see `gates/README.md` and §4 of this ratification)

Destructive operations and financial/critical mutations are owned by
`HC-01`/`HC-02` and `gate-2-architecture.md VCPS-G2-012`'s failure-design
requirement (forward/rollback plans); auditability of privileged actions
is owned by `gate-2-architecture.md VCPS-G2-014`'s logging requirement.
Gate 5 evaluates the *security* properties of a change that touches these
areas (e.g. "can an unauthorized actor trigger the destructive operation")
without re-owning the destructive-operation or audit-logging requirements
themselves.

## Outcomes

Per `gates/README.md §2`. `PASS` requires every touched category
evaluated at the required evidence strength with no unresolved blocking
finding. `NOT_APPLICABLE` only where the change touches no security-relevant
category at all (`R0`, or an `R1` change outside any such category per
`gates/README.md §4`).

## Recovery note

*Non-normative.* This file was first reconstructed on 2026-10-05 after
the original was lost to repository corruption, from only two recovered
fragments in `standard/core-audit-0.1.md`'s per-line requirement
inventory: the original (narrower) category-list sentence and
`VCPS-G5-012`'s static-review sentence — see git history of this file
for that first-pass version. On the same day, during the dedicated
recovery-ratification audit, a structured adversarial pass against 20
named attack categories found `VCPS-G5-001`'s category list materially
narrower than `risk-model.md` D3's own definition (missing
authentication, secrets, and privilege, which D3 names explicitly) and
found no coverage at all for several categories with clear grounding
elsewhere in VCPS (webhook/replay trust, LLM-output trust, upload
handling, injection, production-fidelity limits on security evidence).
§1 is corroborated-but-widened (the category list now matches D3
exactly); §2 is **entirely new, design-decision content**, explicitly
not claimed as recovered, each item grounded in a named existing VCPS
principle per the instructions for this ratification pass. This remains
the gate file with the least original material behind it — §1's two
items are the only text with a direct textual ancestor; everything in §2
should be read as "a security practitioner's reasonable elaboration of
D3/D4/D8 under VCPS's own stated principles," subject to the Owner's
review and revision, not as recovered specification.

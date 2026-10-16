# Glossary

This document owns VCPS term definitions. Other documents use these terms
with exactly these meanings. Normative rules about a term live in the document
linked from its entry.

| Term | Definition |
|------|------------|
| **Adapter** | Integration that lets a specific agent execute VCPS. Non-normative for the Core. See [VCPS.md §4](VCPS.md#4-architecture-and-layering). |
| **Assertion** | A precise, falsifiable statement about system behavior that evidence supports or refutes (e.g. "two concurrent debits on one account never overdraw it on PostgreSQL 16"). |
| **Baseline** | Recorded state of all configured checks at a specific revision, used to distinguish pre-existing failures from newly introduced ones. See [../workflows/setup.md](../workflows/setup.md). |
| **Change** | A coherent unit of modification evaluated through gates (typically one branch / pull request). |
| **Change risk class** | `R0`–`R3` rating of a single change. See [risk-model.md](risk-model.md). |
| **Checkpoint** | A required human decision point `HC-*`. See [human-checkpoints.md](human-checkpoints.md). |
| **Claim** | An assertion stated without supporting evidence. Evidence tier `E0`. |
| **Component** | A separately risk-classified part of a repository (service, package, module, screen group). |
| **Critical invariant** | A property whose violation causes high-impact harm (e.g. "ledger always balances"), registered as `INV-*`. See [risk-model.md](risk-model.md). |
| **Enforcement path** | The code, schema, configuration, and checks that together uphold an invariant. |
| **Evidence** | A recorded observation supporting or refuting an assertion. See [evidence-model.md](evidence-model.md). |
| **Evidence tier** | `E0 CLAIMED` … `E5 PRODUCTION`. See [evidence-model.md](evidence-model.md). |
| **Feature** | A user-meaningful capability tracked through the lifecycle. See [lifecycle.md](lifecycle.md). |
| **Fidelity** | How faithfully the environment used for evidence represents the environment the assertion is about. |
| **Finding** | A recorded, classified observation of a problem or uncertainty. See [classifications.md](classifications.md). |
| **Gate** | A defined quality checkpoint (Gate 1–6) with an outcome. See [gates/README.md](gates/README.md). |
| **Gate outcome** | `PASS`, `PARTIAL`, `BLOCKED`, `NOT_APPLICABLE`, or `NOT_EVALUATED`. |
| **Independence mode** | `I0`–`I4` separation between builder and verifier. See [independence.md](independence.md). |
| **Intent** | The kind of work requested: `SETUP`, `FEATURE`, `REVIEW`, `BUG`, `TINY`, `HOTFIX`, `AUDIT`, `RELEASE`. See [../workflows/README.md](../workflows/README.md). |
| **Legacy evidence gap** | An `EVIDENCE_GAP` recorded during setup for pre-existing code. |
| **Project level** | `L1`–`L3` rating of a project or component. See [levels.md](levels.md). |
| **Remediation** | A change that resolves a finding. |
| **Revision** | An immutable identifier of the exact repository content evaluated (e.g. a commit hash, or a content-addressed worktree snapshot that can be reconstructed). See [evidence-model.md §6](evidence-model.md#6-revision-binding-and-staleness). |
| **Stale evidence** | Evidence whose scope has been changed since it was produced. See [evidence-model.md](evidence-model.md). |
| **Trust boundary** | A point where data or control crosses from a less-trusted to a more-trusted context. |
| **Untrusted input** | Any data originating from frontend/client code, end users, external providers, webhooks, files, or LLM output. |
| **VCPS artifact** | A repository-readable file under the project's VCPS directory. See [artifacts.md](artifacts.md). |
| **Verification weakening** | Any change that reduces the ability of checks to detect defects. See [anti-gaming.md](anti-gaming.md). |

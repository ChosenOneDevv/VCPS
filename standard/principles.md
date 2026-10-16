# Principles

*Informative.* Principles explain intent. They are not directly testable.
Each principle points to the normative rules that implement it.

| ID | Principle | Implemented by |
|----|-----------|----------------|
| P-01 | **Working is not done.** A change that runs is only `CODED`. Done-ness is a lifecycle state backed by evidence. | [lifecycle.md](lifecycle.md) |
| P-02 | **Evidence over confidence.** An agent's certainty is a claim (`E0`), not evidence. | [evidence-model.md](evidence-model.md) VCPS-EVD-001 |
| P-03 | **Missing evidence is not a defect.** Absence of a test or environment is an `EVIDENCE_GAP`. | [classifications.md](classifications.md) VCPS-CLS-003 |
| P-04 | **`NOT_RUN` is not `PASS`.** Unexecuted checks never count as passing. | [evidence-model.md](evidence-model.md) VCPS-EVD-020 |
| P-05 | **No unbounded self-certification.** Verification independence scales with risk. | [independence.md](independence.md) |
| P-06 | **Untrusted by default.** Frontend/client, external provider, and LLM output are untrusted inputs. | [gates/gate-5-security.md](gates/gate-5-security.md), [gates/gate-2-architecture.md](gates/gate-2-architecture.md) |
| P-07 | **Critical state changes are engineered, not hoped for.** Authorization, isolation, atomicity, idempotency/concurrency, observability, recovery. | [gates/gate-2-architecture.md](gates/gate-2-architecture.md) VCPS-G2-010 |
| P-08 | **Reproduced defects become regressions tests where practical.** | [gates/gate-4-verification.md](gates/gate-4-verification.md) VCPS-G4-030 |
| P-09 | **No silent weakening.** Agents do not lower the bar to clear it. | [anti-gaming.md](anti-gaming.md) |
| P-10 | **Portable state.** Project truth lives in the repository, not in an agent's memory. | [portability.md](portability.md) |
| P-11 | **Risk-weighted burden.** Effort scales with impact; small changes to critical invariants are not small. | [risk-model.md](risk-model.md) |
| P-12 | **Automate routine work; escalate irreversible decisions.** | [human-checkpoints.md](human-checkpoints.md) |
| P-13 | **Legacy is recorded, not ignored or panicked over.** Existing gaps are registered and ratcheted. | [../workflows/setup.md](../workflows/setup.md) |
| P-14 | **Agent independence.** Any capable agent or human can execute VCPS. | [VCPS.md](VCPS.md) VCPS-CORE-001 |

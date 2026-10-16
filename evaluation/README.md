# Validation / Evaluation Suite (Layer 5)

[Setup Engine scenarios](setup-scenarios.md) define conceptual adversarial
fixtures and expected outcomes. They are not adapter execution results.
The full Core conformance suite is not yet implemented; the current
14-item contract coverage, including open checks, is mapped in
[`validation-contract-coverage.md`](validation-contract-coverage.md).
Adapter-specific structural and simulated checks also exist. See `OQ-010` in
[`../standard/open-questions.md`](../standard/open-questions.md).

Adapter execution records: [claude-code-adapter.md](claude-code-adapter.md)
(test classes: `STRUCTURAL_TEST`, `SIMULATED_EXECUTION`,
`LIVE_ADAPTER_EXECUTION`; simulated runs are never live passes).

The Codex adapter's structural evaluation and live-evidence limits are
recorded in [codex-adapter.md](codex-adapter.md).

Phase H adversarial case coverage is catalogued in
[anti-gaming-suite.md](anti-gaming-suite.md); it distinguishes executable
literal-pattern checks from semantic cases that still require model runs.
The reusable before/after diff-review bundle now covers all AG-001..017
cases in
[`fixtures/anti-gaming-diffs.json`](fixtures/anti-gaming-diffs.json). Its
blind prompt renderer is `python3 evaluation/render_diff_case.py AG-015`;
score the captured answer against the fixture's expected disposition and
rubric. Structural checks validate fixture and renderer behavior, not model
behavior.
All twelve evidence-integrity before/after cases (EVI-001..012) are in
[`fixtures/evidence-integrity-diffs.json`](fixtures/evidence-integrity-diffs.json)
and render with `python3 evaluation/render_diff_case.py --suite evidence-integrity EVI-009`.
Phase I's bounded security review and residual risks are recorded in
[security-audit.md](security-audit.md). Neither record claims full live
conformance.

The synthetic L3-shaped project, runnable preflight, and live Codex
read-only handoff limitations are documented in
[phase-j-acceptance.md](phase-j-acceptance.md).
The fixture's canonical read-only AUDIT report is
[synthetic-commerce-audit.md](synthetic-commerce-audit.md).

The Phase 0 product scope, gate baseline, recovery-confidence register,
phase charters, and completion assessment are recorded in
[phase-0-charter.md](phase-0-charter.md). Its three-round review findings
and expanded Phase 0–5 plan are in
[phase-0-5-deep-review.md](phase-0-5-deep-review.md).

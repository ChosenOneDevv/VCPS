# Changelog

## 1.0.0 — 2026-10-07

First stable release of the VCPS Core specification.

- Stabilizes the Core requirements after resolving or explicitly deferring
  all entries in [`standard/open-questions.md`](standard/open-questions.md).
- No normative requirement content changed from `0.1.0-draft`; this release
  removes the draft status and establishes the Core stability guarantee.
- No project artifact schema or layout migration is required. A project
  recording `vcps_version: 0.1.0-draft` may update that label to `1.0.0`.
  Setup reports the old version as `BEHIND`; it does not require `REPAIR`
  solely for this label change.
- Adapter, workflow-executor, and evaluation-suite maturity is unchanged
  and remains as described in
  [`evaluation/completion-roadmap.md`](evaluation/completion-roadmap.md).

Release audit: [`evaluation/system-audit-1.0.0.md`](evaluation/system-audit-1.0.0.md).

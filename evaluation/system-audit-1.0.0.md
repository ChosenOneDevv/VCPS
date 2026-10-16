# VCPS 1.0.0 release-candidate system audit

Date: 2026-10-07  
Audited source: `HEAD` `37db8409fa9b16664c4259f282bd8f2f4189e9f0` plus the
tracked release-candidate diff, SHA-256
`0b262abd92ae1a16169143a7f6aeaa3a2cbe349bc019edb7207caefdccc351b9`,
and [`CHANGELOG.md`](../CHANGELOG.md), SHA-256
`47415efee58cf99a736e52710556c7019bb5f4f3d67b925d1af59bddf3edadb1`.
The audit report itself is excluded from these digests.  
Scope: Core specification release readiness, open-question gate, version
metadata, setup version-drift behavior, and consistency of the user-facing
release claims. This is not a full audit of every adapter, evaluation case,
security threat, or external deployment.

## Evidence inventory

| Evidence | Revision / tier | Audit use and limitation |
|---|---|---|
| [`standard/core-audit-0.1.md`](../standard/core-audit-0.1.md) | Recorded adversarial Core audit; requirement inventory and 40 findings | Its final consistency pass found no direct contradictions and 225 unique requirement IDs with no undefined references. The normative requirement text is unchanged in this release candidate; this audit remains the substantive Core review. Its historical open questions are superseded by the current open-question decisions. |
| [`standard/open-questions.md`](../standard/open-questions.md) | Current source review | 12/12 entries are `RESOLVED` or explicitly `DEFERRED`; OQ-010 is deferred with reasoning. |
| [`standard/versioning.md`](../standard/versioning.md), [`VERSION`](../VERSION), Core and README status lines | Current source review | Authoritative version and release statements identify `1.0.0`; the stable claim is bounded to Core. |
| [`evaluation/completion-roadmap.md`](completion-roadmap.md) | Current source review | Known implementation gaps and live-evidence limits remain visible; no claim of complete adapter/evaluation conformance is made. |
| `git diff --check` | Release-candidate working tree | Passed. This checks patch whitespace only, not runtime behavior. |

## Review results

1. **Core stability gate:** all 12 open questions have a recorded disposition. No normative `VCPS-*` requirement text is changed by this release candidate; the changes update the version, explain the stability boundary, and align explanatory version-support text.
2. **Version consistency:** `/VERSION`, `standard/VCPS.md`, `standard/versioning.md`, and public repository documentation state `1.0.0`. Project schema `0.2.0` and layout `0.1.0` remain separate versions.
3. **Legacy version handling:** the Claude Code helper recognizes both `1.0.0` and `0.1.0-draft`. A legacy project is classified `BEHIND` and can update its version label without a blocking schema repair, because this cut changes no requirement content. Other unsupported versions remain subject to read-only repair behavior.
4. **Claims and gaps:** README, security, contribution, adapter, and roadmap text distinguish stable Core requirements from unfinished or unverified adapters and evaluation work. The release does not claim that the repository or its adapters are fully conformant or production-proven.
5. **Recorded conformance statement:** this report makes no VCPS project-conformance claim for the specification repository. It records a scoped release-readiness audit for the Core `1.0.0` cut.

## Residual limits

- The audit is scoped to the Core release boundary and its version-support surface. It does not close the broader Phase I security review or Phase J representative-project acceptance gaps.
- No runtime tests were run for this release-candidate pass. Existing adapter and evaluation results retain the revisions and evidence tiers recorded in their own reports.
- Repository adapter implementations remain at their separately documented maturity levels; the stable Core claim does not upgrade their evidence.

## Outcome

**Release-candidate audit: PASS for the scoped Core `1.0.0` stability claim.**
The pre-release question gate and owner authorization are satisfied. This
outcome applies to the recorded source snapshot and scope above; it is not a
whole-repository production-readiness certification.

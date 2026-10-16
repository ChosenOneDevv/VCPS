# Claude Code adapter

Reference/development-phase adapter binding Claude Code to VCPS. Scope:
`/vcps-setup` (the Setup Engine, `workflows/setup.md`), `/vcps` (general
intent classification + mechanical risk-escalation,
`workflows/README.md` `VCPS-WF-001/002/003`), and all seven non-`SETUP`
workflow executors: `/vcps-audit` (`workflows/audit.md`), `/vcps-review`
(`workflows/review.md`), `/vcps-bug` (`workflows/bug.md`), `/vcps-tiny`
(`workflows/tiny.md`), `/vcps-feature` (`workflows/feature.md`),
`/vcps-hotfix` (`workflows/hotfix.md`), and `/vcps-release`
(`workflows/release.md`) — roadmap Phase D closed in full 2026-10-06.
Installable from the public GitHub repository through the animated installer
or `adapters/install.py`; live workflow maturity remains limited as described
in the evaluation roadmap.

- Adapter version: `0.1.0-draft.9` (this file's directory, `VERSION`)
- VCPS Core: `1.0.0`; project schema `0.2.0`; layout `0.1.0`
- Invocation: `/vcps-setup [--dry-run] [--core <path>]`,
  `/vcps <request description>`, `/vcps-audit [scope description]`,
  `/vcps-review [scope description]`, `/vcps-bug [report description]`,
  `/vcps-tiny [change description]`, `/vcps-feature [feature description]`,
  `/vcps-hotfix [incident description]`, `/vcps-release [release description]`
- Skill locations: `adapters/claude-code/vcps-setup/`,
  `vcps-router/`, `vcps-audit/`, `vcps-review/`, `vcps-bug/`,
  `vcps-tiny/`, `vcps-feature/`, `vcps-hotfix/`, and `vcps-release/`
  (all under `adapters/claude-code/`), each surfaced as a Claude Code
  Skill via a symlink at `.claude/skills/<name>` →
  `../../adapters/claude-code/<name>`. Claude Code Skills may be symlinks
  (confirmed against current Skills documentation, 2026-10); the real
  files do not need to live under `.claude/skills/` themselves.
  `vcps-audit/`, `vcps-review/`, and `vcps-bug/` additionally depend on a shared
  `adapters/claude-code/lib/` directory being present alongside them —
  see `lib/README.md` for why (unlike every other component here, that
  one is deliberately *not* independently installable).
  All nine skills also load `adapters/UNTRUSTED-CONTENT.md` before reading
  target-controlled material. Symlink installs resolve it from the source
  tree; if skills are copied under `.claude/skills/<name>`, copy that file to
  `.claude/UNTRUSTED-CONTENT.md` so their relative reference remains valid.

## Supported Core version

This adapter's `detect` logic in `scripts/vcps_tool.py` treats
`1.0.0` and legacy `0.1.0-draft` as recognized VCPS specification versions,
and project schema `0.2.0` as the only currently supported write target
(with `0.1.0` as the sole migratable predecessor schema), matching
`workflows/setup.md VCPS-SETUP-050`. A different VCPS/schema version is
not an adapter bug — it routes to read-only `REPAIR`/`BLOCKED` per Core,
exactly as intended.

## Two installation modes

**A. VCPS repository development mode.** This adapter is developed and
tested from inside the VCPS specification repository itself — the skill
runs with its working directory inside (or at) the repo containing
`standard/VCPS.md`, and that same repository is both the Core source and
the (unusual, self-referential) target of setup. This is how the test
suite in `tests/` exercises the adapter today.

**B. Installed-into-target-repository mode.** The skill's own files travel
with the target repository via `.claude/skills/vcps-setup` (symlink or a
copy, either placed there by `adapters/install.py`), while the actual
project being set up is whatever arbitrary external repository the user
is in. See `vcps-setup/references/core-discovery.md` for exactly how the
skill locates a real Core copy to execute against in this mode —
`adapters/install.py --vendor-core` vendors a pinned copy automatically;
`--core <path>` remains supported for a one-off override.

## Claude Code assumptions and capability mapping

See `vcps-setup/references/orchestration.md` for the full mapping (this
resolves `standard/open-questions.md` OQ-005). Summary of what is
currently **verified** vs. **unverified**:

| Capability | Status |
|---|---|
| Skill discovery, slash invocation, `$ARGUMENTS` parsing | Verified against current Skills documentation and this environment's Claude Code version. |
| `Read`/`Grep`/`Glob` for discovery | Verified — ordinary tool use. |
| `Bash` with `allowed-tools` glob-restricted pre-approval | Verified — documented current behavior; confirmed single-command (non-chained) invocations avoid false denials seen during development. |
| `Bash` reaching a path outside the target repository (e.g. a symlinked skill's helper script, or `--core` on a separate path) | **Live finding (2026-10-05, first live acceptance run)**: in a headless/no-approval-surface session, `Bash` was hard-denied for *any* path outside the target repository's own directory — including `${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py` itself, reached only via a symlink from outside that directory. `Read` tool access to the same external paths succeeded. This means `vcps_tool.py` may be entirely uninvokable via `Bash` in that session configuration regardless of `allowed-tools` patterns; the model correctly fell back to manual `Read`-based discovery and recorded the resulting evidence at a lower tier (`E1`) rather than fabricating the script's output. Not something `SKILL.md` wording can fix — it is a property of that session type, not of this adapter. |
| `${CLAUDE_SKILL_DIR}` for locating bundled scripts regardless of cwd | Verified against current documentation. |
| `Write`/`Edit` permission prompts gating actual mutation | Relied upon by design (deliberately not pre-approved in `allowed-tools`). **Live-exercised (2026-10-05, second live acceptance run)**: in a headless/no-approval-surface session, `Write` to `VCPS.md` and `.vcps/project.yaml` was denied as a "sensitive file" (Claude Code's own protection, distinct from the Bash-path-sandboxing finding above), and `Bash → vcps_tool.py atomic-write` was denied as outside `allowed-tools`, exactly as designed. The adapter correctly reported `SETUP_STATUS: BLOCKED` rather than fabricating success. This means mutating execution cannot be observed from a fully headless session at all — it requires an interactive session where a human actually approves the prompts, which is the adapter's intended operating mode, not a gap to work around. |
| `AskUserQuestion` for human checkpoints | Used by design; **not yet exercised in a live run**. |
| `context: fork` / subagent independence (`I2`) | Documented as available; **not exercised by this skill**, which runs inline (`I1`) by design — see `orchestration.md`. |
| Hosted CI inspection, external-provider verification, browser execution, production observation (`E3`-`E5` beyond local `Bash`/`Read`) | **Not available through this adapter today** — any check needing them records `NOT_RUN`/`INCONCLUSIVE` and the run stays `PARTIAL`. |

## `/vcps` router component

`vcps-router/` is a second, independent skill: it classifies a request
into one of the eight `workflows/README.md` intents and checks it against
the genuinely mechanical half of Core's risk-escalation contract
(`standard/risk-model.md` `VCPS-RISK-041` enforcement-path matches;
`VCPS-RISK-045` work-item file-overlap signals). See
`vcps-router/references/intent-classification.md` (resolves
`standard/open-questions.md` `OQ-011`) for the full mechanical/judgment
split and `evaluation/vcps-router.md` for its test record. It does **not**
dispatch to an automated executor for `FEATURE`/`REVIEW`/`BUG`/`TINY`/
`HOTFIX`/`AUDIT`/`RELEASE` — `vcps-audit/`, `vcps-review/`, and
`vcps-bug/` below are the first three of those seven to actually exist.

## The seven non-`SETUP` workflow components

`vcps-audit/` (`workflows/audit.md`), `vcps-review/`
(`workflows/review.md`), `vcps-bug/` (`workflows/bug.md`), `vcps-tiny/`
(`workflows/tiny.md`), `vcps-feature/` (`workflows/feature.md`),
`vcps-hotfix/` (`workflows/hotfix.md`), and `vcps-release/`
(`workflows/release.md`) are the full set of non-`SETUP` workflow
executors — roadmap Phase D closed in full. All seven lean on
**shared** mechanical helpers (`lib/vcps_evidence.py`, and `vcps-tiny/`/
`vcps-feature/` additionally reuse `vcps-router/`'s `escalation-check`/
`project-context`/`segmentation-scan`) rather than each vendoring their
own copy of Core-rule-specific logic — see `lib/README.md` for the full
rationale.

- `vcps-audit/` is read-only by design (`VCPS-WF-AUDIT-001`); zero
  `Write`/`Edit` in its `allowed-tools`, checked structurally.
- `vcps-review/`, `vcps-bug/`, `vcps-tiny/`, and `vcps-feature/` are
  mostly model judgment, reusing `lib/`'s and/or `vcps-router/`'s
  mechanical subcommands as sanity checks at specific steps rather than
  owning any new mechanical logic themselves.
- `vcps-bug/` deliberately ships **no** mechanical helper for
  `VCPS-G4-031`'s parent-fails/fix-passes regression confirmation, even
  though that check is itself genuinely mechanical — see
  `evaluation/vcps-bug.md` for why automating arbitrary command
  execution from inside a pre-approved script is a security anti-pattern
  this adapter avoids rather than a missed opportunity.
- `vcps-hotfix/` is the one exception that needed genuinely new
  mechanical logic: `lib/vcps_evidence.py`'s `lapsed-deferral-check`
  (plus an additive `deferral_follow_up` field on
  `templates/schemas/approval.schema.json`), because
  `VCPS-WF-HOTFIX-001`/`003`'s deferral-tracking rule is itself
  mechanical in a way nothing else in this adapter previously checked.
- `vcps-release/` similarly needed `lib/vcps_evidence.py`'s
  `release-readiness-check` for `VCPS-GATE-032`'s prerequisite-gate
  check, and **never performs an actual deployment** — that step is
  explicitly outside this skill's scope.

See `evaluation/vcps-audit.md`, `evaluation/vcps-review.md`,
`evaluation/vcps-bug.md`, `evaluation/vcps-tiny.md`,
`evaluation/vcps-feature.md`, `evaluation/vcps-hotfix.md`, and
`evaluation/vcps-release.md` for each component's full detail.

## Tests

- `tests/run_tests.py` — setup component (a sibling directory of
  `vcps-setup/`, a layout predating later components' addition).
- `vcps-router/tests/run_tests.py` — router component.
- `lib/tests/run_tests.py` — the shared evidence/reference helper
  (`evidence-inventory`/`gate-reference-check`/`orphan-check`/
  `baseline-history-check`/`record-history-check`/
  `antigaming-scan`/`antigaming-diff-scan`/`lapsed-deferral-check`/
  `release-readiness-check`),
  tested once here rather than duplicated under every skill that calls it.
- `vcps-audit/`, `vcps-review/`, `vcps-bug/`, `vcps-tiny/`,
  `vcps-feature/`, `vcps-hotfix/`, and `vcps-release/`'s own
  `tests/run_tests.py` — each skill's own structural soundness only
  (frontmatter, no stray `Write`/`Edit`, every referenced script path
  actually resolves, and each skill's own absolute claims — e.g.
  `vcps-release/`'s "never deploys," `vcps-hotfix/`'s "`HC-10`/`HC-03`
  not waivable" — are checked as literal text assertions, not merely
  implied); the mechanical logic any of them call is `lib/`'s or
  `vcps-router/`'s, tested in those components' own suites.

See each component's `evaluation/vcps-*.md` record for the current
pass/fail record, test classification (`STRUCTURAL_TEST` /
`SIMULATED_EXECUTION` / `LIVE_ADAPTER_EXECUTION`), and known limitations.
`tests/run_live.sh` drives a real `claude -p` invocation against a
disposable fixture for live checks on the setup component; it is opt-in
and not run as part of any structural/simulated suite. No equivalent
live-run script exists yet for any other component.

## Known limitations

- **No `LIVE_ADAPTER_EXECUTION` evidence for eight of the nine components**
  (router and all seven workflow executors). The setup adapter itself now
  has full live evidence for both its dry-run and mutating paths,
  including resume/idempotency and revision invalidation (Phase A,
  closed 2026-10-07; see `evaluation/claude-code-adapter.md`'s third live
  acceptance entry); every other component's model-driven judgment steps
  remain entirely unverified beyond structural soundness and the
  mechanical helpers' own `SIMULATED_EXECUTION` coverage.
- `adapters/install.py --vendor-core` (Phase K, closed 2026-10-07) vendors
  a pinned Core copy into `<target>/.vcps-core/`, which
  `vcps-setup/references/core-discovery.md`'s resolution order now checks;
  `--core <path>` remains supported for a one-off override. The installer
  also knows every sibling dependency (`lib/` for `vcps-audit/`,
  `vcps-review/`, `vcps-bug/`, `vcps-hotfix/`, `vcps-release/`,
  `vcps-tiny/`, and `vcps-feature/`; `vcps-setup/` additionally for
  `vcps-audit/`; `vcps-router/` additionally for `vcps-tiny/` and
  `vcps-feature/`) and auto-installs it when a subset is selected — see
  `adapters/README.md`'s "Installing an adapter" and
  `adapters/tests/run_tests.py`.
- `scripts/vcps_tool.py`'s `validate` subcommand now applies the real
  `jsonschema` Draft 2020-12 engine through `scripts/vcps_schema.py` against
  `templates/schemas/*.json` when invoked with `--core <path>`, plus a
  substantial set of cross-record checks (roadmap Phase E, both
  slices): ID uniqueness and full reference *resolution* (not just
  prefix-family), plan-hash recomputation, path-traversal/absolute-path
  rejection (including `commands[].working_directory`/
  `ci.config_paths`/`components[].path`), a secret/credential heuristic
  scan, risk-model "exactly one `PROJECT` profile" plus its
  `derived_level` matching `project.yaml.level.value`,
  `applicable_invariants` existence against `invariants.md`,
  `baseline.md` history append-only consistency, a `LEGACY` finding's
  first history entry being `OPEN`, `COMPLETE` requiring a non-null
  `baseline_ref`, a baseline observation's `check_id` matching a
  configured command, a gate `PASS` never citing a `REJECTED`
  checkpoint, `E0` evidence never being `PASS`, `RESOLVED` findings
  requiring remediation evidence, and `KNOWN_LIMITATION` implying
  `RISK_ACCEPTED`. This closes `templates/validation.md` items 1, 5, 9,
  11 (heuristic scope), 13, 14 in full, and most of items 2, 3, 4, 6, 7,
  10, 12. **Deliberately still open**, not merely forgotten:
  - an `evidence_policy.minimum_tier_overrides` key vocabulary Core
    never defines, so "never lowers the Core minimum" can't be checked
    without inventing one;
  - withdrawn-invariant-ID-reservation and invariant-removal-requires-
    `HC-08` tracking, which need historical/git-diff analysis beyond a
    point-in-time file read;
  - lifecycle history continuity and allowed transition checks, now covered
    with lifecycle.md's explicitly-permitted demotions represented in the
    validator and positive/negative regression cases;
  - `VCPS.md` pointer-consistency checking, since `VCPS.md` has no
    fixed machine-parseable format to check against (only a prose
    convention);
  - `AUDIT`-cannot-claim-implementation-gate-outcomes, left to model
    judgment given ambiguity in what counts as "claiming" vs. merely
    reviewing a gate record;
  - the full Gate 1–6 applicability-matrix cross-check against a
    work-item's actual `R`-class, and gate-chain supersession integrity
    (the latter is covered for `vcps-audit`'s own purposes by
    `lib/vcps_evidence.py`'s `gate-reference-check`, a different
    component, not duplicated in `vcps_tool.py`).

  Without `--core`, schema checks are explicitly reported
  `SKIPPED_NO_CORE_SCHEMAS`, never silently passed.

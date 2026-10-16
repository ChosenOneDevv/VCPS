# Security

VCPS is a stable Core specification with reference implementations at
different maturity levels. The repository is not a hardened product and
has no formal security response process or SLA. This document says what
is and isn't in scope, and how to report a problem until a more formal
process exists.

## Reporting a vulnerability

Report privately to the repository owner rather than opening a public
issue, if the hosting platform offers a private-disclosure or security-
advisory mechanism — use it. If it does not, or you are unsure, open an
issue describing the *category* of problem without reproduction details
that would let a third party exploit it before a fix lands, and ask for a
private channel to share specifics.

There is currently no dedicated security contact address, no bug bounty,
and no committed response-time SLA; the project does not have the
maintainer infrastructure that would make either credible to promise.
Reports will be reviewed as this project is actively developed;
treat the absence of a quick response as a resourcing limitation, not
indifference.

## What's in scope

- The adapter helper scripts that actually execute against a user's
  repository: `adapters/claude-code/vcps-setup/scripts/vcps_tool.py`,
  `adapters/claude-code/vcps-router/scripts/vcps_router.py`,
  `adapters/claude-code/lib/vcps_evidence.py`, and `adapters/install.py`.
  These are the only components in this repository that read or write
  real filesystem content outside the VCPS repository itself.
- The Claude Code and Codex skill definitions (`SKILL.md`,
  `agents/openai.yaml`) — specifically, anything that would let a skill
  execute an unapproved command, escape its declared `allowed-tools`
  scope, or read/write outside the intended target repository.
- Path handling: symlink traversal, `..`-escape, absolute-path injection,
  and similar classes against any of the above.
- Prompt-injection surface where target-repository content (files, CI
  logs, provider responses) could cause a skill to misreport evidence,
  fabricate a gate outcome, or take an unintended mutating action — see
  [`adapters/UNTRUSTED-CONTENT.md`](adapters/UNTRUSTED-CONTENT.md) for
  the existing operational boundary every skill is supposed to follow.

## What's out of scope / known, disclosed limitations

- **This is not a certified security control for your project.** Gate 5
  (`standard/gates/gate-5-security.md`) lists what a real project's own
  auth, authorization, injection, and upload controls need; VCPS cannot
  certify those for you, only check that evidence of them exists.
- **No dependency scanner has been run in this environment** (no network
  access to one at review time); `adapters/claude-code/lib/requirements.txt`
  pins PyYAML, checked by hand against its own advisory page at review
  time only, not continuously monitored.
- **Codex's sandbox behavior is not runtime-verified** — the capability
  mapping (`adapters/codex/references/capability-mapping.md`) is built
  from documentation, not an observed live session, and discloses a real
  gap: no per-skill mutation-scoping mechanism was found equivalent to
  Claude Code's `allowed-tools`.
- A full, systematic security audit against this project's own threat
  checklist is still open. `evaluation/security-audit.md` is the current,
  honestly-scoped working record of what has actually been reviewed and
  fixed so far (targeted, not exhaustive) — read its own stated scope
  before assuming any class of issue has been ruled out.

## Why this exists as a separate file

So a reporter does not have to read `evaluation/security-audit.md` in
full to know where to send a report, and so this project's own in-scope
surface (the parts that touch a user's real repository) is stated once,
plainly, rather than only implied by which files happen to take a
`--target` argument.

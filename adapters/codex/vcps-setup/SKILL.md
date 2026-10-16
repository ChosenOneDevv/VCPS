---
name: vcps-setup
description: Install, adopt, upgrade, or repair a VCPS (Vibe Coding Production Standard) installation in this repository by executing the canonical VCPS Core Setup Engine (workflows/setup.md). Use when the user asks to set up VCPS, adopt VCPS, run VCPS setup, check VCPS installation status, or resume an interrupted VCPS setup.
---

# Codex skill: vcps-setup

Before inspecting target-controlled content, read and follow
`../../UNTRUSTED-CONTENT.md`.

You are executing the **VCPS Setup Engine** as defined in
`workflows/setup.md` (§7, "Deterministic Setup Engine contract") in the
*current target repository* (the repository this session's working
directory is in now — this is almost never the VCPS specification
repository itself, except in VCPS's own development/dev-mode checkout).

This skill is an **adapter**. Per `standard/VCPS.md` `VCPS-CORE-003`, it
MUST NOT weaken, reinterpret, or omit a Core/Workflow requirement, and
MUST NOT define a second copy of VCPS. Where this file and a Core
document conflict, the Core document wins and the conflict is a defect
to report, not something to follow silently.

**Before anything else, read `adapters/codex/references/
capability-mapping.md` in full** if you have not already this session.
It resolves `standard/open-questions.md` `OQ-012` and states, with
sources, exactly where Codex's actual mechanisms differ from what this
text assumes — most importantly: **Codex's default sandbox
(`workspace-write` + `on-request`) permits in-workspace file writes
without a per-file prompt.** This is unlike the Claude Code adapter's
design, which relies on every mutation hitting a visible permission
prompt by default. **Before performing any mutating stage (Stage 4
onward) in this skill, confirm with the operator that either
`approval_policy = "untrusted"` is set, or a `.codex/rules/*.rules` entry
marks `vcps_tool.py atomic-write` as `decision = "prompt"`.** If neither
is confirmed, STOP before Stage 4 and report this explicitly as a
blocking precondition — do not proceed on the assumption that Codex's
default behavior provides the same mutation visibility the Claude Code
adapter relies on, because it does not.

## 0. Locate VCPS Core and the helper script (every invocation, first)

**Core discovery**, mirroring the Claude Code adapter's own dev-mode /
installed-mode distinction (`adapters/claude-code/vcps-setup/references/
core-discovery.md`, which is agent-neutral prose you may read directly —
nothing in it is Claude-specific except its own file path):

1. Run `git rev-parse --show-toplevel`. If `<toplevel>/standard/VCPS.md`
   exists, you are in VCPS's own dev-mode checkout; that directory is
   both the Core source and the target repository.
2. Otherwise, this is installed-into-target-repository mode. Locate Core
   in this order: `~/.agents/vcps-source` (installed globally by
   `adapters/install.py --adapter codex --global`), an explicit path the
   operator gives you, or — in this
   repository's current layout — `adapters/claude-code/` relative to
   this skill's own location if this skill was installed by copying the
   whole VCPS repository alongside the target (see "A deliberate
   cross-adapter sharing decision" in `adapters/codex/README.md`).
3. Verify any candidate Core path per `core-discovery.md`'s "Verifying a
   Core candidate" section before trusting it: `standard/VCPS.md`,
   `VERSION`, and `workflows/setup.md` must all exist and be non-empty.
   If verification fails, STOP and report `BLOCKED` with the exact paths
   checked — never fabricate Core content from memory.

**Helper script.** This skill invokes
`adapters/claude-code/vcps-setup/scripts/vcps_tool.py` directly — the
same physical file the Claude Code adapter uses, deliberately not
duplicated (see `adapters/codex/README.md`). Confirm it exists at that
path relative to the Core root located above before relying on it; if it
is missing, report `BLOCKED` rather than attempting to reconstruct its
logic from memory.

Invocation shape (identical to the Claude Code adapter's, since it is
the same script): `python3 <path-to-vcps_tool.py> <subcommand> --target
<path> [--core <path>] [flags]` — subcommand first.

## 1. Parse invocation and determine mode

Read `adapters/claude-code/vcps-setup/references/loading-map.md` for the
progressive-loading discipline this skill follows (load each Core/
workflow document only when the stage that needs it is reached — this
file is agent-neutral prose, safe to read directly). Then run:

```
python3 <vcps_tool.py path> detect --target <target repo> --core <core root>
```

Follow `workflows/setup.md` `VCPS-SETUP-001`–`004`/`050` exactly as the
Claude Code adapter's own `SKILL.md` would (read `workflows/setup.md`
itself for the full stage sequence — this skill does not restate it).

## 2. Dry-run before any mutation (`VCPS-SETUP-051`/`052`)

Mandatory, read-only, before Stage 4. Produces the plan this skill is
bound to for the rest of the run. No file is created or modified in this
step — confirm this is actually true by re-checking `git status` after,
not merely by intending it.

## 3. Stages 1–11

Follow `workflows/setup.md` §2 and §7 directly. Stages 1–3 are read-only
discovery (`E1`). **Stage 4 onward is mutating** — this is the point at
which the sandbox/approval precondition from this file's header MUST
already be confirmed, not merely assumed.

## 4. Resume, idempotency, and revision invalidation

Per `VCPS-SETUP-003`/`053`/`054`/`055`: this skill's own session state
(conversation history) is never the source of truth — re-read
`.vcps/project.yaml`'s `installation` object from disk every time,
including on a fresh session, per `VCPS-PORTABILITY-008`.

## Never

- Never proceed past Stage 3 without the operator having confirmed the
  sandbox/approval precondition stated at the top of this file.
- Never claim this skill's mutation behavior is as visible as the Claude
  Code adapter's by default — it is not, unless explicitly configured to
  be.
- Never fabricate Core content when a candidate path fails verification.
- Never report `SETUP_STATUS: COMPLETE` without having actually
  persisted and structurally validated every Stage 4+ output.

# Core discovery

This skill executes VCPS Core (`standard/`), Workflows (`workflows/`), and
the artifact contract (`templates/`). It must locate real copies of these
documents before doing anything else — it never recites Core rules from
its own memory or from this skill's text, and never fabricates Core
content to keep going when it cannot find the real document.

## Two operating modes

**A. VCPS repository development mode.** Claude Code's working directory
*is* (or is inside) the VCPS specification repository itself — the one
that contains `standard/VCPS.md`. This is how this adapter is developed
and tested. Detect it with a single `git rev-parse --show-toplevel`
followed by checking whether `<toplevel>/standard/VCPS.md` exists. If
found, that directory is both the Core source and — unusually — the
"target repository" being set up; Stage 1 discovery will observe this
repository's own tree, which is expected in dev mode.

**B. Installed-into-target-repository mode.** Claude Code's working
directory is an arbitrary external project that is *not* the VCPS
specification repository. The skill's own files (`SKILL.md`,
`references/`, `scripts/`) live under `${CLAUDE_SKILL_DIR}`, which —
because Skills can be symlinked (`.claude/skills/vcps-setup` → wherever
the real files live) — resolves reliably regardless of the target
repository's structure. But `${CLAUDE_SKILL_DIR}` is the *adapter's*
directory, not necessarily where a full copy of VCPS Core lives. The
supported resolution order is:

1. `--core <path>` argument, if given — use it verbatim (resolve relative
   to the target repository root if not absolute).
2. `<target repo root>/.vcps-core/` — `adapters/install.py --vendor-core`
   (Phase K, `evaluation/completion-roadmap.md`) copies `standard/`,
   `workflows/`, `templates/`, and `VERSION` here. Verify by checking
   `.vcps-core/standard/VCPS.md` exists before trusting it; do not assume
   it is current — `.vcps-core/VERSION` records the vendored Core version
   this was pinned at, which may have drifted from the adapter's own
   `SUPPORTED_VCPS_VERSIONS` if the target was never re-installed after a
   Core upgrade.
3. `${CLAUDE_SKILL_DIR}/../../..` — if this adapter is running from a
   symlinked-in copy of the VCPS dev repo's own
   `adapters/claude-code/vcps-setup/` directory, this resolves back to
   the VCPS repo root. Verify by checking `standard/VCPS.md` exists there
   before trusting it — do not assume the path shape; confirm.
4. Otherwise: STOP. Report `BLOCKED` — "VCPS Core location unknown; pass
   --core <path> to this skill, run `adapters/install.py --vendor-core`,
   or run it from inside/alongside a VCPS checkout." Do not guess a path,
   and do not proceed using only this skill's own text as if it were
   Core.

## Verifying a Core candidate

Before trusting any candidate Core path, confirm all of:

- `<path>/standard/VCPS.md` exists and is non-empty.
- `<path>/VERSION` exists, is non-empty, and its content is a version this
  adapter declares support for (see
  `adapters/claude-code/README.md` "Supported Core version"). A
  *different* supported version is not automatically an error —
  `VCPS-VER-011` drift handling applies — but a missing or unparseable
  `VERSION` is `BLOCKED`.
- `<path>/workflows/setup.md` exists and is non-empty — this is the Setup
  Engine this skill actually executes; without it there is nothing to
  run.

If any check fails, report exactly which one and stop. Never fall through
to a different candidate silently without saying so in the final report —
the user needs to know which Core copy, if any, you actually used.

## Locating the target repository

The target repository is the one being set up — almost always Claude
Code's own working directory. Confirm its boundary with a single
`git rev-parse --show-toplevel`. If that fails (no VCS), treat the working
directory itself as the boundary and record VCS absence per
`VCPS-SETUP-056`/`VCPS-SETUP-050` — a repository without VCS is valid
input to the Setup Engine, not an error condition to work around.

# Quick Start

VCPS Core is stable at `1.0.0`. Adapter support and live execution evidence
remain separate; see the [completion roadmap](evaluation/completion-roadmap.md).

## Requirements

- Codex CLI or Claude Code installed and configured.
- Python 3.10+, `curl`, and `tar` available on `PATH`.
- A target project directory. Run the command from that project, or pass
  `--target /path/to/project`.
- The VCPS helper scripts need pinned `PyYAML` and `jsonschema` dependencies.
  Install them into the Python environment used by the agent:

  ```sh
  python3 -m pip install -r adapters/claude-code/lib/requirements.txt
  ```

Codex mutation workflows require reviewing and configuring sandbox/approval
policy as described in [`adapters/codex/README.md`](adapters/codex/README.md).

## Install from GitHub

Run in a terminal to open the animated installer. It detects Codex and Claude
Code, lets you select agents, then choose project-wide or user-wide scope:

```sh
curl -fsSL https://raw.githubusercontent.com/ChosenOneDevv/VCPS/main/install.sh | bash
```

The installer downloads VCPS over HTTPS into a temporary directory, runs the
manifest-aware installer, removes temporary source, then verifies installed
files. It refuses to overwrite existing paths.

For direct non-interactive Codex installation into the current project:

```sh
curl -fsSL https://raw.githubusercontent.com/ChosenOneDevv/VCPS/main/install.sh | bash -s -- --adapter codex --target "$PWD"
```

For Claude Code:

```sh
curl -fsSL https://raw.githubusercontent.com/ChosenOneDevv/VCPS/main/install.sh | bash -s -- --adapter claude-code --target "$PWD" --mode copy --vendor-core
```

For Codex availability across all projects for the current OS user:

```sh
curl -fsSL https://raw.githubusercontent.com/ChosenOneDevv/VCPS/main/install.sh | bash -s -- --adapter codex --global
```

For Claude Code availability across the current user's projects:

```sh
curl -fsSL https://raw.githubusercontent.com/ChosenOneDevv/VCPS/main/install.sh | bash -s -- --adapter claude-code --global
```

User-wide installs place Codex skills under `~/.agents/skills/` and Claude
Code skills under `~/.claude/skills/`.

Codex skills are invoked as `$vcps`, `$vcps-setup`, and the other skill names.
Claude Code commands are invoked as `/vcps`, `/vcps-setup`, and so on. Use
`--plan` to preview paths/conflicts or `--verify` to check a completed install.
To install a branch or tag instead of `main`, pass `--ref <branch-or-tag>`.

## Install from a local checkout

For development or offline use, from a VCPS source checkout:

```sh
python3 adapters/install.py --adapter codex --target /path/to/project
```

For Claude Code, add `--mode copy --vendor-core` for project installs. Use
`--global` without `--target` for user-wide installs of either adapter.

## First run

1. Review the install report and confirm target path is correct.
2. Start the agent in target project and invoke `$vcps-setup` (Codex) or
   `/vcps-setup` (Claude Code).
3. Follow mode/risk summary and any human checkpoints.
4. Run validation command the skill reports. File verification proves copied
   adapter files match source; it does not prove every workflow is live or
   that project conforms to every VCPS rule.

## Existing project and troubleshooting

- Keep recoverable copy of existing project files before initial setup.
- SETUP diagnoses existing `.vcps/` records and versions. Do not manually
  change schema version; review migration plan and repo state first.
- If `--verify` reports mismatches, retain output and inspect files before
  changing target.
- Resolve path collisions deliberately. Do not remove a directory whose
  ownership is unclear.
- `BLOCKED`, `PARTIAL`, or `NOT_RUN` is a valid report of missing prerequisite
  or evidence gap. Never relabel it `PASS`.

See [adapter install details](adapters/README.md) and the
[support/evidence charter](evaluation/phase-0-charter.md).

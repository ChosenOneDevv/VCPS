#!/usr/bin/env python3
"""Structural and simulated-execution tests for the Claude Code /vcps-setup
adapter.

Classification (see evaluation/claude-code-adapter.md):
  STRUCTURAL_TEST     - static checks of adapter files, unit behavior of
                        vcps_tool.py.
  SIMULATED_EXECUTION - a script plays the adapter's mechanical role
                        against a disposable fixture by invoking the real
                        helper script in a fresh process. No model
                        involved. Not a live pass.

This script never invokes `claude -p` — that is tests/run_live.sh, a
separate, explicitly LIVE_ADAPTER_EXECUTION path.
"""

import json
import copy
import importlib.util
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ADAPTER_ROOT / "vcps-setup"
TOOL = SKILL_DIR / "scripts" / "vcps_tool.py"
RUN_LIVE = ADAPTER_ROOT / "tests" / "run_live.sh"
FINGERPRINT_FIXTURE = ADAPTER_ROOT / "tests" / "fingerprint_fixture.py"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def run_tool(target, subcommand, *rest, input_text=None):
    # Subcommand FIRST, then --target, then any subcommand-specific flags
    # (e.g. --core, --scope, --no-git) — vcps_tool.py's CLI shape is
    # "<subcommand> --target <path> [flags]", not flags-then-subcommand.
    cmd = [sys.executable, str(TOOL), subcommand, "--target", str(target)] + list(rest)
    return subprocess.run(cmd, capture_output=True, text=True, input=input_text, timeout=30)


# ---------------------------------------------------------------- STRUCTURAL

def test_structural():
    cat = "STRUCTURAL_TEST"

    live_runner = RUN_LIVE.read_text(encoding="utf-8")
    record(
        cat, "S16 live runner fingerprints both sides and preserves CLI failure status",
        "failed to fingerprint fixture before Claude invocation" in live_runner
        and "failed to fingerprint fixture after Claude invocation" in live_runner
        and "if (cd \"${FIXTURE_DIR}\" && claude" in live_runner
        and "fingerprint_fixture.py" in live_runner
        and "sha256sum" not in live_runner
        and "|| true)\"" not in live_runner,
    )
    shell_syntax = subprocess.run(["bash", "-n", str(RUN_LIVE)], capture_output=True, text=True)
    record(cat, "S17 live runner passes bash syntax validation",
           shell_syntax.returncode == 0, shell_syntax.stderr)
    try:
        compile(FINGERPRINT_FIXTURE.read_text(encoding="utf-8"), str(FINGERPRINT_FIXTURE), "exec")
        fingerprint_compiles = True
    except (OSError, SyntaxError):
        fingerprint_compiles = False
    record(cat, "S18 fixture fingerprint helper compiles and is present",
           FINGERPRINT_FIXTURE.is_file() and fingerprint_compiles)

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n", skill_text, re.S)
    record(cat, "S1 SKILL.md has frontmatter", fm_match is not None)
    frontmatter = fm_match.group(1) if fm_match else ""

    record(
        cat, "S2 disable-model-invocation: true present",
        "disable-model-invocation: true" in frontmatter,
    )

    bad_blanket = bool(
        re.search(r"(^|,\s*)(Write|Edit)(\s|,|$)", frontmatter)
    ) or bool(re.search(r"(^|,\s*)Bash(\s|,|$)", frontmatter.replace("Bash(", "BASHPATTERN(")))
    record(
        cat, "S3 no blanket Write/Edit/bare-Bash pre-approval",
        not bad_blanket, "frontmatter grants unrestricted mutation tool" if bad_blanket else "",
    )

    md_link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    broken_links = []
    for md_file in list(SKILL_DIR.rglob("*.md")) + [ADAPTER_ROOT / "README.md"]:
        text = md_file.read_text(encoding="utf-8")
        for link in md_link_re.findall(text):
            if link.startswith(("http://", "https://", "#")):
                continue
            link_path = link.split("#")[0]
            if not link_path:
                continue
            resolved = (md_file.parent / link_path).resolve()
            if not resolved.exists():
                broken_links.append(f"{md_file.relative_to(ADAPTER_ROOT)} -> {link}")
    record(cat, "S4 all relative markdown links resolve", not broken_links, "; ".join(broken_links))

    core_text = ""
    for relpath in ("standard/VCPS.md", "workflows/setup.md"):
        core_text += (REPO_ROOT / relpath).read_text(encoding="utf-8") + "\n"
    core_sentences = set(re.findall(r"[^.\n]{40,}\.", core_text))
    skill_all_text = skill_text
    for ref in SKILL_DIR.glob("references/*.md"):
        skill_all_text += "\n" + ref.read_text(encoding="utf-8")
    overlap = [s for s in core_sentences if s.strip() and s.strip() in skill_all_text]
    record(
        cat, "S5 no verbatim long-sentence duplication of Core text",
        len(overlap) == 0,
        f"{len(overlap)} overlapping sentence(s), e.g. {overlap[0][:80] if overlap else ''}",
    )

    vendor_names = ["anthropic", "openai", "gpt-4", "gpt-5", "gemini", "llama"]
    core_files = list((REPO_ROOT / "standard").glob("*.md")) + list(
        (REPO_ROOT / "standard" / "gates").glob("*.md")
    )
    vendor_hits = []
    for f in core_files:
        text = f.read_text(encoding="utf-8").lower()
        for v in vendor_names:
            if v in text:
                vendor_hits.append(f"{f.name}:{v}")
    record(cat, "S6 Core text names no specific agent vendor", not vendor_hits, "; ".join(vendor_hits))

    record(cat, "S7 vcps_tool.py exists and is syntactically valid", TOOL.is_file())
    if TOOL.is_file():
        compiled = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open({str(TOOL)!r}).read())"],
            capture_output=True, text=True,
        )
        record(cat, "S7b vcps_tool.py compiles", compiled.returncode == 0, compiled.stderr)

    schema_module = SKILL_DIR / "scripts" / "vcps_schema.py"
    record(cat, "S7c vcps_schema.py exists and is syntactically valid", schema_module.is_file())
    if schema_module.is_file():
        compiled = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open({str(schema_module)!r}).read())"],
            capture_output=True, text=True,
        )
        record(cat, "S7d vcps_schema.py compiles", compiled.returncode == 0, compiled.stderr)

    with tempfile.TemporaryDirectory() as td:
        res = run_tool(td, "detect")
        record(
            cat, "S8 Core discovery: empty dir with no config -> NEW, no crash",
            res.returncode == 0 and json.loads(res.stdout).get("mode") == "NEW",
            res.stdout + res.stderr,
        )

    orchestration = (SKILL_DIR / "references" / "orchestration.md").read_text(encoding="utf-8")
    record(
        cat, "S9 orchestration.md explicitly marks itself informative/non-Core",
        "informative" in orchestration.lower() and "not Core" in orchestration,
    )

    # S10: every vcps_tool.py invocation example documented in SKILL.md must
    # actually be ACCEPTED by the real argparse CLI (not merely name a real
    # subcommand). Found live (2026-10-05, VCPS commit 268cec8): SKILL.md
    # had no exact invocation example and the model guessed --repo instead
    # of --target, in the wrong flag order; SKILL.md also referenced a
    # nonexistent "plan" subcommand. This derives validation from the real
    # parser (per this ratification's own instruction to prefer that over a
    # second manually-maintained command list) by extracting every example
    # command from SKILL.md's fenced code blocks, substituting a real
    # disposable fixture for placeholders, and actually invoking each one —
    # asserting it is never rejected by argparse (exit code 2 / a "usage:"
    # line on stderr is argparse's own signature for "the flags I was given
    # don't parse", regardless of whether the target path itself exists).
    code_blocks = re.findall(r"```\n(.*?)\n```", skill_text, re.S)
    example_lines = [
        line.strip() for block in code_blocks for line in block.splitlines()
        if "vcps_tool.py" in line
    ]
    record(cat, "S10 SKILL.md contains at least one vcps_tool.py example to check", len(example_lines) > 0)

    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {"README.md": "# x\n"})
        bad_invocations = []
        for line in example_lines:
            cmd = line.replace("${CLAUDE_SKILL_DIR}/scripts/vcps_tool.py", str(TOOL))
            cmd = cmd.replace("<target-repo>", str(fixture)).replace("<core-path>", str(fixture))
            cmd = re.sub(r"<path>(\s*\[<path> \.\.\.\])?", str(fixture / "README.md"), cmd)
            is_pipe = cmd.startswith("echo ")
            if is_pipe:
                m = re.match(r"echo '(.*)' \| (.*)$", cmd)
                if not m:
                    continue
                stdin_text, real_cmd = m.group(1), m.group(2)
            else:
                stdin_text, real_cmd = None, cmd
            if "<" in real_cmd or ">" in real_cmd:
                continue  # unsubstituted placeholder we don't have a fixture for; skip, don't guess
            try:
                parts = shlex.split(real_cmd)
            except ValueError:
                bad_invocations.append((line, "could not shlex-split"))
                continue
            proc = subprocess.run(
                [sys.executable] + parts, capture_output=True, text=True,
                input=stdin_text, timeout=15,
            )
            if proc.returncode == 2 or "usage:" in proc.stderr.lower():
                bad_invocations.append((line, proc.stderr.strip()[:200]))
        record(
            cat, "S10b every SKILL.md vcps_tool.py example is accepted by the real argparse CLI",
            not bad_invocations, f"rejected: {bad_invocations}",
        )

    # S10c: the allowed-tools frontmatter pattern for each real, non-mutating
    # subcommand must literally contain "vcps_tool.py <subcommand> " as a
    # substring, matching the now-enforced subcommand-first invocation shape
    # (and NOT matching a flags-before-subcommand shape, which this
    # ratification deliberately removed as unverified-safe).
    help_text = subprocess.run(
        [sys.executable, str(TOOL), "--help"], capture_output=True, text=True
    ).stdout
    real_subcommands = set()
    m = re.search(r"\{([a-z,\-]+)\}", help_text)
    if m:
        real_subcommands = set(m.group(1).split(","))
    mutating_subcommands = {"atomic-write", "migrate-project-schema", "rollback-project-schema"}
    non_mutating = real_subcommands - mutating_subcommands
    missing_from_allowed_tools = [
        s for s in non_mutating if f"vcps_tool.py {s} *" not in frontmatter
    ]
    record(
        cat, "S10c allowed-tools pre-approves every non-mutating subcommand, subcommand-first",
        not missing_from_allowed_tools, f"missing: {missing_from_allowed_tools}",
    )
    record(
        cat, "S10d atomic-write (mutating) is never blanket pre-approved",
        f"vcps_tool.py atomic-write" not in frontmatter,
    )
    record(
        cat, "S10e migrate-project-schema (mutating) is never blanket pre-approved",
        f"vcps_tool.py migrate-project-schema" not in frontmatter,
    )
    record(
        cat, "S10f rollback-project-schema (mutating) is never blanket pre-approved",
        f"vcps_tool.py rollback-project-schema" not in frontmatter,
    )


# ------------------------------------------------------------ SIMULATED EXEC

def make_fixture(tmp, files, git=True, commit=True):
    root = Path(tmp)
    for relpath, content in files.items():
        p = root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    if git:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        if commit:
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True)
    return root


def test_simulated():
    cat = "SIMULATED_EXECUTION"

    # 1. Simple NEW repository
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {"README.md": "# demo\n"})
        res = run_tool(fixture, "detect")
        mode = json.loads(res.stdout).get("mode") if res.returncode == 0 else None
        record(cat, "1 simple NEW repo -> mode NEW", mode == "NEW", res.stdout + res.stderr)

    # 2. Dirty legacy repository: staged + modified + untracked + deleted
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {"a.txt": "one\n", "b.txt": "two\n", "package.json": "{}\n"},
        )
        (fixture / "a.txt").write_text("one changed\n")
        (fixture / "c_untracked.txt").write_text("new\n")
        (fixture / "b.txt").unlink()
        res = run_tool(fixture, "inventory")
        inv = json.loads(res.stdout) if res.returncode == 0 else {}
        entries = {e["path"]: e["vcs"] for e in inv.get("dirty_tree_entries", [])}
        ok = (
            entries.get("a.txt") == " M"
            and entries.get("b.txt") == " D"
            and entries.get("c_untracked.txt") == "??"
        )
        record(cat, "2 dirty legacy repo classified by VCS state", ok, json.dumps(entries))

    # 3. "Level-3-like" fixture: just confirm manifest/CI signal detection
    # (risk classification itself is model judgment, not tool judgment).
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {
                "package.json": "{}\n",
                ".github/workflows/ci.yml": "name: ci\n",
                "src/ledger.js": "// balances\n",
            },
        )
        res = run_tool(fixture, "inventory")
        inv = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = inv.get("manifest_signals", {}).get("package.json") and inv.get(
            "ci_signals", {}
        ).get(".github/workflows")
        record(cat, "3 manifest + CI signals detected for risk-bearing fixture", bool(ok), json.dumps(inv))

    # Git status honors a repository-local core.fsmonitor executable by
    # default. Helpers only need read-only Git facts and must not run project
    # configuration as code while inspecting a target.
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {"tracked.txt": "safe\n"})
        marker = Path(td) / "fsmonitor-was-run"
        hook = Path(td) / "controlled-fsmonitor"
        hook.write_text(
            "#!/bin/sh\nprintf called > \"$1\"\nprintf '\\0'\n", encoding="utf-8"
        )
        hook.chmod(0o700)
        subprocess.run(
            ["git", "-C", str(fixture), "config", "core.fsmonitor", f"{hook} {marker}"],
            check=True,
        )
        res = run_tool(fixture, "inventory")
        record(cat, "3b target core.fsmonitor command is not executed during inventory",
               res.returncode == 0 and not marker.exists(), res.stdout + res.stderr)

    # 4. REPAIR: malformed project.yaml (duplicate key)
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {".vcps/project.yaml": "schema_version: '0.2.0'\nschema_version: '0.2.0'\n"},
        )
        res = run_tool(fixture, "detect", "--core", str(REPO_ROOT))
        mode = json.loads(res.stdout).get("mode") if res.returncode == 0 else None
        record(cat, "4 malformed config (duplicate key) -> REPAIR", mode == "REPAIR", res.stdout)

    # 5. UPGRADE: schema 0.1.0
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {
                ".vcps/project.yaml": (
                    "schema_version: '0.1.0'\n"
                    "artifact_layout_version: '0.1.0'\n"
                    "vcps_version: '0.1.0-draft'\n"
                )
            },
        )
        res = run_tool(fixture, "detect", "--core", str(REPO_ROOT))
        mode = json.loads(res.stdout).get("mode") if res.returncode == 0 else None
        record(cat, "5 project schema 0.1.0 -> UPGRADE", mode == "UPGRADE", res.stdout)

    # 6. Unsupported newer schema -> REPAIR, read-only diagnosis, no downgrade
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {
                ".vcps/project.yaml": (
                    "schema_version: '9.9.9'\n"
                    "artifact_layout_version: '0.1.0'\n"
                    "vcps_version: '0.1.0-draft'\n"
                )
            },
        )
        res = run_tool(fixture, "detect", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = data.get("mode") == "REPAIR" and data.get("project_schema_relation") == "UNSUPPORTED"
        record(cat, "6 unsupported newer project schema -> REPAIR, flagged UNSUPPORTED", ok, res.stdout)

    # 6b. AHEAD vcps_version (project newer than this executor) -> read-only
    #     REPAIR diagnosis, never auto-downgraded (VCPS-SETUP-002/VCPS-VER-011).
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {
                ".vcps/project.yaml": (
                    "schema_version: '0.2.0'\n"
                    "artifact_layout_version: '0.1.0'\n"
                    "vcps_version: '9.9.9-draft'\n"
                )
            },
        )
        res = run_tool(fixture, "detect", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = data.get("mode") == "REPAIR" and data.get("vcps_version_relation") == "AHEAD"
        record(cat, "6b AHEAD vcps_version -> read-only REPAIR, no downgrade", ok, res.stdout)

    # 6c. Resume is NOT a fifth mode (VCPS-SETUP-003): a consistent
    #     PARTIAL/BLOCKED config must route to RESUME with mode left null,
    #     never reported as if "RESUME" were itself a mode value.
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(
            td,
            {
                ".vcps/project.yaml": (
                    "schema_version: '0.2.0'\n"
                    "artifact_layout_version: '0.1.0'\n"
                    "vcps_version: '0.1.0-draft'\n"
                    "installation:\n  status: PARTIAL\n  stage: 5\n"
                )
            },
        )
        res = run_tool(fixture, "detect", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = data.get("route") == "RESUME" and data.get("mode") is None
        record(cat, "6c resume is a route, not a fifth mode (mode stays null)", ok, res.stdout)

    # 7. UNKNOWN untracked binary file: hashed, not read as text, left untouched
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {"README.md": "# x\n"})
        binpath = fixture / "blob.bin"
        binpath.write_bytes(bytes(range(256)) * 4)
        before = binpath.read_bytes()
        res = run_tool(fixture, "fingerprint", "--scope", ".")
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        entry = next((e for e in data.get("entries", []) if e["path"] == "blob.bin"), None)
        after = binpath.read_bytes()
        ok = (
            entry is not None
            and entry["type"] == "file"
            and entry["vcs"] == "??"
            and before == after
        )
        record(cat, "7 unknown untracked binary hashed, bytes unchanged", ok, json.dumps(entry))

    # 9. Destructive migration: HC-02 is in the catalog and the tool never
    #    executes arbitrary migration commands (it has no such subcommand).
    hc_text = (REPO_ROOT / "standard" / "human-checkpoints.md").read_text(encoding="utf-8")
    ok = "HC-02" in hc_text and "destructive" in hc_text.lower()
    record(cat, "9 HC-02 (destructive migration) present in checkpoint catalog", ok)
    # This checks for a subcommand that would run an arbitrary/destructive
    # data-migration *script found in the target repo* (HC-02's actual
    # concern) -- not `migrate-project-schema` (Phase K), which only ever
    # rewrites VCPS's own project.yaml via a fixed, narrow, mechanical
    # field transform per templates/contract.md and never executes
    # anything the target repository supplies. A bare substring check for
    # "migrate" would false-positive on that name, so this parses the
    # real subcommand list instead (same technique as S10c).
    dangerous_migration_subcommands = {"migrate", "apply-migration", "run-migration", "run-migration-script"}
    help_text_9b = subprocess.run(
        [sys.executable, str(TOOL), "--help"], capture_output=True, text=True
    ).stdout
    m9b = re.search(r"\{([a-z,\-]+)\}", help_text_9b)
    real_subcommands_9b = set(m9b.group(1).split(",")) if m9b else set()
    has_migration_exec = bool(real_subcommands_9b & dangerous_migration_subcommands)
    record(cat, "9b helper script has no arbitrary/destructive migration-script-execution subcommand", not has_migration_exec,
           str(real_subcommands_9b))

    # 10. Interrupted + resume: stage_events journal -> earliest incomplete stage
    with tempfile.TemporaryDirectory() as td:
        events = [
            {"stage": 1, "event_state": "COMPLETED"},
            {"stage": 2, "event_state": "COMPLETED"},
            {"stage": 3, "event_state": "COMPLETED"},
            {"stage": 4, "event_state": "COMPLETED"},
            {"stage": 5, "event_state": "COMPLETED"},
            {"stage": 6, "event_state": "BLOCKED", "reason": "DECISION"},
        ]
        content = json.dumps(
            {
                "schema_version": "0.2.0",
                "artifact_layout_version": "0.1.0",
                "vcps_version": "0.1.0-draft",
                "installation": {
                    "status": "BLOCKED",
                    "stage": 6,
                    "stage_events": events,
                },
            }
        ) + "\n"
        fixture = make_fixture(td, {".vcps/project.yaml": content})
        res = run_tool(fixture, "resume-status")
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = (
            data.get("earliest_incomplete_stage") == 6
            and data.get("blocked_stages", {}).get("6") == "DECISION"
        )
        record(cat, "10 resume-status finds earliest incomplete stage from journal", ok, res.stdout)

    # 10b. A completed stage whose recorded input fingerprint no longer
    #      matches the current repository must be reported stale, not
    #      trusted as still COMPLETED (VCPS-SETUP-054).
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {"manifest.txt": "original\n"}, git=False)
        fp_before = json.loads(
            run_tool(fixture, "fingerprint", "--scope", "manifest.txt", "--no-git").stdout
        )["fingerprint"]
        events = [
            {
                "stage": 1, "event_state": "COMPLETED",
                "input_scope": ["manifest.txt"], "input_fingerprint": fp_before,
            },
            {"stage": 2, "event_state": "COMPLETED"},
        ]
        content = json.dumps(
            {
                "schema_version": "0.2.0", "artifact_layout_version": "0.1.0",
                "vcps_version": "0.1.0-draft",
                "installation": {"status": "PARTIAL", "stage": 2, "stage_events": events},
            }
        ) + "\n"
        (fixture / ".vcps").mkdir()
        (fixture / ".vcps" / "project.yaml").write_text(content, encoding="utf-8")
        (fixture / "manifest.txt").write_text("changed after stage 1 completed\n", encoding="utf-8")
        res = run_tool(fixture, "resume-status", "--no-git")
        data = json.loads(res.stdout) if res.returncode == 0 else {}
        ok = (
            "1" in data.get("stale_stages", {})
            and data.get("earliest_incomplete_stage") == 1
            and 1 not in data.get("completed_stages", [])
        )
        record(cat, "10b resume-status detects stale completed stage on changed input", ok, res.stdout)

    # 11. Atomic persistence: malformed replacement is rejected without
    #     touching the target (write to temp + validate + rename).
    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {}, git=False)
        original = "---\nschema_version: '0.2.0'\n---\n"
        (fixture / ".vcps").mkdir()
        (fixture / ".vcps" / "project.yaml").write_text(original, encoding="utf-8")
        res = run_tool(
            fixture, "atomic-write", "--file", ".vcps/project.yaml", "--stdin",
            input_text="schema_version: '0.2.0'\nschema_version: broken\n",
        )
        after = (fixture / ".vcps" / "project.yaml").read_text(encoding="utf-8")
        # atomic-write itself does not validate content (that is `validate`'s
        # job) but it must never leave a partially-written file: the file is
        # either fully the old content or fully the new content, never a mix.
        ok = after in (original, "schema_version: '0.2.0'\nschema_version: broken\n")
        record(cat, "11 atomic-write never leaves a partial/mixed file", ok, repr(after))

    # Round-trip: plan-hash recomputation matches `validate`
    with tempfile.TemporaryDirectory() as td:
        plan = {"mode": "NEW", "base_revision": "deadbeef"}
        ph = json.loads(run_tool(td, "plan-hash", input_text=json.dumps(plan)).stdout)["sha256"]
        plan_with_hash = dict(plan, sha256=ph)
        content = json.dumps(
            {
                "schema_version": "0.2.0",
                "artifact_layout_version": "0.1.0",
                "vcps_version": "0.1.0-draft",
                "project": {}, "level": {}, "installation": {"plan": plan_with_hash},
                "repository": {}, "stack": {}, "commands": {}, "ci": {},
                "critical_domains": {}, "applicable_invariants": [],
                "evidence_policy": {}, "baseline_ref": None, "config_history": [],
                "lifecycle": {},
            }
        ) + "\n"
        fixture = make_fixture(td, {".vcps/project.yaml": content})
        res = run_tool(fixture, "validate")
        data = json.loads(res.stdout)
        plan_errors = [e for e in data.get("errors", []) if "sha256" in e]
        record(cat, "11b validate recomputes and matches a correct plan hash", not plan_errors, json.dumps(data))

    # 12. Symlink-safe directory fingerprinting (regression for the defect
    # where a symlinked directory was silently dropped from recursive
    # expansion -- making its retargeting invisible to the stage input
    # fingerprint -- and where a scope path reaching through a symlink, or
    # containing '..'/an absolute path, dereferenced content outside the
    # repository boundary). Covers: regular file, regular directory,
    # symlink to file, symlink to directory, symlink inside a recursively
    # fingerprinted directory, broken symlink, symlink loop, symlink
    # escaping the repository boundary, nested symlink, path traversal.
    with tempfile.TemporaryDirectory() as td:
        outside = Path(td) / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("secret\n", encoding="utf-8")
        repo = Path(td) / "repo"
        (repo / "d").mkdir(parents=True)
        (repo / "f.txt").write_text("hello\n", encoding="utf-8")
        (repo / "d" / "a.txt").write_text("a\n", encoding="utf-8")
        (repo / "d" / "flink").symlink_to(repo / "f.txt")
        (repo / "d" / "dirlink").symlink_to(outside, target_is_directory=True)
        (repo / "d" / "broken").symlink_to("nowhere")
        (repo / "d" / "loop1").symlink_to("loop2")
        (repo / "d" / "loop2").symlink_to("loop1")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)

        res = run_tool(repo, "fingerprint", "--scope", ".")
        data = json.loads(res.stdout)
        entries = {e["path"]: e for e in data.get("entries", [])}
        ok = (
            res.returncode == 0
            and entries.get("d/dirlink", {}).get("type") == "symlink"
            and entries.get("d/flink", {}).get("type") == "symlink"
            and entries.get("d/broken", {}).get("type") == "symlink"
            and entries.get("d/loop1", {}).get("type") == "symlink"
            and entries.get("d/loop2", {}).get("type") == "symlink"
            and "d/dirlink/secret.txt" not in entries
        )
        record(
            cat,
            "12a fingerprint records every symlink type, never its content",
            ok, json.dumps(entries, default=str),
        )

        # Retargeting the symlinked directory MUST change the fingerprint
        # of a scope that recursively includes it (VCPS-SETUP-054: a
        # changed input must be detected, not silently trusted).
        fp_before = data["fingerprint"]
        (repo / "d" / "dirlink").unlink()
        (repo / "d" / "dirlink").symlink_to(Path(td), target_is_directory=True)
        res2 = run_tool(repo, "fingerprint", "--scope", ".")
        fp_after = json.loads(res2.stdout)["fingerprint"]
        record(
            cat,
            "12b retargeting a symlinked directory changes the recursive fingerprint",
            fp_before != fp_after,
            f"before={fp_before} after={fp_after}",
        )

        # A scope item that is itself a symlink to a directory must not be
        # followed into -- it is recorded as the symlink, full stop.
        res3 = run_tool(repo, "fingerprint", "--scope", "d/dirlink")
        data3 = json.loads(res3.stdout)
        entries3 = {e["path"]: e["type"] for e in data3.get("entries", [])}
        record(
            cat,
            "12c scope item that is a symlink to a directory is not followed",
            entries3 == {"d/dirlink": "symlink"},
            json.dumps(entries3),
        )

        # A scope item reaching *through* a symlinked directory component
        # must stop at the symlink boundary, never read what lies beyond it.
        res4 = run_tool(repo, "fingerprint", "--scope", "d/dirlink/secret.txt")
        data4 = json.loads(res4.stdout)
        entries4 = {e["path"]: e["type"] for e in data4.get("entries", [])}
        record(
            cat,
            "12d scope path through a symlinked directory stops at the boundary",
            entries4 == {"d/dirlink": "symlink"},
            json.dumps(entries4),
        )

        # Path traversal and absolute scope paths must fail closed, not
        # silently resolve outside the repository.
        res5 = run_tool(repo, "fingerprint", "--scope", "../outside/secret.txt")
        record(
            cat,
            "12e '..' traversal in scope is rejected, not resolved",
            res5.returncode != 0 and "error" in (res5.stdout or ""),
            res5.stdout,
        )
        res6 = run_tool(repo, "fingerprint", "--scope", str(outside / "secret.txt"))
        record(
            cat,
            "12f absolute path in scope is rejected, not resolved",
            res6.returncode != 0 and "error" in (res6.stdout or ""),
            res6.stdout,
        )

    # 13. JSON Schema validation (roadmap Phase E: wiring the Phase B
    # schemas into vcps_tool.py validate() itself). All cases exercised
    # against copies of the real, already-schema-conformant worked
    # example at templates/examples/project, mutated one way at a time --
    # proving the schema check has real teeth against realistic records,
    # not just synthetic minimal fixtures.
    worked_example = REPO_ROOT / "templates" / "examples" / "project"

    def copy_worked_example(dest):
        shutil.copytree(worked_example, dest)
        return Path(dest)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13a worked example validates clean with --core (schema checks active)",
               data["ok"] is True and data["schema_validation_status"] == "CHECKED", res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        res = run_tool(fixture, "validate")
        data = json.loads(res.stdout)
        record(cat, "13b without --core, schema checks are SKIPPED (not silently PASSED), mechanical checks still run",
               data["ok"] is True and data["schema_validation_status"] == "SKIPPED_NO_CORE_SCHEMAS"
               and data["ids_seen"] == 14, res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {".vcps/project.yaml": "date: 2026-10-07\n"})
        res = run_tool(fixture, "validate")
        data = json.loads(res.stdout)
        record(cat, "13b1 implicit YAML timestamp objects are rejected",
               data["ok"] is False and any("implicit YAML timestamp" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {".vcps/project.yaml": "1: invalid-key\n"})
        res = run_tool(fixture, "validate")
        data = json.loads(res.stdout)
        record(cat, "13b2 non-string YAML mapping keys are rejected",
               data["ok"] is False and any("non-string key" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "findings" / "FND-00000000-0000-4000-8000-00000000000c.md"
        p.write_text(p.read_text().replace("severity: CRITICAL", "severity: SEVERE"), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13c invalid enum value (severity: SEVERE) is rejected by schema validation",
               data["ok"] is False and any("SEVERE" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "evidence" / "EVD-00000000-0000-4000-8000-000000000002.md"
        p.write_text(p.read_text().replace("tier: E2", "tier: E2\nunexpected_field: nope", 1), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13d unknown additional field is rejected (additionalProperties: false)",
               data["ok"] is False and any("unexpected_field" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "bugs" / "BUG-00000000-0000-4000-8000-000000000005.md"
        p.write_text(
            p.read_text().replace(
                'defect_ref: "FND-00000000-0000-4000-8000-00000000000c"',
                'defect_ref: "EVD-00000000-0000-4000-8000-00000000000d"',
            ),
            encoding="utf-8",
        )
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13e reference field pointing at the wrong ID-prefix family is rejected",
               data["ok"] is False and any("expected one of ['FND']" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "project.yaml"
        p.write_text(
            p.read_text().replace("remote: null", 'remote: "https://user:AKIAIOSFODNN7EXAMPLE@github.com/x/y.git"'),
            encoding="utf-8",
        )
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13f credentialed-URL-shaped value in an otherwise-valid field is flagged as a possible secret",
               data["ok"] is False and any("possible secret" in e and "credentialed URL" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "bugs" / "BUG-00000000-0000-4000-8000-000000000005.md"
        p.write_text(p.read_text().replace('"src/sync.js"', '"../outside/evil.js"', 1), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13g '..' path traversal in a path-bearing field (scope.files) is rejected",
               data["ok"] is False and any("must not contain '..'" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "risk-model.md"
        text = p.read_text()
        dup_block = (
            '  - scope: "PROJECT"\n'
            "    dimensions:\n"
            "      D1: {rating: 0}\n      D2: {rating: 0}\n      D3: {rating: 0}\n"
            "      D4: {rating: 0}\n      D5: {rating: 0}\n      D6: {rating: 0}\n"
            "      D7: {rating: 0}\n      D8: {rating: 0}\n      D9: {rating: 0}\n"
            "    derived_level: L1\n    rationale: duplicate\n"
        )
        text = text.replace('  - scope: "PROJECT"\n', dup_block + '  - scope: "PROJECT"\n', 1)
        p.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "13h a second PROJECT-scope risk profile is rejected (exactly one required)",
               data["ok"] is False and any("exactly one PROJECT-scope profile" in e for e in data["errors"]),
               res.stdout)

    # 14. Phase E slice 2: cross-record semantic checks (templates/
    # validation.md items 3-5/9), again against mutated copies of the
    # real Phase B worked example.
    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "bugs" / "BUG-00000000-0000-4000-8000-000000000005.md"
        p.write_text(
            p.read_text().replace(
                'defect_ref: "FND-00000000-0000-4000-8000-00000000000c"',
                'defect_ref: "FND-00000000-0000-4000-8000-ffffffffffff"',
            ),
            encoding="utf-8",
        )
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14a a correctly-prefixed but nonexistent reference is rejected (resolution, not just prefix)",
               data["ok"] is False and any("does not resolve to any record found" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "project.yaml"
        p.write_text(p.read_text().replace('- "INV-001"', '- "INV-999"'), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14b an applicable_invariants entry not registered in invariants.md is rejected",
               data["ok"] is False and any("does not exist in invariants.md" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "risk-model.md"
        p.write_text(p.read_text().replace("derived_level: L2", "derived_level: L3"), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14c project.yaml level mismatched against risk-model.md's derived_level is rejected",
               data["ok"] is False and any("does not match" in e and "derived_level" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "project.yaml"
        p.write_text(p.read_text().replace('working_directory: "."', 'working_directory: "../outside"'), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14d a command's working_directory with '..' traversal is rejected",
               data["ok"] is False and any("working_directory" in e and "must not contain" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "baseline.md"
        text = p.read_text()
        text = text.replace(
            "history: []",
            'history:\n  - type: RESOLVE_OBSERVATION\n    timestamp: "2026-10-06T00:00:00Z"\n'
            '    reason: "x"\n    observation_id: "BLO-00000000-0000-4000-8000-ffffffffffff"\n'
            '    resolution_finding_ref: "FND-00000000-0000-4000-8000-00000000000c"',
        )
        p.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14e RESOLVE_OBSERVATION referencing an observation_id not in the original array is rejected",
               data["ok"] is False and any("not in the original observations array" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "findings" / "FND-00000000-0000-4000-8000-000000000001.md"
        text = p.read_text()
        text = text.replace(
            '  - timestamp: "2026-08-03T09:20:00Z"\n    to_status: OPEN',
            '  - timestamp: "2026-08-03T09:20:00Z"\n    to_status: RISK_ACCEPTED',
        )
        p.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14f a LEGACY finding whose first history entry is not OPEN is rejected",
               data["ok"] is False and any("must be OPEN" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "findings" / "FND-00000000-0000-4000-8000-00000000000c.md"
        p.write_text(
            p.read_text().replace(
                'remediation_evidence_refs:\n    - "EVD-00000000-0000-4000-8000-00000000000d"',
                "remediation_evidence_refs: []",
            ),
            encoding="utf-8",
        )
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14g a RESOLVED finding with no remediation evidence is rejected",
               data["ok"] is False and any("remediation_evidence_refs" in e and "minItems" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "findings" / "FND-00000000-0000-4000-8000-00000000000e.md"
        p.write_text(p.read_text().replace("status: RISK_ACCEPTED", "status: OPEN", 1), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14h a KNOWN_LIMITATION finding not in status RISK_ACCEPTED is rejected",
               data["ok"] is False and any("RISK_ACCEPTED" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "evidence" / "EVD-00000000-0000-4000-8000-000000000002.md"
        p.write_text(p.read_text().replace("tier: E2", "tier: E0", 1), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14i an E0-tier evidence record with result PASS is rejected",
               data["ok"] is False, res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "project.yaml"
        p.write_text(p.read_text().replace('baseline_ref: ".vcps/baseline.md"', "baseline_ref: null"), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14j COMPLETE installation with a null baseline_ref is rejected",
               data["ok"] is False and any("baseline_ref is still null" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "baseline.md"
        p.write_text(p.read_text().replace('check_id: "test"', 'check_id: "nonexistent_check"'), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14k baseline observation referencing an unconfigured check_id is rejected",
               data["ok"] is False and any("not among project.yaml's configured commands" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p1 = fixture / ".vcps" / "approvals" / "HCR-00000000-0000-4000-8000-000000000009.md"
        p1.write_text(p1.read_text().replace("decision: APPROVED_WITH_CONDITIONS", "decision: REJECTED"), encoding="utf-8")
        p2 = fixture / ".vcps" / "gates" / "GATE-00000000-0000-4000-8000-000000000008.md"
        p2.write_text(
            p2.read_text().replace(
                "checkpoint_refs: []",
                'checkpoint_refs: ["HCR-00000000-0000-4000-8000-000000000009"]',
            ),
            encoding="utf-8",
        )
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14l a gate outcome PASS citing a REJECTED checkpoint decision is rejected",
               data["ok"] is False and any("whose recorded decision is REJECTED" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "features" / "FEAT-00000000-0000-4000-8000-000000000003.md"
        p.write_text(p.read_text().replace(
            "from_state: SPECIFIED\n    to_state: CODED",
            "from_state: PROPOSED\n    to_state: CODED",
            1,
        ), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14m FEATURE lifecycle cannot skip SPECIFIED on an L2 feature",
               data["ok"] is False and any("skips or reverses" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "features" / "FEAT-00000000-0000-4000-8000-000000000003.md"
        p.write_text(p.read_text().replace(
            '  state: PENDING\n  decision_ref: null',
            '  state: APPROVED\n  decision_ref: "HCR-00000000-0000-4000-8000-000000000009"',
        ), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14n FEATURE acceptance projection must cite HC-14 and match its decision",
               data["ok"] is False and any("not an HC-14 decision" in e for e in data["errors"])
               and any("does not equal HC-14 decision" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "features" / "FEAT-00000000-0000-4000-8000-000000000003.md"
        p.write_text(p.read_text().replace("lifecycle_state: VERIFIED", "lifecycle_state: CODED", 1),
                     encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14o FEATURE current state must equal its last history event",
               data["ok"] is False and any("does not match the latest history state" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        p = fixture / ".vcps" / "features" / "FEAT-00000000-0000-4000-8000-000000000003.md"
        p.write_text(p.read_text().replace("to_state: PROPOSED", "to_state: CODED", 1),
                     encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14p FEATURE history must start at PROPOSED (or permitted L1 collapse)",
               data["ok"] is False and any("must establish an initial state" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        risk = fixture / ".vcps/risk-model.md"
        project.write_text(project.read_text().replace("value: L2", "value: L1", 1), encoding="utf-8")
        risk.write_text(risk.read_text().replace("derived_level: L2", "derived_level: L1", 1),
                        encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14q risk-derived level cannot understate a dimension rated 2",
               data["ok"] is False and any("dimension-based minimum 'L2'" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        config = yaml.safe_load(project.read_text(encoding="utf-8"))
        config["installation"]["plan_history"] = [copy.deepcopy(config["installation"]["plan"])]
        project.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14r active and archived setup plans cannot reuse the same hash",
               data["ok"] is False and any("duplicates an active or archived plan hash" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        finding = fixture / ".vcps/findings/FND-00000000-0000-4000-8000-00000000000e.md"
        misplaced = fixture / ".vcps/evidence/FND-00000000-0000-4000-8000-00000000000e.md"
        finding.rename(misplaced)
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14s correctly prefixed reference resolving to the wrong record type is rejected",
               data["ok"] is False and any("expected one of ['findings']" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        evidence = fixture / ".vcps/evidence/EVD-00000000-0000-4000-8000-00000000000d.md"
        evidence.write_text(evidence.read_text().replace("result: PASS", "result: NOT_RUN", 1),
                            encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14t PASS gate cannot cite evidence with a non-PASS result",
               data["ok"] is False and any("not PASS" in e for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        evidence = fixture / ".vcps/evidence/EVD-00000000-0000-4000-8000-00000000000d.md"
        evidence.write_text(evidence.read_text().replace(
            'revision: "c49d0f6a1e88"', 'revision: "d49d0f6a1e88"', 1), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14u Gate 4/5 PASS evidence must match the evaluated revision",
               data["ok"] is False and any("differs from evidence" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace('baseline_ref: ".vcps/baseline.md"',
                                                            "baseline_ref: null", 1)
        text = text.replace("  stage: null\n", "  stage: 8\n", 1)
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14v pending baseline is rejected at Stage 8",
               data["ok"] is False and any("pending only before Stage 8" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace("  pending_artifact_refs: []",
                                                            "  pending_artifact_refs: [\".vcps/new.md\"]", 1)
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14w COMPLETE rejects any pending artifact reference",
               data["ok"] is False and any("pending_artifact_refs" in e for e in data["errors"]),
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        project.write_text(project.read_text(encoding="utf-8").replace(
            "default_observation_window_days: 14", "default_observation_window_days: .nan", 1
        ), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        record(cat, "14x strict YAML rejects non-finite numbers before schema validation",
               res.returncode == 1 and "non-finite number" in res.stdout,
               res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace(
            "mutation_paths: []", 'mutation_paths: ["src/unauthorized.py"]', 1
        )
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14y stage-event mutations must stay within referenced plan allowed_paths",
               data["ok"] is False and any("mutation path 'src/unauthorized.py' is outside" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace(
            'mutation_paths: [".vcps/baseline.md"]',
            'mutation_paths: [".vcps/unplanned.md"]', 1
        )
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14af stage-event mutation must be declared in the referenced plan",
               data["ok"] is False and any("mutation path '.vcps/unplanned.md' is not declared" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace(
            '".vcps/project.yaml"', '"../outside/project.yaml"', 1
        )
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14z plan create/modify paths must be safe and included in allowed_paths",
               data["ok"] is False and any("../outside/project.yaml" in e and "outside allowed_paths" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        project = fixture / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace("max_changed_files: 10", "max_changed_files: 0", 1)
        project.write_text(text, encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14aa dry-run path set cannot exceed max_changed_files",
               data["ok"] is False and any("plans 5 unique paths but max_changed_files is 0" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        finding = fixture / ".vcps/findings/FND-00000000-0000-4000-8000-000000000001.md"
        finding.write_text(finding.read_text(encoding="utf-8").replace(
            "status: RISK_ACCEPTED", "status: OPEN", 1
        ), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14ab finding current status must match the latest history event",
               data["ok"] is False and any("does not match latest history to_status" in e
                                           for e in data["errors"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {".vcps/project.yaml": "- malformed\n"})
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14ac validator rejects a non-mapping project document cleanly",
               res.returncode == 1 and "must be a YAML mapping" in data["errors"][0], res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = make_fixture(td, {".vcps/project.yaml": "schema_version: '0.2.0'\ninstallation: malformed\n"})
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14ad validator rejects malformed installation mapping cleanly",
               res.returncode == 1 and "installation must be a mapping" in data["errors"][0], res.stdout)

    with tempfile.TemporaryDirectory() as td:
        fixture = copy_worked_example(Path(td) / "project")
        finding = fixture / ".vcps/findings/FND-00000000-0000-4000-8000-00000000000c.md"
        finding.write_text(finding.read_text(encoding="utf-8").replace(
            "EVD-00000000-0000-4000-8000-00000000000d",
            "EVD-00000000-0000-4000-8000-000000000099", 1
        ), encoding="utf-8")
        res = run_tool(fixture, "validate", "--core", str(REPO_ROOT))
        data = json.loads(res.stdout)
        record(cat, "14ae nested remediation evidence reference must resolve",
               data["ok"] is False and any("remediation_evidence_refs" in e and
                                           "does not resolve to any record found" in e
                                           for e in data["errors"]), res.stdout)

    # 15. A malicious .vcps symlink must neither be read nor used as an
    # atomic-write destination outside the repository.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, outside_root = Path(td) / "target", Path(outside)
        root.mkdir()
        sentinel = "SYNTHETIC_EXTERNAL_SECRET_CANARY"
        (outside_root / "project.yaml").write_text(f"token: {sentinel}\n", encoding="utf-8")
        (root / ".vcps").symlink_to(outside_root, target_is_directory=True)
        detected = run_tool(root, "detect", "--core", str(REPO_ROOT))
        detect_data = json.loads(detected.stdout)
        validation = run_tool(root, "validate", "--core", str(REPO_ROOT))
        write_attempt = run_tool(root, "atomic-write", "--file", ".vcps/new.md", input_text="synthetic\n")
        record(cat, "15a external .vcps symlink is rejected without reading external content",
               detect_data["mode"] == "REPAIR"
               and "resolves outside" in " ".join(detect_data["reasons"])
               and sentinel not in detected.stdout
               and validation.returncode != 0 and sentinel not in validation.stdout,
               detected.stdout + validation.stdout)
        record(cat, "15b atomic-write refuses an external .vcps symlink destination",
               write_attempt.returncode != 0 and not (outside_root / "new.md").exists(),
               write_attempt.stdout + write_attempt.stderr)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        absolute_target = root.parent / (root.name + "-outside-write")
        res = run_tool(root, "atomic-write", "--file", str(absolute_target), input_text="must not write\n")
        record(cat, "15c atomic-write rejects an absolute destination",
               res.returncode != 0 and not absolute_target.exists(), res.stdout + res.stderr)

    # 15d. Swap an opened in-repository parent directory for an external
    # symlink. The dirfd-based writer must stay anchored to the opened folder.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, outside_root = Path(td) / "repo", Path(outside)
        records_dir = root / ".vcps" / "records"
        records_dir.mkdir(parents=True)
        held_dir = root / ".vcps" / "held-records"
        (outside_root / "new.md").write_text("outside canary\n", encoding="utf-8")

        spec = importlib.util.spec_from_file_location("vcps_tool_atomic_test", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_open = module.os.open
        original_dir_fd_support = module.os.supports_dir_fd
        swapped = False

        def racing_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            fd = original_open(path, flags, mode, dir_fd=dir_fd)
            if path == "records" and dir_fd is not None and not swapped:
                records_dir.rename(held_dir)
                records_dir.symlink_to(outside_root, target_is_directory=True)
                swapped = True
            return fd

        module.os.open = racing_open
        module.os.supports_dir_fd = set(original_dir_fd_support) | {racing_open}
        try:
            module.atomic_write(root, ".vcps/records/new.md", "inside original directory\n")
        finally:
            module.os.open = original_open
            module.os.supports_dir_fd = original_dir_fd_support

        safe_write = (held_dir / "new.md").read_text(encoding="utf-8") == "inside original directory\n"
        canary_safe = (outside_root / "new.md").read_text(encoding="utf-8") == "outside canary\n"
        record(cat, "15d parent-directory symlink swap cannot redirect atomic-write outside",
               swapped and safe_write and canary_safe,
               f"swapped={swapped}; safe_write={safe_write}; canary_safe={canary_safe}")

    # Live-runner failure-path regression: even when the CLI fails after
    # changing the disposable fixture, the script must print the tree diff.
    with tempfile.TemporaryDirectory(prefix="vcps-live-runner-test-") as td:
        base = Path(td)
        fixture = base / "fixture"
        fake_bin = base / "bin"
        fixture.mkdir()
        fake_bin.mkdir()
        fake_claude = fake_bin / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\nprintf changed > runner-canary.txt\nexit 7\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o700)
        env = __import__("os").environ.copy()
        env["PATH"] = str(fake_bin) + __import__("os").pathsep + env.get("PATH", "")
        live = subprocess.run(
            ["bash", str(RUN_LIVE), str(fixture)], cwd=ADAPTER_ROOT,
            env=env, capture_output=True, text=True, timeout=20,
        )
        record(cat, "16 live runner reports fixture diff and preserves nonzero CLI status",
               live.returncode == 7
               and "tree CHANGED:" in live.stdout
               and (fixture / "runner-canary.txt").is_file(),
               live.stdout + live.stderr)

    # Fixture snapshots include symlink identity but never read through links.
    with tempfile.TemporaryDirectory(prefix="vcps-fingerprint-link-test-") as td, \
         tempfile.TemporaryDirectory(prefix="vcps-fingerprint-outside-a-") as outside_a, \
         tempfile.TemporaryDirectory(prefix="vcps-fingerprint-outside-b-") as outside_b:
        fixture = Path(td)
        link = fixture / "external"
        Path(outside_a, "secret.txt").write_text("private one", encoding="utf-8")
        Path(outside_b, "secret.txt").write_text("private two", encoding="utf-8")
        link.symlink_to(outside_a, target_is_directory=True)
        first = subprocess.run([sys.executable, str(FINGERPRINT_FIXTURE), str(fixture)],
                               capture_output=True, text=True, timeout=15)
        Path(outside_a, "secret.txt").write_text("changed private data", encoding="utf-8")
        unchanged_link = subprocess.run([sys.executable, str(FINGERPRINT_FIXTURE), str(fixture)],
                                        capture_output=True, text=True, timeout=15)
        link.unlink()
        link.symlink_to(outside_b, target_is_directory=True)
        changed_link = subprocess.run([sys.executable, str(FINGERPRINT_FIXTURE), str(fixture)],
                                      capture_output=True, text=True, timeout=15)
        record(cat, "17 fixture fingerprint notices symlink retargeting without hashing external contents",
               first.returncode == 0 and unchanged_link.returncode == 0 and changed_link.returncode == 0
               and first.stdout == unchanged_link.stdout and first.stdout != changed_link.stdout
               and "private" not in first.stdout + unchanged_link.stdout + changed_link.stdout,
               first.stderr + unchanged_link.stderr + changed_link.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-fingerprint-race-test-") as td:
        base = Path(td)
        fixture = base / "fixture"
        records_dir = fixture / "records"
        outside = base / "outside"
        held = fixture / "held-records"
        records_dir.mkdir(parents=True)
        outside.mkdir()
        (records_dir / "safe.txt").write_text("inside", encoding="utf-8")
        (outside / "secret.txt").write_text("external secret", encoding="utf-8")
        spec = importlib.util.spec_from_file_location("vcps_fixture_fingerprint_race", FINGERPRINT_FIXTURE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_open = module.os.open
        original_dir_fd_support = module.os.supports_dir_fd
        swapped = False

        def racing_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            if path == "records" and dir_fd is not None and not swapped:
                records_dir.rename(held)
                records_dir.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        module.os.open = racing_open
        module.os.supports_dir_fd = set(original_dir_fd_support) | {racing_open}
        error = None
        try:
            module.fingerprint(fixture)
        except OSError as exc:
            error = str(exc)
        finally:
            module.os.open = original_open
            module.os.supports_dir_fd = original_dir_fd_support
        record(cat, "18 fixture fingerprint fails closed on parent-directory symlink swap",
               swapped and error is not None
               and "external secret" not in error
               and (outside / "secret.txt").read_text(encoding="utf-8") == "external secret",
               str(error))

    # A gitignored directory (e.g. a self-contained skill install's own
    # regenerated __pycache__/) must be invisible to vcps_tool.py
    # fingerprint --scope . and never cause drift between runs, even when
    # its contents genuinely change between invocations. This is the live-
    # found regression: `git status --porcelain` omits ignored paths by
    # default, so the existing "!!" exclusion check never had data to act
    # on until git_ignored_files() started asking for `--ignored=matching`.
    with tempfile.TemporaryDirectory(prefix="vcps-fingerprint-ignored-test-") as td:
        root = make_fixture(td, {
            "src/app.py": "value = 1\n",
            ".gitignore": "__pycache__/\n*.pyc\n",
        })
        pycache = root / "src" / "__pycache__"
        pycache.mkdir()
        (pycache / "app.cpython-314.pyc").write_bytes(b"bytecode-version-one")
        first = run_tool(root, "fingerprint", "--scope", ".")
        (pycache / "app.cpython-314.pyc").write_bytes(b"different-bytecode-entirely")
        second = run_tool(root, "fingerprint", "--scope", ".")
        first_json = json.loads(first.stdout) if first.returncode == 0 else {}
        second_json = json.loads(second.stdout) if second.returncode == 0 else {}
        first_paths = [e["path"] for e in first_json.get("entries", [])]
        record(cat, "19 gitignored directory (regenerated __pycache__) is excluded and never causes fingerprint drift",
               first.returncode == 0 and second.returncode == 0
               and not any("__pycache__" in p for p in first_paths)
               and first_json.get("fingerprint") == second_json.get("fingerprint")
               and first_json.get("fingerprint") is not None,
               first.stdout + first.stderr + second.stdout + second.stderr)

    # A standalone gitignored file (not inside an ignored directory) is
    # also excluded by the same mechanism.
    with tempfile.TemporaryDirectory(prefix="vcps-fingerprint-ignored-file-test-") as td:
        root = make_fixture(td, {
            "src/app.py": "value = 1\n",
            ".gitignore": "local.env\n",
        })
        envfile = root / "local.env"
        envfile.write_text("SECRET=one", encoding="utf-8")
        before = run_tool(root, "fingerprint", "--scope", ".")
        envfile.write_text("SECRET=two", encoding="utf-8")
        after = run_tool(root, "fingerprint", "--scope", ".")
        before_json = json.loads(before.stdout) if before.returncode == 0 else {}
        after_json = json.loads(after.stdout) if after.returncode == 0 else {}
        before_paths = [e["path"] for e in before_json.get("entries", [])]
        record(cat, "20 standalone gitignored file is excluded and never causes fingerprint drift",
               before.returncode == 0 and after.returncode == 0
               and "local.env" not in before_paths
               and before_json.get("fingerprint") == after_json.get("fingerprint")
               and before_json.get("fingerprint") is not None,
               before.stdout + before.stderr + after.stdout + after.stderr)

    # Explicitly naming a gitignored path in input_scope still surfaces it
    # (the existing "...not in input_scope" carve-out used by the symlink
    # exclusions applies identically here).
    with tempfile.TemporaryDirectory(prefix="vcps-fingerprint-ignored-explicit-test-") as td:
        root = make_fixture(td, {
            "src/app.py": "value = 1\n",
            ".gitignore": "build/\n",
        })
        build_dir = root / "build"
        build_dir.mkdir()
        (build_dir / "out.txt").write_text("artifact", encoding="utf-8")
        explicit = run_tool(root, "fingerprint", "--scope", "build")
        explicit_json = json.loads(explicit.stdout) if explicit.returncode == 0 else {}
        explicit_paths = [e["path"] for e in explicit_json.get("entries", [])]
        record(cat, "21 an explicitly-scoped gitignored directory is still fingerprinted, not silently dropped",
               explicit.returncode == 0 and "build/out.txt" in explicit_paths,
               explicit.stdout + explicit.stderr)

    # Phase K: migrate-project-schema (templates/contract.md "Unknown
    # fields and migrations", the 0.1.0 -> 0.2.0 project-schema migration).
    minimal_01 = textwrap.dedent("""\
        schema_version: "0.1.0"
        artifact_layout_version: "0.1.0"
        vcps_version: "0.1.0-draft"
        project:
          name: "migrate-fixture"
          description: "test"
        level:
          value: L1
          rationale: "trivial"
          evidence_refs: []
          lowering_approval_ref: null
        installation:
          mode: null
          route: ALREADY_COMPLETE
          stage: null
          status: COMPLETE
          history: []
          pending_artifact_refs: []
        repository:
          vcs: git
          remote: null
          default_branch: "main"
        stack:
          languages: ["python"]
          frameworks: []
          package_managers: []
        commands: []
        ci:
          present: false
          provider: null
          config_paths: []
          job_gate_map: []
        critical_domains: []
        applicable_invariants: []
        evidence_policy:
          minimum_tier_overrides: {}
        baseline_ref: null
        config_history: []
        lifecycle:
          default_observation_window_days: 14
          notes: "test"
        """)

    with tempfile.TemporaryDirectory(prefix="vcps-migrate-ok-test-") as td:
        root = make_fixture(td, {".vcps/project.yaml": minimal_01})
        before = run_tool(root, "validate")
        migrated = run_tool(root, "migrate-project-schema")
        migrated_json = json.loads(migrated.stdout) if migrated.returncode == 0 else {}
        after_text = (root / ".vcps" / "project.yaml").read_text(encoding="utf-8")
        after = run_tool(root, "validate", "--core", str(REPO_ROOT))
        after_json = json.loads(after.stdout) if after.returncode == 0 else {}
        record(cat, "22 migrate-project-schema turns a valid 0.1.0 record into a valid 0.2.0 record",
               migrated.returncode == 0
               and migrated_json.get("migrated") is True
               and migrated_json.get("from_schema") == "0.1.0"
               and migrated_json.get("to_schema") == "0.2.0"
               and migrated_json.get("backup") == ".vcps/project.yaml.0.1.0.bak"
               and (root / ".vcps/project.yaml.0.1.0.bak").read_bytes() == minimal_01.encode("utf-8")
               and "schema_version: '0.2.0'" in after_text
               and "plan_history: []" in after_text
               and "stage_events: []" in after_text
               and "status: PARTIAL" in after_text
               and "project schema migration" in after_text
               and after.returncode == 0 and after_json.get("ok") is True,
               migrated.stdout + migrated.stderr + "\n---after---\n" + after.stdout)

        again = run_tool(root, "migrate-project-schema")
        again_json = json.loads(again.stdout) if again.returncode == 0 else {}
        record(cat, "23 migrate-project-schema is a safe no-op once already at the current schema",
               again.returncode == 0 and again_json.get("migrated") is False,
               again.stdout + again.stderr)

        rolled_back = run_tool(root, "rollback-project-schema")
        rollback_json = json.loads(rolled_back.stdout) if rolled_back.returncode == 0 else {}
        record(cat, "22b rollback-project-schema restores byte-identical original config",
               rolled_back.returncode == 0 and rollback_json.get("rolled_back") is True
               and (root / ".vcps/project.yaml").read_bytes() == minimal_01.encode("utf-8"),
               rolled_back.stdout + rolled_back.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-migrate-unsupported-test-") as td:
        root = make_fixture(td, {
            ".vcps/project.yaml": "schema_version: \"9.9.9\"\ninstallation:\n  mode: null\n",
        })
        result = run_tool(root, "migrate-project-schema")
        record(cat, "24 migrate-project-schema refuses an unsupported schema_version rather than guessing",
               result.returncode != 0 and "no defined migration" in (result.stdout + result.stderr),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-journal-stage-projection-test-") as td:
        example = REPO_ROOT / "templates/examples/project/.vcps/project.yaml"
        root = make_fixture(td, {".vcps/project.yaml": example.read_text(encoding="utf-8")})
        project = root / ".vcps/project.yaml"
        text = project.read_text(encoding="utf-8").replace("  stage: null\n", "  stage: 1\n", 1)
        project.write_text(text, encoding="utf-8")
        result = run_tool(root, "validate", "--core", str(REPO_ROOT))
        record(cat, "25b validate rejects installation.stage that disagrees with completed journal",
               result.returncode == 1 and "earliest incomplete journal stage" in result.stdout,
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-migrate-corrupt-test-") as td:
        corrupt = minimal_01.replace(
            "  pending_artifact_refs: []\n",
            "  pending_artifact_refs: []\n  plan: null\n",
        )
        root = make_fixture(td, {".vcps/project.yaml": corrupt})
        result = run_tool(root, "migrate-project-schema")
        record(cat, "25 migrate-project-schema refuses a 0.1.0 record that already has a plan field",
               result.returncode != 0 and "already has" in (result.stdout + result.stderr),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-migrate-rollback-test-") as td:
        root = make_fixture(td, {".vcps/project.yaml": minimal_01})
        project = root / ".vcps/project.yaml"
        original_text = project.read_text(encoding="utf-8")
        spec = importlib.util.spec_from_file_location("vcps_tool_migration_failure_test", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_replace = os.replace

        def fail_atomic_replace(src, dst, *args, **kwargs):
            if str(dst) == "project.yaml":
                raise OSError("injected atomic replacement failure")
            return original_replace(src, dst, *args, **kwargs)

        try:
            module.os.replace = fail_atomic_replace
            try:
                module.migrate_project_schema(root)
                failed_as_injected = False
            except OSError as exc:
                failed_as_injected = "injected atomic replacement failure" in str(exc)
        finally:
            module.os.replace = original_replace
        record(cat, "26 failed schema migration replacement preserves original project.yaml",
               failed_as_injected and project.read_text(encoding="utf-8") == original_text
               and (root / ".vcps/project.yaml.0.1.0.bak").read_text(encoding="utf-8") == original_text
               and not list((root / ".vcps").glob(".vcps_tmp_*")),
               f"failed_as_injected={failed_as_injected}; original_preserved="
               f"{project.read_text(encoding='utf-8') == original_text}")

    with tempfile.TemporaryDirectory(prefix="vcps-migrate-edited-rollback-test-") as td:
        root = make_fixture(td, {".vcps/project.yaml": minimal_01})
        run_tool(root, "migrate-project-schema")
        project = root / ".vcps/project.yaml"
        project.write_text(project.read_text(encoding="utf-8") + "# user edit\n", encoding="utf-8")
        result = run_tool(root, "rollback-project-schema")
        record(cat, "27 rollback-project-schema refuses to overwrite edits made after migration",
               result.returncode != 0 and "changed after migration" in (result.stdout + result.stderr),
               result.stdout + result.stderr)


def main():
    print(f"Adapter root: {ADAPTER_ROOT}")
    print(f"VCPS repo root: {REPO_ROOT}")
    test_structural()
    test_simulated()

    structural = [r for r in results if r["category"] == "STRUCTURAL_TEST"]
    simulated = [r for r in results if r["category"] == "SIMULATED_EXECUTION"]
    s_pass = sum(1 for r in structural if r["ok"])
    sim_pass = sum(1 for r in simulated if r["ok"])

    print()
    print(f"STRUCTURAL_TEST: {s_pass}/{len(structural)} passed")
    print(f"SIMULATED_EXECUTION: {sim_pass}/{len(simulated)} passed")

    failed = [r for r in results if not r["ok"]]
    if failed:
        print("\nFAILURES:")
        for r in failed:
            print(f"  [{r['category']}] {r['name']}: {r['detail']}")
        sys.exit(1)
    print("\nAll tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()

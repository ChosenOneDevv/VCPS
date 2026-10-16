#!/usr/bin/env python3
"""Structural/simulated tests for adapters/install.py (Phase K,
evaluation/completion-roadmap.md). All STRUCTURAL_TEST/SIMULATED_EXECUTION
per the classification in evaluation/claude-code-adapter.md: no model
invocation, a disposable fixture per test, the real script run as a fresh
subprocess."""

import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "adapters" / "install.py"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def run_installer(*args, env=None):
    cmd = [sys.executable, str(INSTALLER)] + list(args)
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=child_env)


def make_target(td):
    target = Path(td) / "target"
    target.mkdir()
    return target


def test_structural():
    cat = "STRUCTURAL_TEST"
    text = INSTALLER.read_text(encoding="utf-8")
    record(cat, "S1 installer never executes anything in the target beyond file copy/symlink",
           "subprocess.run" not in text and "subprocess.Popen" not in text and "os.system" not in text)
    record(cat, "S2 installer refuses to overwrite an existing path (copy and symlink)",
           text.count("refusing to overwrite existing path") >= 2)
    record(cat, "S3 codex mode documents the hard-coded-path workaround, not a silent fix",
           "workaround, not a clean install" in text)


def test_simulated():
    cat = "SIMULATED_EXECUTION"

    with tempfile.TemporaryDirectory(prefix="vcps-install-copy-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "claude-code", "--target", str(target),
                                 "--mode", "copy", "--vendor-core")
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        verification = data.get("verification", {})
        record(cat, "1 claude-code copy install (all skills + lib) verifies byte-identical",
               result.returncode == 0 and verification.get("ok") is True and verification.get("files_checked", 0) > 0,
               result.stdout + result.stderr)
        record(cat, "2 --vendor-core copies standard/workflows/templates/VERSION into .vcps-core",
               (target / ".vcps-core" / "standard" / "VCPS.md").is_file()
               and (target / ".vcps-core" / "workflows").is_dir()
               and (target / ".vcps-core" / "templates").is_dir()
               and (target / ".vcps-core" / "VERSION").is_file(),
               str(list((target / ".vcps-core").iterdir()) if (target / ".vcps-core").exists() else "missing"))
        record(cat, "3 copy install also places UNTRUSTED-CONTENT.md at .claude/UNTRUSTED-CONTENT.md",
               (target / ".claude" / "UNTRUSTED-CONTENT.md").is_file())
        record(cat, "4 vcps-audit/vcps-review/vcps-bug's shared lib/ is installed as a sibling",
               (target / ".claude" / "skills" / "lib" / "vcps_evidence.py").is_file())

        # Functional smoke test: the installed, self-contained copy must
        # actually run, not merely match bytes.
        detect = subprocess.run(
            [sys.executable, str(target / ".claude" / "skills" / "vcps-setup" / "scripts" / "vcps_tool.py"),
             "detect", "--target", str(target), "--core", str(target / ".vcps-core")],
            capture_output=True, text=True, timeout=20,
        )
        detect_json = json.loads(detect.stdout) if detect.returncode == 0 else {}
        record(cat, "5 the installed copy actually runs detect against the vendored .vcps-core",
               detect.returncode == 0 and detect_json.get("mode") in ("NEW", "ADOPT"),
               detect.stdout + detect.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-symlink-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "claude-code", "--target", str(target), "--mode", "symlink")
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        record(cat, "6 claude-code symlink install verifies byte-identical through the link",
               result.returncode == 0 and data.get("verification", {}).get("ok") is True,
               result.stdout + result.stderr)
        record(cat, "7 symlink install does not duplicate UNTRUSTED-CONTENT.md (resolved from source tree)",
               not (target / ".claude" / "UNTRUSTED-CONTENT.md").exists())
        record(cat, "8 symlink install creates real symlinks, not copies",
               (target / ".claude" / "skills" / "vcps-setup").is_symlink())

    with tempfile.TemporaryDirectory(prefix="vcps-install-codex-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "codex", "--target", str(target))
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        record(cat, "9 codex install verifies byte-identical and vendors the required claude-code subtree",
               result.returncode == 0 and data.get("verification", {}).get("ok") is True
               and (target / "adapters" / "claude-code" / "lib" / "vcps_evidence.py").is_file()
               and (target / "adapters" / "claude-code" / "vcps-setup" / "scripts" / "vcps_tool.py").is_file(),
               result.stdout + result.stderr)
        record(cat, "9b codex install also places UNTRUSTED-CONTENT.md at .agents/UNTRUSTED-CONTENT.md",
               (target / ".agents" / "UNTRUSTED-CONTENT.md").is_file())

    with tempfile.TemporaryDirectory(prefix="vcps-install-conflict-") as td:
        target = make_target(td)
        (target / ".claude" / "skills" / "vcps-setup").mkdir(parents=True)
        (target / ".claude" / "skills" / "vcps-setup" / "placeholder.txt").write_text("pre-existing", encoding="utf-8")
        result = run_installer("--adapter", "claude-code", "--target", str(target), "--mode", "copy")
        record(cat, "10 install refuses to overwrite a pre-existing skill directory",
               result.returncode != 0
               and (target / ".claude" / "skills" / "vcps-setup" / "placeholder.txt").read_text(encoding="utf-8") == "pre-existing",
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-badname-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "claude-code", "--target", str(target),
                                 "--mode", "copy", "--skills", "not-a-real-skill")
        record(cat, "11 an unknown component name fails cleanly rather than installing a partial set",
               result.returncode != 0 and "unknown claude-code component" in (result.stdout + result.stderr),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-subset-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "claude-code", "--target", str(target),
                                 "--mode", "copy", "--skills", "vcps-tiny")
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        record(cat, "13 selecting a single skill auto-installs its sibling dependencies (lib, vcps-router)",
               result.returncode == 0
               and (target / ".claude" / "skills" / "vcps-tiny").is_dir()
               and (target / ".claude" / "skills" / "lib").is_dir()
               and (target / ".claude" / "skills" / "vcps-router").is_dir()
               and {".claude/skills/lib", ".claude/skills/vcps-router"}.issubset(
                   set(data.get("installed", []))),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-missing-target-") as td:
        result = run_installer("--adapter", "claude-code", "--target", str(Path(td) / "does-not-exist"))
        record(cat, "12 a nonexistent target directory fails cleanly",
               result.returncode != 0 and "target not found" in (result.stdout + result.stderr),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-plan-") as td:
        target = make_target(td)
        result = run_installer("--adapter", "claude-code", "--target", str(target), "--plan", "--vendor-core")
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        record(cat, "14 claude plan lists outputs without creating them",
               result.returncode == 0 and data.get("ready") is True
               and data.get("read_only") is True
               and any(item["path"] == ".vcps-core/standard" for item in data.get("actions", []))
               and not (target / ".claude").exists() and not (target / ".vcps-core").exists(),
               result.stdout + result.stderr)
        planned_paths = {item["path"] for item in data.get("actions", []) if item["kind"] != "manifest"}
        installed = run_installer("--adapter", "claude-code", "--target", str(target),
                                  "--mode", "copy", "--vendor-core")
        installed_data = json.loads(installed.stdout) if installed.stdout else {}
        record(cat, "14b install output matches the read-only plan exactly",
               installed.returncode == 0 and set(installed_data.get("installed", [])) == planned_paths,
               installed.stdout + installed.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-plan-conflict-") as td:
        target = make_target(td)
        (target / ".claude/skills/vcps-setup").mkdir(parents=True)
        result = run_installer("--adapter", "claude-code", "--target", str(target), "--plan")
        data = json.loads(result.stdout) if result.stdout else {}
        record(cat, "15 plan reports a conflict and preserves the existing directory",
               result.returncode != 0 and data.get("ready") is False
               and str(target / ".claude/skills/vcps-setup") in data.get("conflicts", [])
               and (target / ".claude/skills/vcps-setup").is_dir(),
               result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-verify-") as td:
        target = make_target(td)
        installed = run_installer("--adapter", "codex", "--target", str(target))
        verified = run_installer("--adapter", "codex", "--target", str(target), "--verify")
        data = json.loads(verified.stdout) if verified.stdout else {}
        record(cat, "16 verify checks Codex skills, helper subtree, and trust policy",
               installed.returncode == 0 and verified.returncode == 0
               and data.get("verification", {}).get("ok") is True
               and data["verification"].get("files_checked", 0) > 1,
               verified.stdout + verified.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-lifecycle-") as td:
        target = make_target(td)
        installed = run_installer("--adapter", "claude-code", "--target", str(target),
                                  "--skills", "vcps-tiny")
        manifest = target / ".vcps-install-claude-code.json"
        skill = target / ".claude/skills/vcps-tiny"
        upgraded = run_installer("--adapter", "claude-code", "--target", str(target), "--upgrade")
        upgraded_data = json.loads(upgraded.stdout) if upgraded.stdout else {}
        record(cat, "17 upgrade re-applies unchanged manifest-owned paths and verifies them",
               upgraded.returncode == 0 and upgraded_data.get("verification", {}).get("ok") is True,
               upgraded.stdout + upgraded.stderr)
        shutil.rmtree(skill)
        repaired = run_installer("--adapter", "claude-code", "--target", str(target), "--repair")
        repaired_data = json.loads(repaired.stdout) if repaired.stdout else {}
        record(cat, "18 repair restores a missing managed path and verifies it",
               installed.returncode == 0 and repaired.returncode == 0
               and (skill / "SKILL.md").is_file()
               and repaired_data.get("verification", {}).get("ok") is True,
               repaired.stdout + repaired.stderr)

        (skill / "SKILL.md").write_text("local edit\n", encoding="utf-8")
        upgrade = run_installer("--adapter", "claude-code", "--target", str(target), "--upgrade")
        record(cat, "19 upgrade refuses to overwrite a locally modified managed path",
               upgrade.returncode != 0 and "modified managed path requires manual review" in upgrade.stdout
               and (skill / "SKILL.md").read_text(encoding="utf-8") == "local edit\n",
               upgrade.stdout + upgrade.stderr)

        # Restore the managed byte before checking that uninstall only removes
        # paths whose recorded digest still matches.
        (skill / "SKILL.md").write_text(
            (REPO_ROOT / "adapters/claude-code/vcps-tiny/SKILL.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        uninstalled = run_installer("--adapter", "claude-code", "--target", str(target), "--uninstall")
        record(cat, "20 uninstall removes unchanged managed paths and its manifest",
               uninstalled.returncode == 0 and not skill.exists() and not manifest.exists(),
               uninstalled.stdout + uninstalled.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-global-") as td:
        home = Path(td) / "home"
        home.mkdir()
        installed = run_installer("--adapter", "codex", "--global", env={"HOME": str(home)})
        verified = run_installer("--adapter", "codex", "--global", "--verify", env={"HOME": str(home)})
        uninstalled = run_installer("--adapter", "codex", "--global", "--uninstall", env={"HOME": str(home)})
        verification = json.loads(verified.stdout).get("verification", {}) if verified.stdout else {}
        record(cat, "21 global Codex scope installs, verifies, and uninstalls under isolated HOME",
               installed.returncode == 0 and verified.returncode == 0
               and verification.get("ok") is True and uninstalled.returncode == 0
               and not (home / ".agents/vcps-install-codex.json").exists(),
               installed.stdout + verified.stdout + uninstalled.stdout + installed.stderr
               + verified.stderr + uninstalled.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-manifest-tamper-") as td:
        target = make_target(td)
        user_file = target / "README.md"
        user_file.write_text("user-owned\n", encoding="utf-8")
        installed = run_installer("--adapter", "codex", "--target", str(target))
        manifest_path = target / ".vcps-install-codex.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["installed"].append({"path": "README.md", "digest": "0" * 64})
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        uninstalled = run_installer("--adapter", "codex", "--target", str(target), "--uninstall")
        record(cat, "22 tampered manifest cannot claim or remove a user-owned path",
               installed.returncode == 0 and uninstalled.returncode != 0
               and "path not owned" in uninstalled.stdout
               and user_file.read_text(encoding="utf-8") == "user-owned\n",
               uninstalled.stdout + uninstalled.stderr)

    with tempfile.TemporaryDirectory(prefix="vcps-install-failure-injection-") as td:
        target = make_target(td)
        spec = importlib.util.spec_from_file_location("vcps_installer_under_test", INSTALLER)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        source = REPO_ROOT
        plan = installer._build_operation_plan(source, "claude-code", target, ["vcps-tiny"],
                                              "copy", False, False, "install")
        original_replace = os.replace
        replacements = 0

        def fail_on_second_replace(src, dst):
            nonlocal replacements
            replacements += 1
            if replacements == 2:
                raise OSError("injected commit failure")
            return original_replace(src, dst)

        try:
            os.replace = fail_on_second_replace
            try:
                installer._execute_operation(source, plan, target,
                                             installer._manifest_path("claude-code", target, False))
                raised = False
            except OSError as exc:
                raised = "injected commit failure" in str(exc)
        finally:
            os.replace = original_replace
        record(cat, "23 injected mid-commit error rolls back files and leaves no manifest",
               raised and not (target / ".claude/skills/vcps-tiny").exists()
               and not (target / ".vcps-install-claude-code.json").exists()
               and not list(target.glob(".vcps-install-*")),
               f"raised={raised}, replacements={replacements}, entries={list(target.iterdir())}")


def main():
    print(f"Repo root: {REPO_ROOT}")
    test_structural()
    test_simulated()
    structural = [r for r in results if r["category"] == "STRUCTURAL_TEST"]
    simulated = [r for r in results if r["category"] == "SIMULATED_EXECUTION"]
    print()
    print(f"STRUCTURAL_TEST: {sum(1 for r in structural if r['ok'])}/{len(structural)} passed")
    print(f"SIMULATED_EXECUTION: {sum(1 for r in simulated if r['ok'])}/{len(simulated)} passed")
    failed = [r for r in results if not r["ok"]]
    if failed:
        print("\nFAILURES:")
        for r in failed:
            print(f"  [{r['category']}] {r['name']}: {r['detail']}")
        sys.exit(1)
    print("\nAll tests passed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the repository's structural and simulated suites in one place.

This runner reports suite results; it does not convert them into VCPS gate
outcomes or claim live adapter execution.
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    ("Claude shared helper", ["adapters/claude-code/lib/tests/run_tests.py"]),
    ("Claude setup", ["adapters/claude-code/tests/run_tests.py"]),
    ("Claude router", ["adapters/claude-code/vcps-router/tests/run_tests.py"]),
    ("Claude workflow skills", [f"adapters/claude-code/vcps-{name}/tests/run_tests.py"
                                for name in ("audit", "review", "bug", "tiny", "feature", "hotfix", "release")]),
    ("Codex skills", ["adapters/codex/tests/run_tests.py"]),
    ("Installer", ["adapters/tests/run_tests.py"]),
    ("Evaluation", [["-m", "unittest", "discover", "-s", "evaluation/tests", "-p", "test_*.py"]]),
    ("JSON Schemas", ["evaluation/check_schemas.py"]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list suites without running them")
    parser.add_argument("--report", type=Path,
                        help="write a machine-readable run report to this path")
    args = parser.parse_args()
    if args.list:
        for name, commands in SUITES:
            rendered = []
            for command in commands:
                if isinstance(command, str):
                    command = [command]
                rendered.append("python3 " + " ".join(command))
            print(f"{name}: " + "; ".join(rendered))
        return 0

    started_at = datetime.datetime.now(datetime.timezone.utc)
    started = time.monotonic()
    suite_results = []
    failures = []
    for name, commands in SUITES:
        print(f"\n=== {name} ===", flush=True)
        suite_failures = []
        rendered_commands = []
        for command in commands:
            if isinstance(command, str):
                command = [command]
            rendered_commands.append([sys.executable, *command])
            argv = [sys.executable, *command]
            try:
                result = subprocess.run(argv, cwd=ROOT, timeout=600)
            except subprocess.TimeoutExpired:
                failures.append((name, command, "TIMEOUT"))
                suite_failures.append({
                    "command": argv, "exit_code": None,
                    "timed_out": True, "timeout_seconds": 600,
                })
                continue
            except OSError as exc:
                failures.append((name, command, "LAUNCH_ERROR"))
                suite_failures.append({
                    "command": argv, "exit_code": None,
                    "launch_error": str(exc),
                })
                continue
            if result.returncode:
                failures.append((name, command, result.returncode))
                suite_failures.append({"command": argv, "exit_code": result.returncode})
        suite_results.append({
            "name": name,
            "commands": rendered_commands,
            "status": "FAIL" if suite_failures else "PASS",
            "failures": suite_failures,
        })
    print("\n=== Summary ===")
    print(f"Suites: {len(SUITES) - len({name for name, _, _ in failures})}/{len(SUITES)} passed")
    status = "FAIL" if failures else "PASS"
    if failures:
        for name, command, code in failures:
            print(f"FAIL {name}: {command} (exit {code})")
    else:
        print("All structural/simulated suites passed. No live adapter claim is implied.")

    if args.report:
        completed_at = datetime.datetime.now(datetime.timezone.utc)
        revision = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "rev-parse", "HEAD"],
            cwd=ROOT, capture_output=True, text=True,
        )
        dirty = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT, capture_output=True, text=True,
        )
        report = {
            "format": "vcps-validation-run-v1",
            "status": status,
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "revision": revision.stdout.strip() if revision.returncode == 0 else None,
            "worktree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
            "python": sys.version,
            "platform": platform.platform(),
            "github_actions": {
                "run_id": os.environ.get("GITHUB_RUN_ID"),
                "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
                "workflow": os.environ.get("GITHUB_WORKFLOW"),
                "job": os.environ.get("GITHUB_JOB"),
            },
            "suites": suite_results,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Run report: {args.report}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Unit tests for revision-bound run report generation."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RUNNER_PATH = Path(__file__).resolve().parents[1] / "run_all.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("vcps_run_all_under_test", RUNNER_PATH)
run_all = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(run_all)


class RunReportTests(unittest.TestCase):
    def _run(self, suite_exit=0, suite_timeout=False):
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "run.json"
            completed = []

            def fake_run(argv, **kwargs):
                completed.append(argv)
                if argv[0] == "git" and "rev-parse" in argv:
                    return run_all.subprocess.CompletedProcess(argv, 0, "abc123\n", "")
                if argv[0] == "git" and "status" in argv:
                    return run_all.subprocess.CompletedProcess(argv, 0, "", "")
                if suite_timeout:
                    raise run_all.subprocess.TimeoutExpired(argv, 600)
                return run_all.subprocess.CompletedProcess(argv, suite_exit, "", "")

            with patch.object(run_all, "SUITES", [("sample", ["sample.py"])]), \
                    patch.object(run_all.sys, "argv", ["run_all.py", "--report", str(report_path)]), \
                    patch.object(run_all.subprocess, "run", side_effect=fake_run), \
                    contextlib.redirect_stdout(io.StringIO()):
                exit_code = run_all.main()
            return exit_code, json.loads(report_path.read_text(encoding="utf-8")), completed

    def test_report_binds_pass_to_revision_and_clean_worktree(self):
        exit_code, report, commands = self._run()
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["format"], "vcps-validation-run-v1")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["revision"], "abc123")
        self.assertFalse(report["worktree_dirty"])
        self.assertEqual(report["suites"][0]["status"], "PASS")
        self.assertTrue(any("rev-parse" in command for command in commands))

    def test_failed_suite_still_writes_failed_report(self):
        exit_code, report, _ = self._run(suite_exit=7)
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["suites"][0]["failures"][0]["exit_code"], 7)

    def test_timed_out_suite_still_writes_failed_report(self):
        exit_code, report, _ = self._run(suite_timeout=True)
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["suites"][0]["failures"][0]["timed_out"])


if __name__ == "__main__":
    unittest.main()

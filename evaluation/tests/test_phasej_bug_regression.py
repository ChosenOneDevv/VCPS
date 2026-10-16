#!/usr/bin/env python3
"""Repeat the synthetic inventory defect on parent and verify its fix."""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "evaluation/fixtures/synthetic-commerce"
class PhaseJBugRegression(unittest.TestCase):
    def test_parent_reproduces_oversell_and_fix_revision_passes_regression(self):
        fixed = subprocess.run(
            [sys.executable, "tools/verify_duplicate_sku_regression.py"],
            cwd=TARGET, capture_output=True, text=True,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
        self.assertIn("PARENT_REPRO=accepted=repro;remaining_stock=-1", fixed.stdout)
        self.assertIn("FIX_TESTS=8 passed", fixed.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)

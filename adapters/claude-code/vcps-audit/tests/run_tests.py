#!/usr/bin/env python3
"""Structural tests for the Claude Code /vcps-audit skill.

The mechanical facts /vcps-audit relies on (evidence-inventory,
gate-reference-check, orphan-check, antigaming-scan) are tested directly
in adapters/claude-code/lib/tests/run_tests.py (SIMULATED_EXECUTION) --
this suite only checks that this skill's own files are structurally
sound, correctly scoped (read-only, per VCPS-WF-AUDIT-001), and reference
the shared lib/setup tool at the right relative path.
"""

import re
import subprocess
import sys
from pathlib import Path

ADAPTER_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_CODE_ROOT = ADAPTER_ROOT.parent
SKILL_MD = ADAPTER_ROOT / "SKILL.md"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def main():
    cat = "STRUCTURAL_TEST"
    text = SKILL_MD.read_text(encoding="utf-8")

    record(cat, "S1 SKILL.md has frontmatter",
           text.startswith("---\n") and "\n---\n" in text[4:])
    fm_end = text.index("\n---\n", 4)
    frontmatter = text[4:fm_end]

    record(cat, "S2 manual invocation only",
           "disable-model-invocation: true" in frontmatter)

    record(cat, "S3 no Write/Edit anywhere in allowed-tools (read-only workflow, VCPS-WF-AUDIT-001)",
           not re.search(r"\bWrite\b", frontmatter) and not re.search(r"\bEdit\b", frontmatter))

    record(cat, "S4 references VCPS-WF-AUDIT-001 explicitly",
           "VCPS-WF-AUDIT-001" in text)

    # S5: every ${CLAUDE_SKILL_DIR}-relative script reference in allowed-tools
    # actually resolves to a real file on disk.
    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)*]+)", frontmatter)
    bad = []
    for ref in refs:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad.append((ref, str(resolved)))
    record(cat, "S5 every allowed-tools script path actually resolves", not bad, str(bad))

    # S6: the same check against the plain-text body instructions
    refs_body = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)`]+)", text)
    bad_body = []
    for ref in refs_body:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad_body.append((ref, str(resolved)))
    record(cat, "S6 every body-text script path reference also resolves", not bad_body, str(bad_body))

    record(cat, "S7 shared lib exists at the referenced location",
           (CLAUDE_CODE_ROOT / "lib" / "vcps_evidence.py").exists())

    record(cat, "S8 setup tool exists at the referenced location",
           (CLAUDE_CODE_ROOT / "vcps-setup" / "scripts" / "vcps_tool.py").exists())

    record(cat, "S9 never claims to re-run verification as an audit finding",
           "not re-running verification" in text or "never re-executing" in text or "never re-executing it" in text)

    structural = [r for r in results if r["category"] == cat]
    s_pass = sum(1 for r in structural if r["ok"])
    print()
    print(f"STRUCTURAL_TEST: {s_pass}/{len(structural)} passed")
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

#!/usr/bin/env python3
"""Structural tests for the Claude Code /vcps-review skill.

Like /vcps-audit, the mechanical facts this skill leans on are tested
directly in adapters/claude-code/lib/tests/run_tests.py -- this suite
only checks that this skill's own files are structurally sound and
reference the shared lib at the right relative path. Unlike /vcps-audit,
this workflow is mostly model judgment (gap analysis, remediation), so
there is deliberately little else to mechanically test here.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
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

    record(cat, "S3 no blanket Write/Edit pre-approval (remediation goes through ordinary permission prompts)",
           not re.search(r"\bWrite\b", frontmatter) and not re.search(r"\bEdit\b", frontmatter))

    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)*]+)", frontmatter)
    bad = []
    for ref in refs:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad.append((ref, str(resolved)))
    record(cat, "S4 every allowed-tools script path actually resolves", not bad, str(bad))

    refs_body = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)`]+)", text)
    bad_body = []
    for ref in refs_body:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad_body.append((ref, str(resolved)))
    record(cat, "S5 every body-text script path reference also resolves", not bad_body, str(bad_body))

    record(cat, "S6 shared lib exists at the referenced location",
           (CLAUDE_CODE_ROOT / "lib" / "vcps_evidence.py").exists())

    record(cat, "S7 references workflows/bug.md for remediation gate mapping",
           "workflows/bug.md" in text)

    record(cat, "S8 states the EVIDENCE_GAP-as-DEFECT misuse rule (AG-008/VCPS-CLS-003)",
           "AG-008" in text or "VCPS-CLS-003" in text)

    record(cat, "S9 states the 'never report clean with an open gap' exit rule",
           "PARTIALLY REVIEWED" in text)

    # S10: workflows/review.md and workflows/bug.md actually exist (these
    # are the Core documents this skill dispatches to without restating).
    record(cat, "S10 workflows/review.md exists",
           (REPO_ROOT / "workflows" / "review.md").exists())
    record(cat, "S11 workflows/bug.md exists",
           (REPO_ROOT / "workflows" / "bug.md").exists())

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

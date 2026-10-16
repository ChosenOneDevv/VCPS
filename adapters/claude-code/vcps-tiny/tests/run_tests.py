#!/usr/bin/env python3
"""Structural tests for the Claude Code /vcps-tiny skill.

The mechanical facts this skill leans on (escalation-check from
vcps-router, antigaming-scan from the shared lib) are tested directly in
their own components' test suites -- this checks only this skill's own
structural soundness and cross-component path references.
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

    record(cat, "S3 no blanket Write/Edit pre-approval",
           not re.search(r"\bWrite\b", frontmatter) and not re.search(r"\bEdit\b", frontmatter))

    bash_entries = re.findall(r"Bash\(([^)]*)\)", frontmatter)
    allowed_git = {
        "git status *", "git diff *", "git log *",
        "git -c core.fsmonitor=false status --short --untracked-files=all",
        "git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv",
        "git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s",
    }
    bad_bash = [
        b for b in bash_entries
        if b not in allowed_git and "vcps_router.py" not in b and "vcps_evidence.py" not in b
    ]
    record(cat, "S4 every pre-approved Bash entry is read-only git, the router, or the shared lib",
           not bad_bash, str(bad_bash))

    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)*]+)", frontmatter)
    bad = []
    for ref in refs:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad.append((ref, str(resolved)))
    record(cat, "S5 every allowed-tools script path actually resolves", not bad, str(bad))

    refs_body = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)`]+)", text)
    bad_body = []
    for ref in refs_body:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad_body.append((ref, str(resolved)))
    record(cat, "S6 every body-text script path reference also resolves", not bad_body, str(bad_body))

    record(cat, "S7 router script exists at the referenced location",
           (CLAUDE_CODE_ROOT / "vcps-router" / "scripts" / "vcps_router.py").exists())
    record(cat, "S8 shared lib exists at the referenced location",
           (CLAUDE_CODE_ROOT / "lib" / "vcps_evidence.py").exists())

    record(cat, "S9 states the mandatory (not optional) Step 1 eligibility check",
           "mandatory, not optional" in text.lower() or "mandatory -- not optional" in text.lower())

    record(cat, "S10 cites VCPS-WF-TINY-001 escalation rule",
           "VCPS-WF-TINY-001" in text)

    record(cat, "S11 workflows/tiny.md exists",
           (REPO_ROOT / "workflows" / "tiny.md").exists())

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

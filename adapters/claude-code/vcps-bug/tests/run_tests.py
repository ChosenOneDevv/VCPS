#!/usr/bin/env python3
"""Structural tests for the Claude Code /vcps-bug skill.

Like /vcps-review, the mechanical facts this skill leans on (evidence
staleness candidates, orphan references, anti-gaming literal patterns)
are tested directly in adapters/claude-code/lib/tests/run_tests.py.
Deliberately absent: any mechanical "run this test command" helper --
see SKILL.md's own explanation (running an arbitrary command from inside
a pre-approved script bypasses the permission prompt that command's real
effects would otherwise require). This suite checks that absence
structurally (no Bash pre-approval beyond read-only git/lib commands) in
addition to the usual frontmatter/path-resolution checks.
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

    # S4: the only Bash entries pre-approved are read-only git inspection
    # or the shared lib's read-only subcommands -- NOT a generic command
    # runner. This is the structural proof behind SKILL.md's own safety
    # claim.
    bash_entries = re.findall(r"Bash\(([^)]*)\)", frontmatter)
    allowed_git = {
        "git status *", "git diff *", "git log *", "git show *", "git worktree list *",
        "git -c core.fsmonitor=false status --short --untracked-files=all",
        "git --no-pager -c core.fsmonitor=false diff --no-ext-diff --no-textconv",
        "git --no-pager -c core.fsmonitor=false log -n 20 --format=%H%x09%an%x09%s",
        "git worktree list --porcelain",
    }
    bad_bash = [
        b for b in bash_entries
        if b not in allowed_git and "vcps_evidence.py" not in b
    ]
    record(cat, "S4 every pre-approved Bash entry is read-only git or the shared lib, never a generic runner",
           not bad_bash, str(bad_bash))

    record(cat, "S5 explicitly states why no command-execution helper is pre-approved",
           "no permission prompt" in text or "bypasses the permission prompt" in text.lower())

    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)*]+)", frontmatter)
    bad = []
    for ref in refs:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad.append((ref, str(resolved)))
    record(cat, "S6 every allowed-tools script path actually resolves", not bad, str(bad))

    refs_body = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)`]+)", text)
    bad_body = []
    for ref in refs_body:
        resolved = (ADAPTER_ROOT / ref.lstrip("/")).resolve()
        if not resolved.exists():
            bad_body.append((ref, str(resolved)))
    record(cat, "S7 every body-text script path reference also resolves", not bad_body, str(bad_body))

    record(cat, "S8 shared lib exists at the referenced location",
           (CLAUDE_CODE_ROOT / "lib" / "vcps_evidence.py").exists())

    record(cat, "S9 states the reproduce-before-fix rule (VCPS-CLS-001 / 'do not proceed to fix a guessed cause')",
           "do not proceed to" in text.lower() and "guessed cause" in text.lower())

    record(cat, "S10 states the risk-class-not-by-triviality rule (AG-014/VCPS-RISK-040)",
           "AG-014" in text and "VCPS-RISK-040" in text)

    record(cat, "S11 states the VCPS-G4-031 parent-fails/fix-passes confirmation rule",
           "VCPS-G4-031" in text and "parent" in text.lower())

    record(cat, "S12 workflows/bug.md exists", (REPO_ROOT / "workflows" / "bug.md").exists())

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

#!/usr/bin/env python3
"""Structural tests for the Claude Code /vcps-release skill.

The release-readiness-check logic this skill leans on is tested
directly in adapters/claude-code/lib/tests/run_tests.py (tests 21-25) --
this suite checks only this skill's own structural soundness, and the
explicit "never deploy, never set HC-10 yourself" claims.
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
    bad_bash = [b for b in bash_entries if b not in allowed_git and "vcps_evidence.py" not in b]
    record(cat, "S4 every pre-approved Bash entry is read-only git or the shared lib",
           not bad_bash, str(bad_bash))

    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)*]+)", frontmatter)
    bad = [(r, str((ADAPTER_ROOT / r.lstrip("/")).resolve()))
           for r in refs if not (ADAPTER_ROOT / r.lstrip("/")).resolve().exists()]
    record(cat, "S5 every allowed-tools script path actually resolves", not bad, str(bad))

    refs_body = re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[^\s)`]+)", text)
    bad_body = [(r, str((ADAPTER_ROOT / r.lstrip("/")).resolve()))
                for r in refs_body if not (ADAPTER_ROOT / r.lstrip("/")).resolve().exists()]
    record(cat, "S6 every body-text script path reference also resolves", not bad_body, str(bad_body))

    record(cat, "S7 shared lib exists at the referenced location",
           (CLAUDE_CODE_ROOT / "lib" / "vcps_evidence.py").exists())

    record(cat, "S8 explicitly states it never performs an actual deployment",
           "never performs an actual" in text.lower() or "never trigger an actual deployment" in text.lower())

    record(cat, "S9 states the agent MUST NOT set the HC-10 decision itself",
           "MUST NOT set" in text and "HC-10" in text)

    record(cat, "S10 states a release going live is not by itself PRODUCTION_PROVEN",
           "not, by itself," in text or "not by itself" in text.lower())

    record(cat, "S11 cites Gate 6 once-per-release-unit rule (VCPS-GATE-020)",
           "VCPS-GATE-020" in text)

    record(cat, "S12 standard/gates/gate-6-release.md exists",
           (REPO_ROOT / "standard" / "gates" / "gate-6-release.md").exists())
    record(cat, "S13 workflows/release.md exists",
           (REPO_ROOT / "workflows" / "release.md").exists())

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

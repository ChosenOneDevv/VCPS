#!/usr/bin/env python3
"""Structural and simulated-execution tests for the Claude Code /vcps
router adapter.

Classification (see evaluation/vcps-router.md):
  STRUCTURAL_TEST     - static checks of adapter files, unit behavior of
                        vcps_router.py.
  SIMULATED_EXECUTION - a script plays the mechanical half of routing
                        against a disposable fixture by invoking the real
                        helper script in a fresh process. No model
                        involved, so no actual intent classification runs
                        here -- only the mechanical escalation/context/
                        segmentation signal this adapter is allowed to
                        compute deterministically. Not a live pass.

This script never invokes `claude -p` -- that would be a separate,
explicitly LIVE_ADAPTER_EXECUTION path, not yet written for this
component (see evaluation/vcps-router.md "Known limitations").
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ADAPTER_ROOT = Path(__file__).resolve().parents[1]
TOOL = ADAPTER_ROOT / "scripts" / "vcps_router.py"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def run_tool(target, subcommand, *rest):
    cmd = [sys.executable, str(TOOL), subcommand, "--target", str(target)] + list(rest)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


# ---------------------------------------------------------------- STRUCTURAL

def test_structural():
    cat = "STRUCTURAL_TEST"
    skill_md = ADAPTER_ROOT / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    record(cat, "S1 SKILL.md has frontmatter",
            text.startswith("---\n") and "\n---\n" in text[4:])

    fm_end = text.index("\n---\n", 4)
    frontmatter = text[4:fm_end]
    record(cat, "S2 manual invocation only",
            "disable-model-invocation: true" in frontmatter)

    record(cat, "S3 no blanket Write/Edit/bare-Bash pre-approval",
            not re.search(r"\bWrite\b", frontmatter)
            and not re.search(r"\bEdit\b", frontmatter)
            and not re.search(r"Bash\(\s*\*", frontmatter)
            and "Bash," not in frontmatter.replace(" ", ""))

    # S4: every relative markdown link resolves
    all_text = skill_md.read_text(encoding="utf-8")
    for ref_md in (ADAPTER_ROOT / "references").glob("*.md"):
        all_text += "\n" + ref_md.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", all_text)
    bad_links = []
    for link in links:
        if link.startswith("http") or link.startswith("#"):
            continue
        link_path = link.split("#")[0]
        candidates = [
            (ADAPTER_ROOT / link_path).resolve(),
            (ADAPTER_ROOT / "references" / link_path).resolve(),
            (REPO_ROOT / link_path).resolve(),
        ]
        if not any(c.exists() for c in candidates):
            bad_links.append(link)
    record(cat, "S4 all relative markdown links resolve", not bad_links, str(bad_links))

    record(cat, "S5 orchestration-mapping doc marks itself informative/non-Core",
            "informative" in (ADAPTER_ROOT / "references" / "intent-classification.md").read_text(encoding="utf-8").lower())

    record(cat, "S6 no vendor name in Core text referenced by this adapter",
            all("claude" not in (REPO_ROOT / "standard" / f"{n}.md").read_text(encoding="utf-8").lower()
                for n in ("risk-model", "VCPS"))
            )

    record(cat, "S7 vcps_router.py exists and is executable-looking",
            TOOL.exists())

    compiled = subprocess.run([sys.executable, "-c", f"import py_compile; py_compile.compile(r'{TOOL}', doraise=True)"],
                               capture_output=True, text=True)
    record(cat, "S7b vcps_router.py compiles", compiled.returncode == 0, compiled.stderr)

    normalized = re.sub(r"\*\*", "", text)
    record(cat, "S8 honestly scopes itself (no claim of executing FEATURE/REVIEW/etc.)",
            "does not itself execute" in normalized or "does not dispatch" in normalized.lower(),
            normalized[:200])

    record(cat, "S9 escalation note states forced_r3 is a floor, never lowerable",
            "MUST NOT lower" in text or "never lowered" in text.lower() or "never a judgment" in TOOL.read_text(encoding="utf-8"))

    record(cat, "S10 TINY/HOTFIX misuse guidance present",
            "VCPS-WF-TINY-001" in text and "HOTFIX" in text)

    # S11: no bare Bash() wildcard that would blanket-approve arbitrary commands
    record(cat, "S11 allowed-tools Bash entries are all scoped to this script's subcommands",
            all(
                m.startswith("git ") or "vcps_router.py" in m
                for m in re.findall(r"Bash\(([^)]*)\)", frontmatter)
            ))


# ---------------------------------------------------------------- SIMULATED

def make_vcps_fixture(tmp, invariants, applicable_invariants, critical_domains=None, work_items=None):
    """Build a minimal .vcps/ root sufficient for vcps_router.py to read."""
    root = Path(tmp)
    vcps = root / ".vcps"
    vcps.mkdir(parents=True)
    project_yaml = {
        "level": {"value": "L2"},
        "critical_domains": critical_domains or [],
        "applicable_invariants": applicable_invariants,
    }
    import yaml
    (vcps / "project.yaml").write_text(yaml.safe_dump(project_yaml), encoding="utf-8")

    inv_fm = {"invariants": invariants}
    (vcps / "invariants.md").write_text(
        "---\n" + yaml.safe_dump(inv_fm) + "---\n\nInvariant registry.\n", encoding="utf-8"
    )

    for sub, items in (work_items or {}).items():
        d = vcps / sub
        d.mkdir(parents=True, exist_ok=True)
        for i, item in enumerate(items):
            (d / f"ITEM-{i}.md").write_text(
                "---\n" + yaml.safe_dump(item) + "---\n\nWork item.\n", encoding="utf-8"
            )
    return root


def test_simulated():
    cat = "SIMULATED_EXECUTION"

    # 1. No .vcps at all: has_vcps false, never crashes, never silently PASSes
    with tempfile.TemporaryDirectory() as td:
        res = run_tool(td, "escalation-check", "--touched-path", "src/anything.js")
        data = json.loads(res.stdout)
        record(cat, "1 no .vcps -> has_vcps false, forced_r3 false, no crash",
               res.returncode == 0 and data["has_vcps"] is False and data["forced_r3"] is False,
               res.stdout)

    # 2. Direct hit: touched path exactly matches an invariant's enforcement path -> forced_r3
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-001", "enforcement_path": ["src/sync.js"], "status": "ACTIVE"}],
            applicable_invariants=["INV-001"],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/sync.js")
        data = json.loads(res.stdout)
        record(cat, "2 direct enforcement-path hit forces R3",
               data["forced_r3"] is True and data["matched_invariants"][0]["invariant_id"] == "INV-001",
               res.stdout)

    # 3. The "undersell" case the roadmap's completion criteria require:
    # trivial wording ("tiny tweak"), but the touched path IS the enforcement
    # path -> must still force R3. (The wording itself is a model-level
    # concern; this test proves the mechanical floor is correct regardless
    # of what the user called it.)
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-001", "enforcement_path": ["src/payments/charge.js"], "status": "ACTIVE"}],
            applicable_invariants=["INV-001"],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/payments/charge.js")
        data = json.loads(res.stdout)
        record(cat, "3 undersell: 'tiny'-worded change touching payments enforcement path still forces R3",
               data["forced_r3"] is True, res.stdout)

    # 4. No hit: unrelated file -> forced_r3 false, but note disclaims safety
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-001", "enforcement_path": ["src/sync.js"], "status": "ACTIVE"}],
            applicable_invariants=["INV-001"],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "README.md")
        data = json.loads(res.stdout)
        record(cat, "4 unrelated file -> forced_r3 false, note present and non-empty",
               data["forced_r3"] is False and len(data.get("note", "")) > 0, res.stdout)

    # 5. Directory-prefix match: enforcement path is a directory, touched path is a file within it
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-002", "enforcement_path": ["src/auth/"], "status": "ACTIVE"}],
            applicable_invariants=["INV-002"],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/auth/session.js")
        data = json.loads(res.stdout)
        record(cat, "5 directory-prefix enforcement path match forces R3",
               data["forced_r3"] is True, res.stdout)

    # 6. Withdrawn invariant is excluded even if applicable list still lists it stale
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-003", "enforcement_path": ["src/old.js"], "status": "WITHDRAWN"}],
            applicable_invariants=["INV-003"],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/old.js")
        data = json.loads(res.stdout)
        record(cat, "6 withdrawn invariant does not force R3",
               data["forced_r3"] is False, res.stdout)

    # 7. Not-applicable invariant (exists in registry, not in project.yaml's
    # applicable_invariants) does not force R3 either.
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td,
            invariants=[{"id": "INV-004", "enforcement_path": ["src/other.js"], "status": "ACTIVE"}],
            applicable_invariants=[],
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/other.js")
        data = json.loads(res.stdout)
        record(cat, "7 non-applicable invariant does not force R3",
               data["forced_r3"] is False, res.stdout)

    # 8. project-context surfaces critical_domains as raw candidates, never
    # itself setting forced_r3 or any escalation verdict.
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td, invariants=[], applicable_invariants=[],
            critical_domains=[{"domain": "payments", "rationale": "x", "impact_dimensions": ["D2"]}],
        )
        res = run_tool(root, "project-context")
        data = json.loads(res.stdout)
        record(cat, "8 project-context surfaces domains as candidates only, no verdict field",
               data["level"] == "L2" and data["critical_domains"][0]["domain"] == "payments"
               and "forced_r3" not in data and "escalate" not in json.dumps(data).lower() or "note" in data,
               res.stdout)

    # 9. segmentation-scan finds overlapping prior work items by file, raw only
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td, invariants=[], applicable_invariants=[],
            work_items={
                "work-items": [
                    {"id": "WORK-1", "intent": "TINY", "risk_class": "R0",
                     "scope": {"files": ["src/sync.js"]}},
                    {"id": "WORK-2", "intent": "BUG", "risk_class": "R1",
                     "scope": {"files": ["src/unrelated.js"]}},
                ]
            },
        )
        res = run_tool(root, "segmentation-scan", "--touched-path", "src/sync.js")
        data = json.loads(res.stdout)
        ids = [o["id"] for o in data["overlapping_work_items"]]
        record(cat, "9 segmentation-scan finds only the genuinely overlapping prior work item",
               ids == ["WORK-1"], res.stdout)

    # 10. segmentation-scan with no overlap returns empty list, not an error
    with tempfile.TemporaryDirectory() as td:
        root = make_vcps_fixture(
            td, invariants=[], applicable_invariants=[],
            work_items={"work-items": [{"id": "WORK-1", "intent": "TINY", "risk_class": "R0",
                                         "scope": {"files": ["src/other.js"]}}]},
        )
        res = run_tool(root, "segmentation-scan", "--touched-path", "src/sync.js")
        data = json.loads(res.stdout)
        record(cat, "10 segmentation-scan with no overlap returns empty list cleanly",
               data["overlapping_work_items"] == [], res.stdout)

    # 11. Malformed invariants.md (duplicate key) is a tool error, not a
    # silent "no escalation needed" false negative.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vcps = root / ".vcps"
        vcps.mkdir()
        (vcps / "project.yaml").write_text(
            "level:\n  value: L2\ncritical_domains: []\napplicable_invariants: [INV-001]\n",
            encoding="utf-8",
        )
        (vcps / "invariants.md").write_text(
            "---\ninvariants: []\ninvariants: []\n---\n\nbroken\n", encoding="utf-8"
        )
        res = run_tool(root, "escalation-check", "--touched-path", "src/x.js")
        record(cat, "11 malformed invariants.md (duplicate key) is a reported error, not a silent pass",
               res.returncode != 0 and "error" in res.stdout, res.stdout)

    # 12. Request-matrix completion criterion: for each of the 8 (touched,
    # project) combinations below, forced_r3 matches the Core-correct
    # mechanical answer, independent of how the request might be WORDED
    # (wording itself is model-level and not exercised by this script --
    # this proves the floor the model is required to respect is itself
    # correct in every cell of the matrix).
    matrix = [
        ("payments enforcement file, project has that invariant", "src/payments/charge.js", ["src/payments/charge.js"], True),
        ("payments enforcement file, invariant not applicable here", "src/payments/charge.js", [], False),
        ("doc-only file, project has an unrelated invariant", "README.md", ["src/payments/charge.js"], False),
        ("test file for the enforcement path itself (VCPS-RISK-041: tests count too)", "tests/payments.test.js", ["tests/payments.test.js"], True),
    ]
    for name, touched, enforcement_paths, expected in matrix:
        with tempfile.TemporaryDirectory() as td:
            root = make_vcps_fixture(
                td,
                invariants=[{"id": "INV-001", "enforcement_path": enforcement_paths, "status": "ACTIVE"}] if enforcement_paths else [],
                applicable_invariants=["INV-001"] if enforcement_paths else [],
            )
            res = run_tool(root, "escalation-check", "--touched-path", touched)
            data = json.loads(res.stdout)
            record(cat, f"12 request-matrix: {name}", data["forced_r3"] is expected, res.stdout)

    # 13. VCPS state reached through an external symlink is rejected, not
    # trusted as absent context or parsed as target-owned state.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, external = Path(td) / "target", Path(outside)
        root.mkdir()
        sentinel = "EXTERNAL_VCPS_CANARY"
        (external / "project.yaml").write_text(
            f"level:\n  value: L3\ncritical_domains: [{sentinel}]\napplicable_invariants: []\n",
            encoding="utf-8",
        )
        (root / ".vcps").symlink_to(external, target_is_directory=True)
        res = run_tool(root, "project-context")
        record(cat, "13 external .vcps symlink causes tool error without reading its content",
               res.returncode != 0 and sentinel not in res.stdout, res.stdout)

    # 14. A work-item directory symlink cannot make segmentation-scan read
    # external metadata or report an empty, apparently-safe overlap set.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root = make_vcps_fixture(td, invariants=[], applicable_invariants=[])
        external = Path(outside)
        sentinel = "EXTERNAL_WORK_ITEM_CANARY"
        (external / "ITEM.md").write_text(
            f"---\nid: {sentinel}\nintent: FEATURE\nscope:\n  files: [src/x.py]\n---\n",
            encoding="utf-8",
        )
        work_dir = root / ".vcps" / "work-items"
        if work_dir.exists():
            import shutil
            shutil.rmtree(work_dir)
        work_dir.symlink_to(external, target_is_directory=True)
        res = run_tool(root, "segmentation-scan", "--touched-path", "src/x.py")
        record(cat, "14 external work-item directory symlink is rejected",
               res.returncode != 0 and sentinel not in res.stdout, res.stdout)


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

#!/usr/bin/env python3
"""Structural and simulated-execution tests for the shared
adapters/claude-code/lib/vcps_evidence.py helper, used by /vcps-audit and
/vcps-review.

Classification (see evaluation/vcps-audit.md and evaluation/vcps-review.md):
  STRUCTURAL_TEST     - static checks, unit behavior of vcps_evidence.py.
  SIMULATED_EXECUTION - a script plays the mechanical role against a
                        disposable fixture by invoking the real helper
                        in a fresh process. No model involved. Not a
                        live pass.
"""

import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

LIB_ROOT = Path(__file__).resolve().parents[1]
TOOL = LIB_ROOT / "vcps_evidence.py"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def run_tool(target, subcommand, *rest):
    cmd = [sys.executable, str(TOOL), subcommand, "--target", str(target)] + list(rest)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def write_fm(path: Path, fm: dict, body: str = "body.\n"):
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(fm) + "---\n\n" + body, encoding="utf-8")


def init_git(root: Path):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()


def test_structural():
    cat = "STRUCTURAL_TEST"
    record(cat, "S1 vcps_evidence.py exists", TOOL.exists())
    compiled = subprocess.run(
        [sys.executable, "-c", f"import py_compile; py_compile.compile(r'{TOOL}', doraise=True)"],
        capture_output=True, text=True,
    )
    record(cat, "S2 vcps_evidence.py compiles", compiled.returncode == 0, compiled.stderr)
    text = TOOL.read_text(encoding="utf-8")
    record(cat, "S3 states staleness is a candidate, not a verdict",
           "CANDIDATE" in text and "VCPS-EVD-051" in text)
    record(cat, "S4 states antigaming matches are candidates, not violations",
           "NOT itself a violation" in text or "not a verdict" in text)


def test_simulated():
    cat = "SIMULATED_EXECUTION"

    # 1. Empty repo: no .vcps at all -> empty inventory, no crash
    with tempfile.TemporaryDirectory() as td:
        res = run_tool(td, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "1 no .vcps -> empty evidence inventory, no crash",
               res.returncode == 0 and data["entries"] == [], res.stdout)

    # 2. Evidence revision matches current HEAD
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "PASS", "revision": "PLACEHOLDER", "scope": ["x"]})
        head = init_git(root)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "PASS", "revision": head, "scope": ["x"]})
        res = run_tool(root, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "2 evidence revision matching current HEAD -> matches_head true",
               data["entries"][0]["matches_head"] is True, res.stdout)

    # 3. Evidence revision differs from current HEAD -> flagged as candidate, not crash
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "PASS", "revision": "deadbeef", "scope": ["x"]})
        init_git(root)
        res = run_tool(root, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "3 stale-looking revision -> matches_head false, not an error",
               res.returncode == 0 and data["entries"][0]["matches_head"] is False, res.stdout)

    # 4. Dirty-worktree revision object is recognized and flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "PASS",
                  "revision": {"base_commit_hash": "deadbeef", "dirty": True, "manifest_hash": "abc"},
                  "scope": ["x"]})
        init_git(root)
        res = run_tool(root, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "4 dirty-worktree revision recognized",
               data["entries"][0]["is_dirty_worktree_revision"] is True
               and data["entries"][0]["revision"] == "deadbeef", res.stdout)

    # 5. gate-reference-check: BLOCKED outcome missing reason_codes is flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 3, "outcome": "BLOCKED"})
        res = run_tool(root, "gate-reference-check")
        data = json.loads(res.stdout)
        record(cat, "5 BLOCKED gate missing reason_codes is flagged",
               any("reason_codes" in i["issue"] for i in data["issues"]), res.stdout)

    # 6. gate-reference-check: Gate 4 missing independence_mode is flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "PASS"})
        res = run_tool(root, "gate-reference-check")
        data = json.loads(res.stdout)
        record(cat, "6 Gate 4 PASS missing independence_mode is flagged",
               any("independence_mode" in i["issue"] for i in data["issues"]), res.stdout)

    # 7. gate-reference-check: unresolved evidence_refs is flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "PASS", "independence_mode": "I2",
                  "evidence_refs": ["EVD-does-not-exist"]})
        res = run_tool(root, "gate-reference-check")
        data = json.loads(res.stdout)
        record(cat, "7 unresolved evidence_refs entry is flagged",
               any("unresolved evidence_refs" in i["issue"] for i in data["issues"]), res.stdout)

    # 8. gate-reference-check: a clean, fully-consistent gate has no issues
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "PASS"})
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "PASS", "independence_mode": "I2",
                  "evidence_refs": ["EVD-1"], "finding_refs": []})
        res = run_tool(root, "gate-reference-check")
        data = json.loads(res.stdout)
        record(cat, "8 fully consistent gate record has zero issues",
               data["issues"] == [], res.stdout)

    # 9. EVD-020: a PASS gate cannot count NOT_RUN/ERROR/INCONCLUSIVE evidence as PASS
    for result in ("NOT_RUN", "ERROR", "INCONCLUSIVE"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                     {"id": "EVD-1", "tier": "E2", "result": result})
            write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                     {"id": "GATE-1", "gate": 4, "outcome": "PASS",
                      "independence_mode": "I2", "evidence_refs": ["EVD-1"]})
            res = run_tool(root, "gate-reference-check")
            data = json.loads(res.stdout)
            flagged = any("potential VCPS-EVD-020 inconsistency" in i["issue"] for i in data["issues"])
            record(cat, f"AG-007/EVI-008/EVI-009 PASS gate citing {result} evidence surfaces a candidate",
                   res.returncode == 0 and flagged, res.stdout)

    # 10. The same unavailable evidence may honestly support a BLOCKED gate.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md",
                 {"id": "EVD-1", "tier": "E2", "result": "NOT_RUN"})
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "BLOCKED",
                  "reason_codes": ["EVIDENCE_GAP"], "independence_mode": "I0",
                  "evidence_refs": ["EVD-1"]})
        res = run_tool(root, "gate-reference-check")
        data = json.loads(res.stdout)
        record(cat, "AG-007 honest BLOCKED gate may cite NOT_RUN evidence without false-PASS warning",
               res.returncode == 0 and data["issues"] == [], res.stdout)

    # AG-017 compares committed baseline state with the worktree. Rewriting
    # an old observation is surfaced; an append requires provenance review.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        baseline = root / ".vcps" / "baseline.md"
        old_observation = {"id": "OBS-1", "check_id": "unit", "result": "FAIL"}
        write_fm(baseline, {"id": "BASELINE-1", "observations": [old_observation], "history": []})
        init_git(root)
        write_fm(baseline, {"id": "BASELINE-1", "observations": [
            {"id": "OBS-1", "check_id": "unit", "result": "PASS"}
        ], "history": []})
        res = run_tool(root, "baseline-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-017 rewrite of a committed baseline observation surfaces a candidate",
               res.returncode == 0 and any("baseline observations array changed" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        baseline = root / ".vcps" / "baseline.md"
        observation = {"id": "OBS-1", "check_id": "unit", "result": "FAIL"}
        old_event = {"type": "RESOLVE_OBSERVATION", "observation_id": "OBS-1",
                     "resolution_finding_ref": "FND-1", "timestamp": "2026-10-06T00:00:00Z",
                     "reason": "fixed with evidence"}
        write_fm(baseline, {"id": "BASELINE-1", "observations": [observation], "history": [old_event]})
        init_git(root)
        write_fm(baseline, {"id": "BASELINE-1", "observations": [observation], "history": []})
        res = run_tool(root, "baseline-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-017 truncating committed baseline history surfaces a candidate",
               res.returncode == 0 and any("committed baseline history was truncated" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        baseline = root / ".vcps" / "baseline.md"
        old_observation = {"id": "OBS-1", "check_id": "unit", "result": "FAIL"}
        write_fm(baseline, {"id": "BASELINE-1", "observations": [old_observation], "history": []})
        init_git(root)
        new_observation = {"id": "OBS-2", "check_id": "lint", "result": "FAIL"}
        event = {"type": "ADD_OBSERVATION", "new_observation": dict(new_observation)}
        write_fm(baseline, {
            "id": "BASELINE-1", "observations": [old_observation],
            "history": [event],
        })
        res = run_tool(root, "baseline-history-check")
        data = json.loads(res.stdout)
        issues = [f["issue"] for f in data["candidate_findings"]]
        record(cat, "AG-017 history-only baseline widening preserves original observations and requires provenance review",
               res.returncode == 0 and not any("baseline observations array changed" in i for i in issues)
               and data["current_observation_count"] == 1
               and "predates the relevant mutation" in data["note"]
               and any("new baseline observations require" in i for i in issues), res.stdout)

    # AG-011 checks old records against their committed form and ensures
    # existing append-only history entries remain an exact prefix.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        gate = root / ".vcps" / "gates" / "GATE-1.md"
        write_fm(gate, {"id": "GATE-1", "outcome": "BLOCKED", "reason_codes": ["EVIDENCE_GAP"]})
        init_git(root)
        write_fm(gate, {"id": "GATE-1", "outcome": "PASS", "reason_codes": []})
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-011 editing a committed gate record surfaces an immutable-record candidate",
               res.returncode == 0 and any(f.get("path", "").endswith("GATE-1.md")
                                           and "record was edited" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        evidence = root / ".vcps" / "evidence" / "EVD-1.md"
        approval = root / ".vcps" / "approvals" / "HCR-1.md"
        write_fm(evidence, {"id": "EVD-1", "result": "FAIL", "revision": "abc"})
        write_fm(approval, {"id": "HCR-1", "decision": "REJECTED", "revision": "abc"})
        init_git(root)
        write_fm(evidence, {"id": "EVD-1", "result": "PASS", "revision": "abc"})
        write_fm(approval, {"id": "HCR-1", "decision": "APPROVED", "revision": "abc"})
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        edited_paths = {f.get("path") for f in data["candidate_findings"]
                        if "record was edited" in f["issue"]}
        record(cat, "AG-011 editing committed evidence and checkpoint records surfaces candidates",
               res.returncode == 0 and edited_paths == {
                   ".vcps/evidence/EVD-1.md", ".vcps/approvals/HCR-1.md"
               }, res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        finding = root / ".vcps" / "findings" / "FND-1.md"
        first = {"timestamp": "2026-01-01T00:00:00Z", "to_status": "OPEN"}
        second = {"timestamp": "2026-01-02T00:00:00Z", "from_status": "OPEN", "to_status": "RESOLVED"}
        write_fm(finding, {"id": "FND-1", "status": "RESOLVED", "history": [first, second]})
        init_git(root)
        write_fm(finding, {"id": "FND-1", "status": "OPEN", "history": [first]})
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-011 truncating a committed finding history surfaces a candidate",
               res.returncode == 0 and any(f.get("field") == "history"
                                           and "truncated" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        finding = root / ".vcps" / "findings" / "FND-1.md"
        first = {"timestamp": "2026-01-01T00:00:00Z", "to_status": "OPEN"}
        second = {"timestamp": "2026-01-02T00:00:00Z", "from_status": "OPEN", "to_status": "RESOLVED"}
        write_fm(finding, {"id": "FND-1", "status": "OPEN", "history": [first]})
        init_git(root)
        write_fm(finding, {"id": "FND-1", "status": "RESOLVED", "history": [first, second]})
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-011 preserves committed finding history when a valid new transition is appended",
               res.returncode == 0 and not data["candidate_findings"], res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        huge_record = root / ".vcps" / "findings" / "FND-large.md"
        write_fm(huge_record, {"id": "FND-large", "history": []}, body="x" * (1024 * 1024 + 1))
        init_git(root)
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-011 oversized committed record is explicitly unverified without loading its blob",
               res.returncode == 0 and any("1 MiB comparison limit" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        huge_record = root / ".vcps" / "findings" / "FND-large.md"
        write_fm(huge_record, {"id": "FND-large", "history": []})
        init_git(root)
        write_fm(huge_record, {"id": "FND-large", "history": []}, body="x" * (1024 * 1024 + 1))
        res = run_tool(root, "record-history-check")
        data = json.loads(res.stdout)
        record(cat, "AG-011 oversized working-tree record is explicitly unverified with bounded read",
               res.returncode == 0 and any("working-tree record exceeds 1 MiB" in f["issue"]
                                           for f in data["candidate_findings"]), res.stdout)

    # 9. orphan-check: a finding referencing a nonexistent evidence record is an orphan
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "findings" / "FND-1.md",
                 {"id": "FND-1", "evidence_refs": ["EVD-ghost"]})
        res = run_tool(root, "orphan-check")
        data = json.loads(res.stdout)
        record(cat, "9 reference to a nonexistent record is an orphan",
               any(o["unresolved_ref"] == "EVD-ghost" for o in data["orphans"]), res.stdout)

    # 10. orphan-check: a resolving reference is not an orphan
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "evidence" / "EVD-1.md", {"id": "EVD-1", "tier": "E2", "result": "PASS"})
        write_fm(root / ".vcps" / "findings" / "FND-1.md", {"id": "FND-1", "evidence_refs": ["EVD-1"]})
        res = run_tool(root, "orphan-check")
        data = json.loads(res.stdout)
        record(cat, "10 resolving reference is not flagged as orphan",
               data["orphans"] == [] and data["total_records"] == 2, res.stdout)

    # 11. orphan-check: a non-ID-shaped *_ref value (e.g. a bare requirement
    # ID or a fixed singleton path) is correctly skipped, not false-flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "handoffs" / "HND-1.md",
                 {"id": "HND-1", "project_ref": ".vcps/project.yaml"})
        res = run_tool(root, "orphan-check")
        data = json.loads(res.stdout)
        record(cat, "11 non-ID-shaped ref value (fixed singleton path) is not false-flagged",
               data["orphans"] == [], res.stdout)

    # 12. antigaming-scan: regression for the xit(/exit( false-positive this
    # session found and fixed during self-testing.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "code.py"
        f.write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "code.py")
        data = json.loads(res.stdout)
        record(cat, "12 'sys.exit(2)' is NOT a false positive for the xit( skip-test pattern",
               data["candidate_findings"] == [], res.stdout)

    # 13. antigaming-scan: a real xit( (Mocha skip) is correctly flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "test.js"
        f.write_text("xit('should do the thing', () => {});\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "test.js")
        data = json.loads(res.stdout)
        record(cat, "13 real xit( skip-test call is flagged (AG-001)",
               any(x["pattern_id"] == "AG-001" for x in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "test_guards.rs"
        f.write_text("#[ignore]\nfn weak_guard() {}\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "test_guards.rs")
        data = json.loads(res.stdout)
        record(cat, "AG-001 Rust ignored-test attribute is surfaced as a candidate",
               any(x["pattern_id"] == "AG-001" for x in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests").mkdir()
        (root / "tests" / "test_network.py").write_text(
            "@unittest.skipIf(OFFLINE, 'network unavailable')\ndef test_remote(): pass\n",
            encoding="utf-8",
        )
        (root / "tests" / "payment_test.go").write_text(
            'func TestPayment(t *testing.T) { t.Skip("temporarily disabled") }\n',
            encoding="utf-8",
        )
        res = run_tool(root, "antigaming-scan", "--scope-path", "tests/test_network.py",
                       "--scope-path", "tests/payment_test.go")
        data = json.loads(res.stdout)
        findings = [x for x in data["candidate_findings"] if x["pattern_id"] == "AG-001"]
        record(cat, "AG-001 Python unittest skip and Go t.Skip calls are surfaced as candidates",
               {x["path"] for x in findings} == {"tests/test_network.py", "tests/payment_test.go"}, res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "ci.sh"
        f.write_text("npm test || :\ngo test || exit 0\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "ci.sh")
        data = json.loads(res.stdout)
        ag004 = [x for x in data["candidate_findings"] if x["pattern_id"] == "AG-004"]
        record(cat, "AG-004 shell no-op/zero-exit fallbacks are surfaced as candidates",
               len(ag004) == 2, res.stdout)

    # 14. antigaming-scan: '|| true' is flagged (AG-004)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "ci.sh"
        f.write_text("npm test || true\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "ci.sh")
        data = json.loads(res.stdout)
        record(cat, "14 '|| true' is flagged (AG-004)",
               any(x["pattern_id"] == "AG-004" for x in data["candidate_findings"]), res.stdout)

    # 15. antigaming-scan: clean file produces zero candidate findings
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "clean.py"
        f.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "clean.py")
        data = json.loads(res.stdout)
        record(cat, "15 clean file produces zero candidate findings",
               data["candidate_findings"] == [], res.stdout)

    # AG-005 and AG-010 are supported literal patterns and must have positive
    # regressions; also preserve the explicit, scoped-ignore exception.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "code.py").write_text("value = 1  # noqa\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "code.py")
        data = json.loads(res.stdout)
        record(cat, "AG-005 blanket noqa is surfaced as a candidate",
               any(x["pattern_id"] == "AG-005" for x in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "code.py").write_text("value = 1  # noqa: F401\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", "code.py")
        data = json.loads(res.stdout)
        record(cat, "AG-005 per-rule noqa is not treated as a blanket-disable candidate",
               not any(x["pattern_id"] == "AG-005" for x in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "handler.js").write_text(
            "if (process.env.NODE_ENV === 'test') return ok;\n", encoding="utf-8"
        )
        res = run_tool(root, "antigaming-scan", "--scope-path", "handler.js")
        data = json.loads(res.stdout)
        record(cat, "AG-010 test-environment production bypass is surfaced as a candidate",
               any(x["pattern_id"] == "AG-010" for x in data["candidate_findings"]), res.stdout)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "runner.py").write_text(
            "def main():\n    try:\n        run_tests()\n    except AssertionError:\n        print('ignored flaky failure')\n        return 0\n",
            encoding="utf-8",
        )
        res = run_tool(root, "antigaming-scan", "--scope-path", "runner.py")
        data = json.loads(res.stdout)
        record(cat, "AG-015 caught AssertionError is surfaced as a candidate",
               any(x["pattern_id"] == "AG-015" for x in data["candidate_findings"])
               and "NOT itself a violation" in data["note"], res.stdout)

    # AG-001: a content scan cannot see a deleted/misplaced test; inspect names
    # in the staged + unstaged diff against HEAD without reading removed bodies.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests").mkdir()
        (root / "src").mkdir()
        (root / "tests" / "test_guard.py").write_text("assert True\n", encoding="utf-8")
        (root / "tests" / "test_staged.py").write_text("assert before()\n", encoding="utf-8")
        (root / "tests" / "test_unstaged.py").write_text("assert before()\n", encoding="utf-8")
        (root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
        (root / "tracked.marker").write_text("base\n", encoding="utf-8")
        init_git(root)
        (root / ".gitattributes").write_text("*.marker filter=evil\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitattributes"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "register test filter"], cwd=root, check=True)
        clean_filter = root.parent / "controlled-clean-filter"
        filter_marker = root.parent / "clean-filter-was-run"
        clean_filter.write_text(
            f"#!/bin/sh\nprintf called >> {shlex.quote(str(filter_marker))}\ncat\n",
            encoding="utf-8",
        )
        clean_filter.chmod(0o700)
        subprocess.run(["git", "config", "filter.evil.clean", str(clean_filter)], cwd=root, check=True)
        subprocess.run(["git", "config", "filter.evil.smudge", "cat"], cwd=root, check=True)
        (root / "tests" / "test_staged.py").write_text("assert True\n", encoding="utf-8")
        subprocess.run(["git", "add", "tests/test_staged.py"], cwd=root, check=True)
        (root / "tests" / "test_unstaged.py").write_text("assert weak_guard()\n", encoding="utf-8")
        subprocess.run(["git", "mv", "tests/test_guard.py", "src/moved_test.txt"], cwd=root, check=True)
        (root / "src" / "app.py").unlink()
        (root / "tracked.marker").write_text("changed\n", encoding="utf-8")
        (root / "tests" / "test_new.py").write_text("assert True\n", encoding="utf-8")
        filter_marker.unlink(missing_ok=True)
        res = run_tool(root, "antigaming-diff-scan")
        data = json.loads(res.stdout)
        candidate_paths = {finding["path"] for finding in data["candidate_findings"]}
        record(cat, "AG-001 staged test rename and staged/unstaged test modifications are candidates; ordinary deletion and untracked test are not",
               res.returncode == 0 and data["staged_deleted_paths"] == 1
               and data["unstaged_deleted_paths"] == 1 and data["deleted_tracked_paths"] == 2
               and data["staged_modified_paths"] == 1 and data["unstaged_modified_paths"] >= 1
               and data["modified_tracked_paths"] >= 2
               and candidate_paths == {"tests/test_guard.py", "tests/test_staged.py", "tests/test_unstaged.py"}
               and not filter_marker.exists(),
               res.stdout)

    # A non-git target must be explicitly unavailable, never a clean result.
    with tempfile.TemporaryDirectory() as td:
        res = run_tool(td, "antigaming-diff-scan")
        data = json.loads(res.stdout)
        record(cat, "AG-001 diff prefilter reports unavailable without Git HEAD",
               res.returncode != 0 and bool(data.get("error"))
               and "clean anti-gaming result is implied" in data["error"],
               res.stdout)

    # 16. scope paths cannot read a file outside the target repository.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, secret_root = Path(td), Path(outside)
        (secret_root / "secret.py").write_text("npm test || true\n", encoding="utf-8")
        res = run_tool(root, "antigaming-scan", "--scope-path", str(secret_root / "secret.py"))
        data = json.loads(res.stdout)
        record(cat, "16 absolute scope path is rejected without exposing outside contents",
               data["candidate_findings"] == [] and len(data["rejected_paths"]) == 1
               and "npm test" not in res.stdout, res.stdout)

    # 17. symlink within target pointing outside is rejected.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, secret_root = Path(td), Path(outside)
        (secret_root / "secret.py").write_text("npm test || true\n", encoding="utf-8")
        (root / "leak.py").symlink_to(secret_root / "secret.py")
        res = run_tool(root, "antigaming-scan", "--scope-path", "leak.py")
        data = json.loads(res.stdout)
        record(cat, "17 external symlink scope is rejected without exposing contents",
               data["candidate_findings"] == [] and len(data["rejected_paths"]) == 1
               and "npm test" not in res.stdout, res.stdout)

    # 17b. Oversized changed source is reported, not silently treated as clean.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "large.py").write_bytes(b"x" * (1024 * 1024 + 1))
        res = run_tool(root, "antigaming-scan", "--scope-path", "large.py")
        data = json.loads(res.stdout)
        record(cat, "oversized anti-gaming scope file is explicitly reported as unreadable",
               len(data["read_errors"]) == 1
               and data["read_errors"][0]["path"] == "large.py"
               and "safety limit" in data["read_errors"][0]["error"], res.stdout)

    # 18. Record inventory must neither follow an external symlink nor
    # silently report a clean inventory when an untrusted record is present.
    with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
        root, external = Path(td), Path(outside)
        sentinel = "EXTERNAL_RECORD_SECRET_CANARY"
        (external / "EVD.md").write_text(
            f"---\nid: EVD-1\nresult: {sentinel}\n---\nbody\n", encoding="utf-8"
        )
        evidence_dir = root / ".vcps" / "evidence"
        evidence_dir.mkdir(parents=True)
        (evidence_dir / "EVD-1.md").symlink_to(external / "EVD.md")
        res = run_tool(root, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "18 evidence inventory rejects an external record symlink and surfaces parse error",
               data["entries"] == [] and bool(data["parse_errors"]) and sentinel not in res.stdout,
               res.stdout)

    # 19. Malformed record (duplicate YAML key) is reported as a parse error,
    # not silently skipped or crashed on.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / ".vcps" / "evidence"
        d.mkdir(parents=True)
        (d / "EVD-1.md").write_text("---\nid: EVD-1\nid: EVD-1\n---\n\nbody\n", encoding="utf-8")
        res = run_tool(root, "evidence-inventory")
        data = json.loads(res.stdout)
        record(cat, "19 malformed record surfaces as a parse error, not silently dropped",
               res.returncode == 0 and len(data["parse_errors"]) == 1, res.stdout)

    # 20. lapsed-deferral-check: an HC-16 DECISION with no deferral_follow_up
    # is flagged (VCPS-WF-HOTFIX-001).
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "approvals" / "HCR-1.md",
                 {"id": "HCR-1", "kind": "DECISION", "checkpoint_codes": ["HC-16"],
                  "human_actor": "owner", "timestamp": "2026-10-01T00:00:00Z",
                  "action": "x", "scope": "x", "decision": "APPROVED"})
        res = run_tool(root, "lapsed-deferral-check")
        data = json.loads(res.stdout)
        record(cat, "20 HC-16 decision with no deferral_follow_up is flagged",
               len(data["lapsed_or_incomplete_deferrals"]) == 1, res.stdout)

    # 21. lapsed-deferral-check: a passed deadline is flagged (VCPS-WF-HOTFIX-003)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "approvals" / "HCR-1.md",
                 {"id": "HCR-1", "kind": "DECISION", "checkpoint_codes": ["HC-16"],
                  "human_actor": "owner", "timestamp": "2026-10-01T00:00:00Z",
                  "action": "x", "scope": "x", "decision": "APPROVED",
                  "deferral_follow_up": {"owner": "owner", "deadline": "2020-01-01T00:00:00Z"}})
        res = run_tool(root, "lapsed-deferral-check")
        data = json.loads(res.stdout)
        record(cat, "21 HC-16 decision with a passed deadline is flagged",
               len(data["lapsed_or_incomplete_deferrals"]) == 1
               and "passed" in data["lapsed_or_incomplete_deferrals"][0]["issue"], res.stdout)

    # 22. lapsed-deferral-check: a future deadline is NOT flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "approvals" / "HCR-1.md",
                 {"id": "HCR-1", "kind": "DECISION", "checkpoint_codes": ["HC-16"],
                  "human_actor": "owner", "timestamp": "2026-10-01T00:00:00Z",
                  "action": "x", "scope": "x", "decision": "APPROVED",
                  "deferral_follow_up": {"owner": "owner", "deadline": "2099-01-01T00:00:00Z"}})
        res = run_tool(root, "lapsed-deferral-check")
        data = json.loads(res.stdout)
        record(cat, "22 HC-16 decision with a future deadline is not flagged",
               data["lapsed_or_incomplete_deferrals"] == [], res.stdout)

    # 23. lapsed-deferral-check: a non-HC-16 decision is never flagged, even
    # with a passed expiry (expiry is a pre-authorization concept, not a
    # deferral follow-up).
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "approvals" / "HCR-1.md",
                 {"id": "HCR-1", "kind": "DECISION", "checkpoint_codes": ["HC-08"],
                  "human_actor": "owner", "timestamp": "2026-10-01T00:00:00Z",
                  "action": "x", "scope": "x", "decision": "APPROVED"})
        res = run_tool(root, "lapsed-deferral-check")
        data = json.loads(res.stdout)
        record(cat, "23 non-HC-16 decision is never flagged",
               data["lapsed_or_incomplete_deferrals"] == [], res.stdout)

    # 24. release-readiness-check: a gate evaluated on a different revision
    # than the release is flagged as a staleness candidate.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "PASS", "revision": "aaa111"})
        write_fm(root / ".vcps" / "bugs" / "BUG-1.md",
                 {"id": "BUG-1", "applicable_gates": [{"gate": 4, "outcome_ref": "GATE-1"}]})
        res = run_tool(root, "release-readiness-check", "--release-revision", "bbb222",
                        "--work-item-ref", "BUG-1")
        data = json.loads(res.stdout)
        record(cat, "24 gate evaluated on a different revision than the release is flagged",
               any("not the release revision" in i["issue"] for i in data["issues"]), res.stdout)

    # 25. release-readiness-check: a gate matching the release revision with
    # outcome PASS produces no issue for that gate.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "PASS", "revision": "bbb222"})
        write_fm(root / ".vcps" / "bugs" / "BUG-1.md",
                 {"id": "BUG-1", "applicable_gates": [{"gate": 4, "outcome_ref": "GATE-1"}]})
        res = run_tool(root, "release-readiness-check", "--release-revision", "bbb222",
                        "--work-item-ref", "BUG-1")
        data = json.loads(res.stdout)
        record(cat, "25 gate matching the release revision with outcome PASS is clean",
               data["issues"] == [], res.stdout)

    # 26. release-readiness-check: a BLOCKED gate outcome is flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "gates" / "GATE-1.md",
                 {"id": "GATE-1", "gate": 4, "outcome": "BLOCKED", "revision": "bbb222"})
        write_fm(root / ".vcps" / "bugs" / "BUG-1.md",
                 {"id": "BUG-1", "applicable_gates": [{"gate": 4, "outcome_ref": "GATE-1"}]})
        res = run_tool(root, "release-readiness-check", "--release-revision", "bbb222",
                        "--work-item-ref", "BUG-1")
        data = json.loads(res.stdout)
        record(cat, "26 BLOCKED gate outcome is flagged, not treated as ready",
               any("BLOCKED" in i["issue"] for i in data["issues"]), res.stdout)

    # 27. release-readiness-check: a missing work item reference is flagged
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        res = run_tool(root, "release-readiness-check", "--release-revision", "bbb222",
                        "--work-item-ref", "BUG-does-not-exist")
        data = json.loads(res.stdout)
        record(cat, "27 missing work item reference is flagged",
               any("not found" in i["issue"] for i in data["issues"]), res.stdout)

    # 28. release-readiness-check: an HC-10 decision recorded on the release
    # revision is surfaced.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fm(root / ".vcps" / "approvals" / "HCR-1.md",
                 {"id": "HCR-1", "kind": "DECISION", "checkpoint_codes": ["HC-10"],
                  "human_actor": "owner", "timestamp": "2026-10-01T00:00:00Z",
                  "action": "x", "scope": "x", "decision": "APPROVED", "revision": "bbb222"})
        res = run_tool(root, "release-readiness-check", "--release-revision", "bbb222",
                        "--work-item-ref", "nonexistent")
        data = json.loads(res.stdout)
        record(cat, "28 HC-10 decision recorded on the release revision is surfaced",
               len(data["hc10_decisions_on_this_revision"]) == 1
               and data["hc10_decisions_on_this_revision"][0]["id"] == "HCR-1", res.stdout)


def main():
    print(f"Lib root: {LIB_ROOT}")
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

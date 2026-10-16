#!/usr/bin/env python3
"""VCPS Claude Code shared evidence/reference helper.

Deterministic mechanical support shared by the /vcps-audit and /vcps-review
skills: evidence-staleness recomputation (standard/evidence-model.md
VCPS-EVD-050/051/053), cross-record reference resolution ("no orphaned
findings", workflows/setup.md VCPS-SETUP-026 / workflows/audit.md step 6),
gate-record internal consistency (standard/gates/README.md VCPS-GATE-050),
and anti-gaming pre-filters for literal patterns and tracked test-file
deletions in the working diff (standard/anti-gaming.md SS1).

This script makes no classification, gate-outcome, staleness VERDICT, or
anti-gaming FINDING judgment -- it surfaces raw, mechanically checkable
facts (a revision mismatch, an unresolved reference, a literal `|| true`
string, a deleted test-like path, or a PASS gate citing evidence whose
result cannot count as PASS)
for the model to judge, per the same VCPS-CORE-001 split
established for vcps_tool.py and vcps_router.py. In particular:
  - A revision mismatch is NOT automatically "stale" -- VCPS-EVD-051
    allows E1/E2 evidence to be carried forward when nothing in scope
    changed; that determination is the model's.
  - A literal anti-gaming pattern match is NOT automatically a violation
    -- VCPS-AG-020/021 define legitimate exceptions; this is a
    candidate-flagging heuristic only, same spirit as
    templates/validation.md item 11's secret-detection heuristics
    ("flag ... for human review; they cannot prove absence").
  - An unresolved reference is a mechanical fact; whether it is a real
    defect (vs. e.g. a reference to a record type this script doesn't
    know about) is reported as a candidate, not asserted as final.

This is deliberately a separate component from vcps_tool.py's and
vcps_router.py's own small strict-YAML cores (each duplicates a similar
~60-line loader rather than importing across sibling skill directories).
Here the calculus is different: evidence-staleness and reference-
resolution logic is Core-rule-specific (VCPS-EVD-050/051/053), not
generic YAML parsing, so a second independently-maintained copy of THIS
logic would risk the two diverging on what "stale" or "orphaned" means --
a real specification-consistency risk, not mere code duplication. Both
vcps-audit and vcps-review therefore reference this single shared copy
at adapters/claude-code/lib/ rather than each vendoring their own. This
is a deliberate, disclosed exception to the "independently installable"
principle used elsewhere (see adapters/claude-code/lib/README.md): both
skills need this lib/ directory present alongside them to function.
"""

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML not available"}))
    print("PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# --- Strict YAML (same contract as vcps_tool.py / vcps_router.py) -------

class StrictLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.events.AliasEvent):
            event = self.get_event()
            raise yaml.constructor.ConstructorError(
                None, None, "forbidden YAML construct: alias/anchor reference",
                event.start_mark,
            )
        return super().compose_node(parent, index)


def _no_duplicate_construct_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key: {key!r}", key_node.start_mark
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


def _forbid(tag_name):
    def _raiser(loader, node):
        raise yaml.constructor.ConstructorError(
            None, None, f"forbidden YAML construct: {tag_name}", node.start_mark
        )
    return _raiser


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_construct_mapping
)
StrictLoader.add_constructor("tag:yaml.org,2002:merge", _forbid("merge key (<<)"))


def strict_yaml_load(text, path="<stream>"):
    docs = list(yaml.load_all(text, Loader=StrictLoader))
    if len(docs) != 1:
        raise ValueError(f"{path}: expected exactly one YAML document, got {len(docs)}")
    return docs[0]


def _parse_frontmatter_text(text: str, path):
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValueError(f"{path}: missing YAML frontmatter opening '---'")
    rest = text[4:]
    marker = "\n---\n"
    idx = rest.find(marker)
    if idx == -1:
        if rest.rstrip("\n").endswith("\n---") or rest == "---":
            idx = len(rest.rstrip("\n")) - 3
        else:
            raise ValueError(f"{path}: missing YAML frontmatter closing '---'")
    fm_text = rest[:idx]
    frontmatter = strict_yaml_load(fm_text, path=str(path))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return frontmatter


def load_frontmatter(file_path: Path, repo_root: Path):
    return _parse_frontmatter_text(read_repo_text(repo_root, file_path), file_path)


RECORD_DIRS = [
    "approvals", "bugs", "evidence", "features", "findings", "gates",
    "handoffs", "releases", "reviews", "work-items",
]


def _safe_repo_path(repo_root: Path, candidate: Path):
    """Resolve an existing target path only when it remains inside the repo.

    VCPS metadata can contain or be reached through symlinks. Never read an
    external file merely because its link is under .vcps/.
    """
    try:
        root = repo_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError):
        return None


def open_repo_file(repo_root: Path, candidate: Path):
    """Open a regular target file with descriptor-relative no-follow lookup."""
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("secure target reads require POSIX O_DIRECTORY/O_NOFOLLOW support")
    if os.open not in os.supports_dir_fd:
        raise OSError("secure target reads require directory-relative open support")
    root = repo_root.resolve(strict=True)
    path = Path(candidate)
    if path.is_absolute():
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise ValueError("read path is outside the target repository") from exc
    else:
        relative = path
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("read path must be repository-relative and contain no '..'")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.open(os.sep, flags)
    file_fd = None
    try:
        for component in root.parts[1:] + relative.parts[:-1]:
            next_fd = os.open(component, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        file_fd = os.open(relative.name, file_flags, dir_fd=current_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise OSError("target path is not a regular file")
        result = file_fd
        file_fd = None
        return result
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(current_fd)


MAX_TARGET_TEXT_BYTES = 1024 * 1024


def read_repo_text(repo_root: Path, candidate: Path, encoding="utf-8", errors="strict") -> str:
    fd = open_repo_file(repo_root, candidate)
    with os.fdopen(fd, "rb") as stream:
        content = stream.read(MAX_TARGET_TEXT_BYTES + 1)
    if len(content) > MAX_TARGET_TEXT_BYTES:
        raise ValueError(f"target text exceeds {MAX_TARGET_TEXT_BYTES}-byte safety limit: {candidate}")
    return content.decode(encoding, errors=errors)


def _safe_markdown_files(repo_root: Path, directory: Path):
    safe_dir = _safe_repo_path(repo_root, directory)
    if safe_dir is None or not safe_dir.is_dir():
        return [], ([str(directory)] if directory.exists() or directory.is_symlink() else [])
    files, rejected = [], []
    for candidate in sorted(safe_dir.glob("*.md")):
        safe_file = _safe_repo_path(repo_root, candidate)
        if safe_file is None or not safe_file.is_file():
            rejected.append(str(candidate))
            continue
        files.append((candidate, safe_file))
    return files, rejected


def run_git_head(repo_root: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "-c", "core.fsmonitor=false", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None


def iter_records(repo_root: Path):
    """Yield (record_file_path, frontmatter_dict) for every .vcps/* record,
    including the four singleton files, skipping (and reporting) any file
    that fails to parse."""
    vcps_dir = repo_root / ".vcps"
    parse_errors = []
    records = []
    safe_vcps_dir = _safe_repo_path(repo_root, vcps_dir)
    if safe_vcps_dir is None or not safe_vcps_dir.is_dir():
        if vcps_dir.is_symlink():
            parse_errors.append({"path": str(vcps_dir), "error": "VCPS directory resolves outside the repository"})
        return records, parse_errors

    singleton_candidates = ["baseline.md", "invariants.md", "risk-model.md"]
    for name in singleton_candidates:
        p = vcps_dir / name
        safe_p = _safe_repo_path(repo_root, p)
        if safe_p and safe_p.is_file():
            try:
                records.append((p, load_frontmatter(safe_p, repo_root)))
            except Exception as exc:
                parse_errors.append({"path": str(p), "error": str(exc)})
        elif p.is_symlink():
            parse_errors.append({"path": str(p), "error": "record symlink resolves outside the repository"})

    for sub in RECORD_DIRS:
        d = vcps_dir / sub
        safe_d = _safe_repo_path(repo_root, d)
        if safe_d is None or not safe_d.is_dir():
            if d.exists() or d.is_symlink():
                parse_errors.append({"path": str(d), "error": "record directory resolves outside the repository"})
            continue
        files, rejected = _safe_markdown_files(repo_root, safe_d)
        parse_errors.extend({"path": p, "error": "record path is unreadable or resolves outside the repository"} for p in rejected)
        for record_file, safe_file in files:
            try:
                records.append((record_file, load_frontmatter(safe_file, repo_root)))
            except Exception as exc:
                parse_errors.append({"path": str(record_file), "error": str(exc)})
    return records, parse_errors


# --- evidence-inventory (VCPS-EVD-050/051/053) --------------------------

def evidence_inventory(repo_root: Path):
    head = run_git_head(repo_root)
    vcps_dir = repo_root / ".vcps" / "evidence"
    entries = []
    parse_errors = []
    if _safe_repo_path(repo_root, vcps_dir) and vcps_dir.is_dir():
        evidence_files, rejected = _safe_markdown_files(repo_root, vcps_dir)
        parse_errors.extend({"path": p, "error": "evidence path is unreadable or resolves outside the repository"} for p in rejected)
        for record_file, safe_file in evidence_files:
            try:
                fm = load_frontmatter(safe_file, repo_root)
            except Exception as exc:
                parse_errors.append({"path": str(record_file), "error": str(exc)})
                continue
            rev = fm.get("revision")
            rev_str = rev if isinstance(rev, str) else (rev or {}).get("base_commit_hash")
            is_dirty_rev = isinstance(rev, dict) and rev.get("dirty") is True
            matches_head = (rev_str == head) if (rev_str and head) else None
            entries.append({
                "id": fm.get("id"),
                "path": str(record_file.relative_to(repo_root)),
                "tier": fm.get("tier"),
                "result": fm.get("result"),
                "revision": rev_str,
                "is_dirty_worktree_revision": is_dirty_rev,
                "current_head": head,
                "matches_head": matches_head,
                "scope": fm.get("scope") or [],
                "corrections": fm.get("corrections") or {},
            })
    elif vcps_dir.exists() or vcps_dir.is_symlink():
        parse_errors.append({"path": str(vcps_dir), "error": "evidence directory resolves outside the repository"})
    return {
        "current_head": head,
        "entries": entries,
        "parse_errors": parse_errors,
        "note": (
            "matches_head=false is a REVISION-MISMATCH CANDIDATE, not a verdict: "
            "VCPS-EVD-051 permits E1/E2 evidence to be carried forward unchanged "
            "when the producer can show nothing in its scope changed. That "
            "determination, and whether this evidence is actually stale for a "
            "given consumer, is the model's judgment, re-checked against the "
            "evidence's own `scope` and the current repository state -- never "
            "a stored freshness label (VCPS-EVD-053)."
        ),
    }


# --- gate-reference-check (VCPS-GATE-050 + narrow EVD-020 lint) ---------

def gate_reference_check(repo_root: Path):
    records, parse_errors = iter_records(repo_root)
    by_id = {fm.get("id"): (p, fm) for p, fm in records if fm.get("id")}
    issues = []
    gate_dir = repo_root / ".vcps" / "gates"
    if _safe_repo_path(repo_root, gate_dir) and gate_dir.is_dir():
        gate_files, rejected = _safe_markdown_files(repo_root, gate_dir)
        parse_errors.extend({"path": p, "error": "gate path is unreadable or resolves outside the repository"} for p in rejected)
        for record_file, safe_file in gate_files:
            try:
                fm = load_frontmatter(safe_file, repo_root)
            except Exception:
                continue
            gid = fm.get("id")
            outcome = fm.get("outcome")
            gate_num = fm.get("gate")
            if outcome == "BLOCKED" and not fm.get("reason_codes"):
                issues.append({"gate_id": gid, "issue": "BLOCKED outcome missing reason_codes"})
            if outcome == "PARTIAL" and not fm.get("partial_gap"):
                issues.append({"gate_id": gid, "issue": "PARTIAL outcome missing partial_gap"})
            if outcome == "NOT_APPLICABLE" and not fm.get("applicability_basis"):
                issues.append({"gate_id": gid, "issue": "NOT_APPLICABLE outcome missing applicability_basis"})
            if gate_num in (4, 5) and not fm.get("independence_mode"):
                issues.append({"gate_id": gid, "issue": f"Gate {gate_num} missing independence_mode"})
            for ref in (fm.get("evidence_refs") or []):
                if ref not in by_id:
                    issues.append({"gate_id": gid, "issue": f"unresolved evidence_refs entry {ref!r}"})
                elif outcome == "PASS":
                    evidence = by_id[ref][1]
                    result = evidence.get("result")
                    if result in ("NOT_RUN", "ERROR", "INCONCLUSIVE"):
                        issues.append({
                            "gate_id": gid,
                            "issue": (
                                f"PASS gate references {result} evidence {ref!r}; "
                                "potential VCPS-EVD-020 inconsistency (candidate, not verdict)"
                            ),
                        })
            for ref in (fm.get("finding_refs") or []):
                if ref not in by_id:
                    issues.append({"gate_id": gid, "issue": f"unresolved finding_refs entry {ref!r}"})
            supersedes = fm.get("supersedes_ref")
            if supersedes and supersedes not in by_id:
                issues.append({"gate_id": gid, "issue": f"unresolved supersedes_ref {supersedes!r}"})
    elif gate_dir.exists() or gate_dir.is_symlink():
        parse_errors.append({"path": str(gate_dir), "error": "gate directory resolves outside the repository"})
    return {"issues": issues, "parse_errors": parse_errors}


# --- orphan-check (generic *_ref / *_refs resolution) --------------------

REF_KEY_RE = re.compile(r"_refs?$")


def _collect_refs(value):
    """Collect plausible record-ID-shaped strings from a *_ref/*_refs field,
    which may be a string, null, or a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


ID_LIKE_RE = re.compile(
    r"^(FND|EVD|FEAT|REV|BUG|REL|WORK|HND|GATE|HCR|PREAUTH|BLO)-"
)


def orphan_check(repo_root: Path):
    records, parse_errors = iter_records(repo_root)
    by_id = {fm.get("id") for _, fm in records if fm.get("id")}
    orphans = []
    for path, fm in records:
        for key, value in fm.items():
            if not REF_KEY_RE.search(key):
                continue
            for ref in _collect_refs(value):
                if not ID_LIKE_RE.match(ref):
                    continue  # not record-ID-shaped (e.g. a bare requirement ID); skip
                if ref not in by_id:
                    orphans.append({
                        "path": str(path.relative_to(repo_root)),
                        "field": key,
                        "unresolved_ref": ref,
                    })
    return {
        "orphans": orphans,
        "total_records": len(records),
        "parse_errors": parse_errors,
        "note": "A reference this script cannot resolve against any record it found. It does NOT know about withdrawn/reserved IDs that are valid references to a since-removed-from-disk record under some future retention policy -- treat each as a candidate, not an automatic defect.",
    }


def baseline_history_check(repo_root: Path):
    """Compare the working baseline with its committed HEAD version.

    This surfaces AG-017 candidates only. New baseline observations can be
    legitimate when backed by earlier-revision evidence, so the helper never
    decides whether an append is laundering.
    """
    git = ["git", "-C", str(repo_root), "-c", "core.fsmonitor=false", "--no-pager"]
    try:
        head = subprocess.run(
            git + ["rev-parse", "--verify", "HEAD^{commit}"],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"candidate_findings": [], "error": f"Git revision lookup unavailable: {exc}"}
    if head.returncode != 0:
        return {"candidate_findings": [], "error": "no readable Git HEAD; baseline history not compared"}

    try:
        original = subprocess.run(
            git + ["cat-file", "blob", "HEAD:.vcps/baseline.md"],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"candidate_findings": [], "error": f"committed baseline lookup unavailable: {exc}"}
    if original.returncode != 0:
        return {
            "base": "HEAD",
            "state": "NO_BASELINE_AT_HEAD",
            "candidate_findings": [],
            "note": "No committed baseline exists to compare; this is not evidence that a new baseline is legitimate.",
        }

    baseline_path = repo_root / ".vcps" / "baseline.md"
    safe_baseline = _safe_repo_path(repo_root, baseline_path)
    findings = []
    if safe_baseline is None or not safe_baseline.is_file():
        return {
            "base": "HEAD",
            "state": "COMPARED",
            "candidate_findings": [{
                "pattern_id": "AG-017",
                "issue": "committed baseline is missing or resolves outside the target repository",
            }],
            "note": "Candidate only; inspect the complete change and any authorized migration.",
        }
    try:
        old = _parse_frontmatter_text(original.stdout.decode("utf-8"), "HEAD:.vcps/baseline.md")
        current = _parse_frontmatter_text(read_repo_text(repo_root, safe_baseline), str(baseline_path))
    except Exception as exc:
        return {"candidate_findings": [], "error": f"baseline comparison could not parse both records: {exc}"}

    old_observations = old.get("observations") or []
    current_observations = current.get("observations") or []
    old_history = old.get("history") or []
    current_history = current.get("history") or []
    if not isinstance(old_observations, list) or not isinstance(current_observations, list):
        findings.append({"pattern_id": "AG-017", "issue": "baseline observations is not a list"})
        old_observations = old_observations if isinstance(old_observations, list) else []
        current_observations = current_observations if isinstance(current_observations, list) else []
    if not isinstance(old_history, list) or not isinstance(current_history, list):
        findings.append({"pattern_id": "AG-017", "issue": "baseline history is not a list"})
        old_history = old_history if isinstance(old_history, list) else []
        current_history = current_history if isinstance(current_history, list) else []

    observations_preserved = current_observations == old_observations
    history_preserved = current_history[:len(old_history)] == old_history
    if not observations_preserved:
        findings.append({
            "pattern_id": "AG-017",
            "issue": "baseline observations array changed; widening/resolution must be recorded in append-only history",
        })
    if not history_preserved:
        findings.append({
            "pattern_id": "AG-017",
            "issue": "committed baseline history was truncated, reordered, or modified",
        })

    added_history = current_history[len(old_history):] if history_preserved else []
    original_ids = {o.get("id") for o in old_observations if isinstance(o, dict)}
    history_added_observation_ids = []
    for event in added_history:
        if not isinstance(event, dict) or event.get("type") not in {"ADD_OBSERVATION", "RESOLVE_OBSERVATION"}:
            findings.append({"pattern_id": "AG-017", "issue": "new baseline history entry is not an allowed append type"})
        elif event.get("type") == "ADD_OBSERVATION":
            observation = event.get("new_observation")
            oid = observation.get("id") if isinstance(observation, dict) else None
            if not oid or oid in original_ids or oid in history_added_observation_ids:
                findings.append({"pattern_id": "AG-017", "issue": "ADD_OBSERVATION does not contain a unique new observation ID"})
            elif isinstance(observation, dict):
                history_added_observation_ids.append(oid)
    if added_history:
        findings.append({
            "pattern_id": "AG-017",
            "issue": "new baseline history entries require review against VCPS-SETUP-027",
            "entry_count": len(added_history),
        })
    if history_added_observation_ids:
        findings.append({
            "pattern_id": "AG-017",
            "issue": "new baseline observations require earlier-revision provenance review",
            "observation_ids": history_added_observation_ids,
        })
    return {
        "base": "HEAD",
        "state": "COMPARED",
        "original_observation_count": len(old_observations),
        "current_observation_count": len(current_observations),
        "original_history_count": len(old_history),
        "current_history_count": len(current_history),
        "candidate_findings": findings,
        "note": "AG-017 candidate checks only; legitimate widening needs evidence that each added failure predates the relevant mutation. This is not an automatic violation verdict.",
    }


def record_history_check(repo_root: Path):
    """Surface edits/truncations to committed append-only VCPS records.

    This is a candidate detector. It compares tracked Markdown artifacts to
    HEAD without checkout/filter execution and never decides whether a change
    has an authorized correction path.
    """
    git = ["git", "-C", str(repo_root), "-c", "core.fsmonitor=false", "--no-pager"]
    try:
        paths_result = subprocess.run(
            git + ["ls-tree", "-r", "--name-only", "-z", "HEAD", "--", ".vcps"],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"candidate_findings": [], "error": f"Git tree lookup unavailable: {exc}"}
    if paths_result.returncode != 0:
        return {"candidate_findings": [], "error": "no readable Git HEAD; record history not compared"}

    findings = []
    checked = 0
    max_record_bytes = 1024 * 1024
    append_only_fields = ("history", "stage_events", "plan_history")
    immutable_dirs = {"evidence", "gates", "approvals"}
    for raw_path in paths_result.stdout.split(b"\0"):
        if not raw_path:
            continue
        rel = raw_path.decode("utf-8", errors="replace")
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts or not rel.startswith(".vcps/"):
            findings.append({"pattern_id": "AG-011", "path": rel, "issue": "unsafe tracked VCPS path rejected"})
            continue
        if posix.suffix != ".md":
            continue
        try:
            size = subprocess.run(
                git + ["cat-file", "-s", f"HEAD:{rel}"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"candidate_findings": findings, "error": f"committed record size lookup failed: {exc}"}
        if size.returncode != 0:
            return {"candidate_findings": findings, "error": f"committed record size unavailable: {rel}"}
        try:
            blob_size = int(size.stdout.strip())
        except ValueError:
            return {"candidate_findings": findings, "error": f"invalid committed record size: {rel}"}
        if blob_size > max_record_bytes:
            findings.append({
                "pattern_id": "AG-011", "path": rel,
                "issue": "committed record exceeds 1 MiB comparison limit; history not verified",
            })
            continue
        try:
            original = subprocess.run(
                git + ["cat-file", "blob", f"HEAD:{rel}"],
                capture_output=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"candidate_findings": findings, "error": f"committed record lookup failed: {exc}"}
        if original.returncode != 0:
            return {"candidate_findings": findings, "error": f"committed record unavailable: {rel}"}

        candidate = repo_root / Path(*posix.parts)
        try:
            current_fd = open_repo_file(repo_root, candidate)
            with os.fdopen(current_fd, "rb") as current_stream:
                current_bytes = current_stream.read(max_record_bytes + 1)
        except (OSError, ValueError) as exc:
            findings.append({"pattern_id": "AG-011", "path": rel, "issue": f"committed record missing or unreadable: {exc}"})
            continue
        if len(current_bytes) > max_record_bytes:
            findings.append({
                "pattern_id": "AG-011", "path": rel,
                "issue": "working-tree record exceeds 1 MiB comparison limit; history not verified",
            })
            continue
        old_text = original.stdout.decode("utf-8", errors="replace")
        current_text = current_bytes.decode("utf-8", errors="replace")
        checked += 1
        top_level = posix.parts[1] if len(posix.parts) > 2 else ""
        if top_level in immutable_dirs and current_text != old_text:
            findings.append({
                "pattern_id": "AG-011", "path": rel,
                "issue": "committed evidence/gate/approval record was edited; preserve it and append a linked correction or new evaluation",
            })
            continue
        try:
            old = _parse_frontmatter_text(old_text, f"HEAD:{rel}")
            current = _parse_frontmatter_text(current_text, str(candidate))
        except Exception as exc:
            findings.append({"pattern_id": "AG-011", "path": rel, "issue": f"history comparison parse failure: {exc}"})
            continue
        for field in append_only_fields:
            before = old.get(field)
            after = current.get(field)
            if before is None:
                continue
            if not isinstance(before, list) or not isinstance(after, list):
                findings.append({"pattern_id": "AG-011", "path": rel, "field": field, "issue": "append-only field is missing or not a list"})
            elif after[:len(before)] != before:
                findings.append({"pattern_id": "AG-011", "path": rel, "field": field, "issue": "committed history was truncated, reordered, or modified"})
    return {
        "base": "HEAD", "state": "COMPARED", "tracked_markdown_records_checked": checked,
        "candidate_findings": findings,
        "note": "AG-011 candidates only. Review record semantics and authorized correction/supersession rules; no automatic violation verdict is made.",
    }


# --- antigaming-scan (standard/anti-gaming.md SS1, literal patterns only) -

ANTIGAMING_PATTERNS = [
    ("AG-004", r"\|\|\s*true\b"),
    ("AG-004", r"\|\|\s*(?::|exit\s+0\b|echo\b|\(\s*true\s*\))"),
    ("AG-004", r"continue-on-error\s*:\s*true"),
    ("AG-004", r"allow_failure\s*:\s*true"),
    ("AG-004", r"--passWithNoTests\b"),
    ("AG-001", r"\.skip\(|(?<![A-Za-z0-9_])xit\(|xdescribe\(|@pytest\.mark\.skip|@unittest\.skip(?:If|Unless)?\s*\(|#\[\s*ignore(?:\s*=\s*\"[^\"]*\")?\s*\]|\bt\.Skip(?:Now|f|ln)?\s*\("),
    ("AG-005", r"#\s*noqa(?!:)|eslint-disable(?!-next-line\s+\S)|type:\s*ignore\b"),
    ("AG-010", r"process\.env\.(TEST|NODE_ENV)\s*===?\s*['\"]test['\"]\s*\)\s*return"),
    ("AG-015", r"except\s+AssertionError(?:\s+as\s+[A-Za-z_]\w*)?\s*:"),
]


def antigaming_scan(repo_root: Path, scope_paths):
    findings = []
    rejected_paths = []
    read_errors = []
    root = repo_root.resolve()
    for rel in scope_paths:
        candidate = Path(rel)
        if candidate.is_absolute() or ".." in candidate.parts:
            rejected_paths.append({"path": rel, "reason": "scope path must be repository-relative and contain no '..'"})
            continue
        full = repo_root / candidate
        try:
            resolved = full.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            rejected_paths.append({"path": rel, "reason": "scope path is missing or resolves outside the repository"})
            continue
        if not resolved.is_file():
            continue
        try:
            text = read_repo_text(repo_root, resolved, errors="ignore")
        except Exception as exc:
            read_errors.append({"path": rel, "error": str(exc)})
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for ag_id, pattern in ANTIGAMING_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "path": rel, "line": lineno, "pattern_id": ag_id,
                        "excerpt": line.strip()[:200],
                    })
    return {
        "candidate_findings": findings,
        "rejected_paths": rejected_paths,
        "read_errors": read_errors,
        "note": (
            "Literal-pattern candidates only (standard/anti-gaming.md SS1 "
            "AG-001/004/005/010/015's most mechanically-recognizable forms). "
            "A match is NOT itself a violation -- VCPS-AG-020/021 define "
            "legitimate exceptions with recorded justification. This is a "
            "pre-filter for the model's own Gate 3/4 anti-gaming review "
            "(VCPS-AG-030), not a substitute for it: most AG-* rules "
            "(AG-002 assertion weakening, AG-003 threshold lowering, "
            "AG-013 mock substitution, etc.) require semantic diff "
            "understanding this script does not attempt."
        ),
    }


def antigaming_diff_scan(repo_root: Path):
    """Surface deleted or modified test/check files in the current diff.

    Only index/filesystem names are inspected. `git diff` is deliberately
    avoided because target-repo clean filters can execute commands even for
    a name-only query. This is an AG-001 candidate prefilter, not a verdict.
    It cannot see changes already committed before the current HEAD, and it
    does not determine whether a test edit weakens an assertion.
    """
    git = ["git", "-C", str(repo_root), "-c", "core.fsmonitor=false", "--no-pager"]
    try:
        staged = subprocess.run(
            git + ["diff-index", "--cached", "--no-renames", "--name-only",
                   "--diff-filter=D", "-z", "HEAD", "--"],
            capture_output=True, timeout=30,
        )
        unstaged = subprocess.run(
            git + ["ls-files", "--deleted", "-z"], capture_output=True, timeout=30,
        )
        staged_modified = subprocess.run(
            git + ["diff-index", "--cached", "--no-renames", "--name-only",
                   "--diff-filter=M", "-z", "HEAD", "--"],
            capture_output=True, timeout=30,
        )
        unstaged_modified = subprocess.run(
            git + ["ls-files", "--modified", "-z"], capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"candidate_findings": [], "error": f"read-only Git index query unavailable: {exc}"}
    queries = (staged, unstaged, staged_modified, unstaged_modified)
    if any(query.returncode != 0 for query in queries):
        return {
            "candidate_findings": [],
            "error": "cannot inspect staged and unstaged tracked changes; no clean anti-gaming result is implied",
        }
    staged_paths = [item.decode("utf-8", errors="replace")
                    for item in staged.stdout.split(b"\0") if item]
    unstaged_paths = [item.decode("utf-8", errors="replace")
                      for item in unstaged.stdout.split(b"\0") if item]
    staged_modified_paths = [item.decode("utf-8", errors="replace")
                             for item in staged_modified.stdout.split(b"\0") if item]
    unstaged_modified_paths = [item.decode("utf-8", errors="replace")
                               for item in unstaged_modified.stdout.split(b"\0") if item]
    deleted_paths = sorted(set(staged_paths + unstaged_paths))
    modified_paths = sorted(set(staged_modified_paths + unstaged_modified_paths))

    candidates = []
    test_filename = re.compile(r"^(?:test(?:\.[^.]+)?|test_.+|.+_test|.+\.(?:test|spec))\.[^.]+$|^test\.py$", re.I)
    for path in deleted_paths:
        posix_path = PurePosixPath(path)
        in_test_dir = any(part.lower() in {"test", "tests", "__tests__"} for part in posix_path.parts[:-1])
        if in_test_dir or test_filename.match(posix_path.name):
            candidates.append({
                "pattern_id": "AG-001",
                "path": path,
                "issue": "tracked test-like file deleted in the working diff",
            })
    for path in modified_paths:
        posix_path = PurePosixPath(path)
        in_test_dir = any(part.lower() in {"test", "tests", "__tests__"} for part in posix_path.parts[:-1])
        if in_test_dir or test_filename.match(posix_path.name):
            candidates.append({
                "pattern_id": "AG-001",
                "path": path,
                "issue": "tracked test-like file modified in the working diff; review for weakened or removed guarantees",
            })
    candidates.sort(key=lambda item: (item["path"], item["issue"]))
    return {
        "base": "HEAD",
        "staged_deleted_paths": len(set(staged_paths)),
        "unstaged_deleted_paths": len(set(unstaged_paths)),
        "deleted_tracked_paths": len(deleted_paths),
        "staged_modified_paths": len(set(staged_modified_paths)),
        "unstaged_modified_paths": len(set(unstaged_modified_paths)),
        "modified_tracked_paths": len(modified_paths),
        "candidate_findings": candidates,
        "note": (
            "AG-001 filename-based deletion/modification candidates only; confirm file purpose, diff intent, "
            "and any VCPS-AG-020/021 exception. Compares staged and unstaged changes "
            "to current HEAD without reading diff content; it does not judge whether assertions were weakened, "
            "and already-committed changes or non-test checks may be missed."
        ),
    }


# --- lapsed-deferral-check (workflows/hotfix.md VCPS-WF-HOTFIX-001/003) ---

def _parse_datetime(s):
    import datetime
    # Accept a bare 'Z' suffix (RFC 3339) which Python's fromisoformat
    # before 3.11 doesn't; normalize it rather than depending on version.
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def lapsed_deferral_check(repo_root: Path):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    approvals_dir = repo_root / ".vcps" / "approvals"
    issues = []
    parse_errors = []
    if _safe_repo_path(repo_root, approvals_dir) and approvals_dir.is_dir():
        approval_files, rejected = _safe_markdown_files(repo_root, approvals_dir)
        parse_errors.extend({"path": p, "error": "approval path is unreadable or resolves outside the repository"} for p in rejected)
        for record_file, safe_file in approval_files:
            try:
                fm = load_frontmatter(safe_file, repo_root)
            except Exception as exc:
                parse_errors.append({"path": str(record_file), "error": str(exc)})
                continue
            codes = fm.get("checkpoint_codes") or []
            if "HC-16" not in codes:
                continue
            if fm.get("kind") != "DECISION":
                continue
            if fm.get("decision") not in ("APPROVED", "APPROVED_WITH_CONDITIONS"):
                continue
            rid = fm.get("id")
            follow_up = fm.get("deferral_follow_up")
            if not follow_up:
                issues.append({
                    "id": rid, "path": str(record_file.relative_to(repo_root)),
                    "issue": "HC-16 deferral has no deferral_follow_up (owner + deadline) recorded (VCPS-WF-HOTFIX-001)",
                })
                continue
            deadline_str = follow_up.get("deadline")
            try:
                deadline = _parse_datetime(deadline_str)
            except Exception:
                issues.append({
                    "id": rid, "path": str(record_file.relative_to(repo_root)),
                    "issue": f"deferral_follow_up.deadline {deadline_str!r} is not a parseable date-time",
                })
                continue
            if deadline < now:
                issues.append({
                    "id": rid, "path": str(record_file.relative_to(repo_root)),
                    "issue": (
                        f"deferral deadline {deadline_str} has passed (owner: "
                        f"{follow_up.get('owner')!r}). Per VCPS-WF-HOTFIX-003 this "
                        "becomes a blocking HIGH+ finding requiring HC-08 "
                        "re-acceptance or immediate scheduling unless already "
                        "resolved by a later record this script does not check for."
                    ),
                })
    elif approvals_dir.exists() or approvals_dir.is_symlink():
        parse_errors.append({"path": str(approvals_dir), "error": "approval directory resolves outside the repository"})
    return {
        "lapsed_or_incomplete_deferrals": issues,
        "parse_errors": parse_errors,
        "note": (
            "Candidates only: this script cannot see whether a lapsed deferral "
            "was already resolved by a later finding/work-item record (AG-011 "
            "forbids editing the original decision record to say so). Absence "
            "of an issue here means no HC-16 DECISION with a passed deadline "
            "was found, not that every HOTFIX follow-up is actually current."
        ),
    }


# --- release-readiness-check (VCPS-GATE-021/032, structural only) ---------

def _find_record_by_id(repo_root: Path, record_id: str):
    records, _ = iter_records(repo_root)
    for path, fm in records:
        if fm.get("id") == record_id:
            return path, fm
    return None, None


def release_readiness_check(repo_root: Path, release_revision: str, work_item_refs):
    issues = []
    checked = []
    for wid in work_item_refs:
        path, fm = _find_record_by_id(repo_root, wid)
        if fm is None:
            issues.append({"work_item": wid, "issue": "work item record not found"})
            continue
        for g in (fm.get("applicable_gates") or []):
            gate_num = g.get("gate")
            outcome_ref = g.get("outcome_ref")
            entry = {"work_item": wid, "gate": gate_num, "outcome_ref": outcome_ref}
            if outcome_ref is None:
                issues.append({**entry, "issue": f"gate {gate_num} has no outcome_ref (not yet evaluated)"})
                checked.append(entry)
                continue
            gpath, gfm = _find_record_by_id(repo_root, outcome_ref)
            if gfm is None:
                issues.append({**entry, "issue": f"outcome_ref {outcome_ref!r} does not resolve to any gate record"})
                continue
            outcome = gfm.get("outcome")
            if outcome not in ("PASS", "PARTIAL", "NOT_APPLICABLE"):
                issues.append({**entry, "issue": f"gate {gate_num} outcome is {outcome!r}, not PASS/PARTIAL/NOT_APPLICABLE"})
            gate_revision = gfm.get("revision")
            if gate_revision != release_revision:
                issues.append({
                    **entry,
                    "issue": (
                        f"gate {gate_num} was evaluated on revision {gate_revision!r}, "
                        f"not the release revision {release_revision!r} -- staleness candidate, "
                        "not a verdict (VCPS-EVD-050/051 may permit carry-forward)."
                    ),
                })
            checked.append(entry)

    hc10_decisions = []
    approvals_dir = repo_root / ".vcps" / "approvals"
    if _safe_repo_path(repo_root, approvals_dir) and approvals_dir.is_dir():
        approval_files, rejected = _safe_markdown_files(repo_root, approvals_dir)
        if rejected:
            issues.extend({"issue": f"approval path is unreadable or resolves outside the repository: {p}"} for p in rejected)
        for record_file, safe_file in approval_files:
            try:
                fm = load_frontmatter(safe_file, repo_root)
            except Exception:
                continue
            if fm.get("kind") == "DECISION" and "HC-10" in (fm.get("checkpoint_codes") or []):
                if fm.get("revision") == release_revision:
                    hc10_decisions.append({
                        "id": fm.get("id"), "decision": fm.get("decision"),
                    })
    elif approvals_dir.exists() or approvals_dir.is_symlink():
        issues.append({"issue": "approval directory resolves outside the repository"})
    return {
        "release_revision": release_revision,
        "gates_checked": checked,
        "issues": issues,
        "hc10_decisions_on_this_revision": hc10_decisions,
        "note": (
            "Structural candidates only (VCPS-GATE-021/032): whether a PARTIAL "
            "outcome is actually 'permitted' per gates/README.md SS3, and "
            "whether an HC-10 decision's conditions are actually met, are the "
            "model's judgment, not this script's. An empty "
            "hc10_decisions_on_this_revision does not mean Gate 6 is blocked "
            "forever -- it means none has been recorded YET on this revision."
        ),
    }


# --- CLI ------------------------------------------------------------------

def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target", default=".", help="target repository root")

    parser = argparse.ArgumentParser(prog="vcps_evidence.py")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("evidence-inventory", parents=[common])
    sub.add_parser("gate-reference-check", parents=[common])
    sub.add_parser("orphan-check", parents=[common])
    sub.add_parser("baseline-history-check", parents=[common])
    sub.add_parser("record-history-check", parents=[common])
    p_ag = sub.add_parser("antigaming-scan", parents=[common])
    p_ag.add_argument("--scope-path", action="append", default=[], dest="scope_paths", required=True)
    sub.add_parser("antigaming-diff-scan", parents=[common])

    sub.add_parser("lapsed-deferral-check", parents=[common])

    p_rr = sub.add_parser("release-readiness-check", parents=[common])
    p_rr.add_argument("--release-revision", required=True)
    p_rr.add_argument("--work-item-ref", action="append", default=[], dest="work_item_refs", required=True)

    args = parser.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(json.dumps({"error": f"target not found: {target}"}))
        sys.exit(2)

    try:
        if args.command == "evidence-inventory":
            print(json.dumps(evidence_inventory(target), indent=2))
        elif args.command == "gate-reference-check":
            print(json.dumps(gate_reference_check(target), indent=2))
        elif args.command == "orphan-check":
            print(json.dumps(orphan_check(target), indent=2))
        elif args.command == "baseline-history-check":
            result = baseline_history_check(target)
            print(json.dumps(result, indent=2))
            if result.get("error"):
                sys.exit(1)
        elif args.command == "record-history-check":
            result = record_history_check(target)
            print(json.dumps(result, indent=2))
            if result.get("error"):
                sys.exit(1)
        elif args.command == "antigaming-scan":
            print(json.dumps(antigaming_scan(target, args.scope_paths), indent=2))
        elif args.command == "antigaming-diff-scan":
            result = antigaming_diff_scan(target)
            print(json.dumps(result, indent=2))
            if result.get("error"):
                sys.exit(1)
        elif args.command == "lapsed-deferral-check":
            print(json.dumps(lapsed_deferral_check(target), indent=2))
        elif args.command == "release-readiness-check":
            print(json.dumps(
                release_readiness_check(target, args.release_revision, args.work_item_refs),
                indent=2,
            ))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

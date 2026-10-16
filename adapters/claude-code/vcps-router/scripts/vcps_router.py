#!/usr/bin/env python3
"""VCPS Claude Code router helper.

Deterministic mechanical support for the /vcps skill: raw, mechanically
checkable facts that bear on intent classification and risk escalation
(workflows/README.md VCPS-WF-001/002, standard/risk-model.md
VCPS-RISK-041/045). This script makes no intent-classification, risk-class,
or workflow-dispatch judgment -- those stay with the model, per the same
split standard/VCPS.md VCPS-CORE-001 and workflows/setup.md VCPS-SETUP-067
establish for the /vcps-setup adapter's own helper. In particular, it
NEVER classifies a critical_domains entry as touched by name/keyword
match (standard/risk-model.md VCPS-RISK-002 explicitly forbids keyword-only
classification) -- domain-level impact tracing is the model's job. What
this script DOES check mechanically is VCPS-RISK-041's own, genuinely
mechanical rule: whether a path is listed in a registered critical
invariant's enforcement_path.

Every subcommand prints one JSON object to stdout and exits 0 on success.
A tool-level problem (bad args, repo not found, unparseable YAML) exits
nonzero with a JSON error object on stdout and a short message on stderr --
this is a tool failure, never a silent "no escalation needed".
"""

import argparse
import json
import os
import stat
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML not available"}))
    print("PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# --- Strict YAML (same contract as adapters/claude-code/vcps-setup/scripts/
# vcps_tool.py -- duplicated rather than imported across sibling skill
# directories, so either component remains independently installable per
# standard/portability.md's "no single agent's private memory or layout"
# spirit applied to adapter-internal layout too). -------------------------

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


def load_frontmatter(file_path: Path, repo_root: Path):
    text = read_repo_text(repo_root, file_path)
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValueError(f"{file_path}: missing YAML frontmatter opening '---'")
    rest = text[4:]
    marker = "\n---\n"
    idx = rest.find(marker)
    if idx == -1:
        if rest.rstrip("\n").endswith("\n---") or rest == "---":
            idx = len(rest.rstrip("\n")) - 3
        else:
            raise ValueError(f"{file_path}: missing YAML frontmatter closing '---'")
    fm_text = rest[:idx]
    frontmatter = strict_yaml_load(fm_text, path=str(file_path))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{file_path}: frontmatter is not a mapping")
    return frontmatter


def _safe_repo_path(repo_root: Path, candidate: Path):
    try:
        root = repo_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError):
        return None


def open_repo_file(repo_root: Path, candidate: Path):
    """Open a target file under descriptor-relative no-follow traversal."""
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


def read_repo_text(repo_root: Path, candidate: Path, encoding="utf-8") -> str:
    fd = open_repo_file(repo_root, candidate)
    with os.fdopen(fd, "rb") as stream:
        content = stream.read(MAX_TARGET_TEXT_BYTES + 1)
    if len(content) > MAX_TARGET_TEXT_BYTES:
        raise ValueError(f"target text exceeds {MAX_TARGET_TEXT_BYTES}-byte safety limit: {candidate}")
    return content.decode(encoding)


# --- Loading project state -------------------------------------------------

def load_project_config(repo_root: Path):
    vcps_dir = repo_root / ".vcps"
    config_path = vcps_dir / "project.yaml"
    safe_vcps = _safe_repo_path(repo_root, vcps_dir)
    if (vcps_dir.exists() or vcps_dir.is_symlink()) and (safe_vcps is None or not safe_vcps.is_dir()):
        raise ValueError(".vcps resolves outside the target repository")
    safe_config = _safe_repo_path(repo_root, config_path)
    if (config_path.exists() or config_path.is_symlink()) and safe_config is None:
        raise ValueError(".vcps/project.yaml resolves outside the target repository")
    if safe_config is None or not safe_config.is_file():
        return None
    return strict_yaml_load(read_repo_text(repo_root, safe_config), str(config_path))


def load_invariants(repo_root: Path):
    inv_path = repo_root / ".vcps" / "invariants.md"
    safe_inv = _safe_repo_path(repo_root, inv_path)
    if (inv_path.exists() or inv_path.is_symlink()) and safe_inv is None:
        raise ValueError(".vcps/invariants.md resolves outside the target repository")
    if safe_inv is None or not safe_inv.is_file():
        return []
    fm = load_frontmatter(safe_inv, repo_root)
    return fm.get("invariants") or []


def _path_touches(touched: str, enforcement: str) -> bool:
    """True if `touched` and `enforcement` are the same path, or one is a
    directory-prefix of the other (either an enforcement entry naming a
    directory, or a touched path naming a directory that contains an
    enforcement file) -- VCPS-RISK-041's 'any file ... in a critical
    invariant's enforcement path', applied without assuming either side
    is necessarily a leaf file."""
    t = touched.rstrip("/")
    e = enforcement.rstrip("/")
    if t == e:
        return True
    if t.startswith(e + "/"):
        return True
    if e.startswith(t + "/"):
        return True
    return False


# --- escalation-check (VCPS-RISK-041, mechanical half) ---------------------

def escalation_check(repo_root: Path, touched_paths):
    config = load_project_config(repo_root)
    if config is None:
        return {
            "has_vcps": False,
            "forced_r3": False,
            "matched_invariants": [],
            "note": "No .vcps/project.yaml found; no registered invariants to check against. This does NOT mean the change is safe -- it means there is nothing mechanical to check yet (run /vcps-setup first).",
        }
    applicable = set(config.get("applicable_invariants") or [])
    all_invariants = load_invariants(repo_root)
    matched = []
    for inv in all_invariants:
        if inv.get("id") not in applicable:
            continue
        if inv.get("status") == "WITHDRAWN":
            continue
        for ep in inv.get("enforcement_path") or []:
            for touched in touched_paths:
                if _path_touches(touched, ep):
                    matched.append({
                        "invariant_id": inv.get("id"),
                        "enforcement_path": ep,
                        "touched_path": touched,
                    })
    return {
        "has_vcps": True,
        "forced_r3": len(matched) > 0,
        "matched_invariants": matched,
        "note": "forced_r3 is a floor, never a judgment of the actual class: VCPS-RISK-041 requires R3 when any match exists, regardless of wording or diff size. The model MUST NOT lower this. Absence of a match does NOT mean R0/R1 -- it only means this mechanical check found nothing; domain-level impact tracing (VCPS-RISK-002) remains the model's job.",
    }


# --- project-context (raw facts only, no domain-match judgment) ------------

def project_context(repo_root: Path):
    config = load_project_config(repo_root)
    if config is None:
        return {"has_vcps": False}
    level = (config.get("level") or {}).get("value")
    critical_domains = config.get("critical_domains") or []
    return {
        "has_vcps": True,
        "level": level,
        "critical_domains": critical_domains,
        "note": "critical_domains is informative context for the model's own impact-path tracing (VCPS-RISK-001/002). Do not auto-escalate by matching a request's wording against a domain name or keyword -- that is exactly what VCPS-RISK-002 forbids.",
    }


# --- segmentation-scan (VCPS-RISK-045, raw overlap facts only) -------------

WORK_ITEM_DIRS = ["features", "reviews", "bugs", "releases", "work-items"]


def segmentation_scan(repo_root: Path, touched_paths):
    vcps_dir = repo_root / ".vcps"
    touched_set = set(touched_paths)
    overlaps = []
    safe_vcps = _safe_repo_path(repo_root, vcps_dir)
    if (vcps_dir.exists() or vcps_dir.is_symlink()) and (safe_vcps is None or not safe_vcps.is_dir()):
        raise ValueError(".vcps resolves outside the target repository")
    if safe_vcps is None or not safe_vcps.is_dir():
        return {"has_vcps": False, "overlapping_work_items": []}
    for sub in WORK_ITEM_DIRS:
        d = safe_vcps / sub
        safe_d = _safe_repo_path(repo_root, d)
        if (d.exists() or d.is_symlink()) and (safe_d is None or not safe_d.is_dir()):
            raise ValueError(f".vcps/{sub} resolves outside the target repository")
        if safe_d is None or not safe_d.is_dir():
            continue
        for record_file in sorted(safe_d.glob("*.md")):
            safe_record = _safe_repo_path(repo_root, record_file)
            if safe_record is None:
                raise ValueError(f"work-item record resolves outside the target repository: {record_file}")
            try:
                fm = load_frontmatter(safe_record, repo_root)
            except Exception:
                continue
            files = ((fm.get("scope") or {}).get("files")) or []
            overlapping_files = sorted(
                f for f in files
                if any(_path_touches(t, f) for t in touched_set)
            )
            if overlapping_files:
                overlaps.append({
                    "id": fm.get("id"),
                    "intent": fm.get("intent"),
                    "risk_class": fm.get("risk_class"),
                    "overlapping_files": overlapping_files,
                })
    return {
        "has_vcps": True,
        "overlapping_work_items": overlaps,
        "note": "Raw overlap facts only. Whether these form a 'same logical unit of work' whose combined effect governs classification (VCPS-RISK-045) is the model's judgment, not this script's -- it does not know branch/ticket lineage.",
    }


# --- CLI ---------------------------------------------------------------

def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target", default=".", help="target repository root")

    parser = argparse.ArgumentParser(prog="vcps_router.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ec = sub.add_parser("escalation-check", parents=[common])
    p_ec.add_argument("--touched-path", action="append", default=[], dest="touched_paths")

    sub.add_parser("project-context", parents=[common])

    p_ss = sub.add_parser("segmentation-scan", parents=[common])
    p_ss.add_argument("--touched-path", action="append", default=[], dest="touched_paths")

    args = parser.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(json.dumps({"error": f"target not found: {target}"}))
        sys.exit(2)

    try:
        if args.command == "escalation-check":
            print(json.dumps(escalation_check(target, args.touched_paths), indent=2))
        elif args.command == "project-context":
            print(json.dumps(project_context(target), indent=2))
        elif args.command == "segmentation-scan":
            print(json.dumps(segmentation_scan(target, args.touched_paths), indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

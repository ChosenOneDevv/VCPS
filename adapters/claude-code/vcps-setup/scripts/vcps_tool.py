#!/usr/bin/env python3
"""VCPS Claude Code adapter helper.

Deterministic mechanical support for the /vcps-setup skill: strict YAML
parsing, canonical-JSON hashing (plan hash, stage input fingerprint per
templates/validation.md), VCS-state inventory, mode detection, resume
status, and atomic file writes. This script makes no risk, classification,
or acceptance judgments — those belong to the model, per
standard/VCPS.md VCPS-CORE-001 (no agent-private feature becomes a Core
requirement) and workflows/setup.md VCPS-SETUP-067 ("the adapter cannot
upgrade a tier by assertion").

Every subcommand prints one JSON object to stdout and exits 0 on success.
A tool-level problem (bad args, repo not found, unparseable YAML) exits
nonzero with a JSON error object on stdout and a short message on stderr —
this is a tool failure, never a silent PASS/COMPLETE.
"""

import argparse
import datetime
import fnmatch
import hashlib
import json
import math
import os
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path, PureWindowsPath

try:
    import vcps_schema
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import vcps_schema

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML not available"}))
    print("PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

SUPPORTED_VCPS_VERSIONS = {"1.0.0", "0.1.0-draft"}
# "0.1.0-draft" is kept recognized (not AHEAD/BEHIND-REPAIR'd) alongside
# "1.0.0": the 1.0.0 cut changed no requirement content, only removed the
# pre-release label (SemVer explicitly does not require 1.0.0 to be
# backward-incompatible with a 0.y.z pre-release). An existing project
# still recording "0.1.0-draft" is correctly flagged vcps_version_relation
# BEHIND (it should update the label next time setup touches it) without
# being forced into a blocking REPAIR -- there is no actual migration to
# perform.
SUPPORTED_PROJECT_SCHEMA = "0.2.0"
MIGRATABLE_PROJECT_SCHEMA = {"0.1.0"}
SUPPORTED_LAYOUT_VERSION = "0.1.0"
PROJECT_SCHEMA_MIGRATION_BACKUP = ".vcps/project.yaml.0.1.0.bak"
PROJECT_SCHEMA_MIGRATION_METADATA = ".vcps/project.yaml.migration.json"

FINGERPRINT_EXCLUDED_FIELDS = {
    "installation.plan",
    "installation.plan_history",
    "installation.stage_events",
    "installation.history",
    "installation.stage",
    "installation.status",
}

ID_PREFIXES = {
    "FND", "EVD", "FEAT", "REV", "BUG", "REL", "WORK", "HND", "GATE",
    "HCR", "PREAUTH", "BLO",
}


# --- Strict YAML -------------------------------------------------------

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
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                None, None, "non-string key", key_node.start_mark
            )
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


def _forbid_implicit_timestamp(loader, node):
    raise yaml.constructor.ConstructorError(
        None, None,
        "implicit YAML timestamp objects are forbidden; quote RFC 3339 timestamp strings",
        node.start_mark,
    )


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_construct_mapping
)
StrictLoader.add_constructor("tag:yaml.org,2002:merge", _forbid("merge key (<<)"))
StrictLoader.add_constructor("tag:yaml.org,2002:timestamp", _forbid_implicit_timestamp)

# Reject multiple-document streams and custom tags by using safe_load_all
# and checking there is exactly one document with only known tags; PyYAML
# raises on genuinely unknown tags under SafeLoader already (no implicit
# Python object construction), so the main residual risks this guards
# against are duplicate keys and merge keys (both common real YAML 1.1
# parser gaps against the YAML 1.2 single-document, no-merge-key contract
# in templates/contract.md "Unknown fields and migrations").


class QuotedStr(str):
    """A string that strict_yaml_dump always emits single-quoted.
    templates/contract.md requires timestamps and versions to be quoted
    strings specifically -- an unquoted bare version like '1.0' would
    otherwise parse back as a YAML float, silently corrupting it. Only
    values deliberately wrapped in this type are quoted; ordinary str
    values (including mapping keys) keep plain, unquoted style so
    generated files still look like the rest of this project's YAML."""


class _QuotedStringDumper(yaml.SafeDumper):
    pass


_QuotedStringDumper.add_representer(
    QuotedStr,
    lambda dumper, value: dumper.represent_scalar(
        "tag:yaml.org,2002:str", str(value), style="'"
    ),
)


def strict_yaml_dump(obj):
    return yaml.dump(
        obj, Dumper=_QuotedStringDumper, sort_keys=False,
        allow_unicode=True, default_flow_style=False,
    )


def strict_yaml_load(text, path="<stream>"):
    docs = list(yaml.load_all(text, Loader=StrictLoader))
    if len(docs) != 1:
        raise ValueError(f"{path}: expected exactly one YAML document, got {len(docs)}")
    document = docs[0]

    def reject_nonfinite(value, location="$", seen=None):
        if seen is None:
            seen = set()
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{path}: non-finite number at {location} is not valid JSON data")
        if isinstance(value, (dict, list)):
            identity = id(value)
            if identity in seen:
                return
            seen.add(identity)
            if isinstance(value, dict):
                for key, child in value.items():
                    reject_nonfinite(child, f"{location}.{key}", seen)
            else:
                for index, child in enumerate(value):
                    reject_nonfinite(child, f"{location}[{index}]", seen)

    reject_nonfinite(document)
    return document


def load_frontmatter(file_path, repo_root):
    """Markdown file: exactly one YAML frontmatter document, then body."""
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
    body = rest[idx + len(marker) :] if idx + len(marker) <= len(rest) else ""
    frontmatter = strict_yaml_load(fm_text, path=str(file_path))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{file_path}: frontmatter is not a mapping")
    return frontmatter, body


def _safe_target_path(repo_root: Path, path: Path):
    """Return the resolved path only when it remains in the target repo."""
    try:
        root = repo_root.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError):
        return None


# --- Canonical JSON / hashing ------------------------------------------

def canonical_json(obj):
    """UTF-8 canonical JSON: sorted keys, compact separators, unescaped
    non-ASCII, per templates/contract.md VCPS-SETUP-052 and
    templates/validation.md item 13."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan_hash(plan_obj: dict) -> str:
    """SHA-256 of canonical JSON of the plan object excluding 'sha256'."""
    stripped = {k: v for k, v in plan_obj.items() if k != "sha256"}
    return sha256_hex(canonical_json(stripped))


# --- Git state -----------------------------------------------------------

def run_git(repo_root, args, check=True):
    result = subprocess.run(
        # `git status` may execute a repository-local core.fsmonitor command.
        # The target repository is untrusted input to these read-only helpers;
        # disable that hook at command scope so local config cannot run code.
        ["git", "-C", str(repo_root), "-c", "core.fsmonitor=false"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def has_git(repo_root) -> bool:
    try:
        run_git(repo_root, ["rev-parse", "--is-inside-work-tree"])
        return True
    except Exception:
        return False


def git_status_porcelain(repo_root):
    """Returns list of {path, index_status, worktree_status, vcs} from
    `git status --porcelain=v1` plus untracked files, in the XY-code shape
    templates/validation.md item 14 expects for the 'vcs' field."""
    out = run_git(repo_root, ["status", "--porcelain=v1", "--untracked-files=all"])
    entries = []
    for line in out.splitlines():
        if not line:
            continue
        xy = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append({"path": path, "vcs": xy})
    return entries


def git_tracked_files(repo_root):
    out = run_git(repo_root, ["ls-files"])
    return [p for p in out.splitlines() if p]


def git_ignored_files(repo_root):
    """Repository-relative paths git considers ignored (gitignore'd),
    including inside otherwise-untracked directories. `git status
    --porcelain` alone never reports these (git omits ignored paths from
    plain status output), so expand_scope's '!!' exclusion silently never
    fired without this — e.g. a self-contained skill installation's own
    regenerated __pycache__/*.pyc churned every directory-scoped
    fingerprint on every invocation. `--others` only (no `--cached`/`-c`)
    keeps this read-only and untracked-scoped, matching what expand_scope
    needs."""
    out = run_git(
        repo_root,
        ["status", "--porcelain=v1", "--ignored=matching", "--untracked-files=all"],
    )
    paths = []
    for line in out.splitlines():
        if not line.startswith("!! "):
            continue
        paths.append(line[3:])
    return paths


# --- Stage input fingerprint (templates/validation.md item 14) ---------

def file_digest(repo_root: Path, path: Path) -> str:
    h = hashlib.sha256()
    fd = open_repo_file(repo_root, path)
    with os.fdopen(fd, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_path(repo_root: Path, rel_path: str, vcs_map: dict):
    full = repo_root / rel_path
    if full.is_symlink():
        target = os.readlink(full)
        digest = sha256_hex(target.encode("utf-8"))
        return {"path": rel_path, "exists": True, "type": "symlink", "digest": digest,
                "vcs": vcs_map.get(rel_path, "  ")}
    if not full.exists():
        return {"path": rel_path, "exists": False, "type": "absent", "digest": None,
                "vcs": vcs_map.get(rel_path, "NA")}
    if full.is_file():
        return {"path": rel_path, "exists": True, "type": "file",
                "digest": file_digest(repo_root, full), "vcs": vcs_map.get(rel_path, "  ")}
    return {"path": rel_path, "exists": True, "type": "submodule", "digest": None,
            "vcs": vcs_map.get(rel_path, "  ")}


def _validate_scope_item(scope_item: str) -> None:
    """Fail closed on anything that could escape the repository boundary
    lexically, before any filesystem check. Absolute paths and '..'
    segments are rejected outright per templates/validation.md item 2
    ("Reject absolute paths, path traversal, symlinks escaping the
    repository")."""
    if os.path.isabs(scope_item):
        raise ValueError(
            f"input_scope path must be repository-relative, not absolute: {scope_item!r}"
        )
    if any(part == ".." for part in Path(scope_item).parts):
        raise ValueError(
            f"input_scope path must not contain '..': {scope_item!r}"
        )


def _first_symlink_boundary(repo_root: Path, rel_path: str):
    """Walk rel_path's components under repo_root one at a time. Return the
    repository-relative path up to and including the first component that
    is itself a symlink (directory or file), or None if no component along
    the way is a symlink. This is the single choke point that prevents
    fingerprinting from ever dereferencing *through* a symlink to reach
    content outside the repository boundary (or a different part of it) —
    the symlink itself becomes the fingerprinted entry; whatever it points
    to is never opened, walked, or hashed by content, per 'Never
    dereference external content merely to compute a repository
    fingerprint unless the canonical specification explicitly requires
    it.'"""
    built = []
    cur = repo_root
    for part in Path(rel_path).parts:
        cur = cur / part
        built.append(part)
        if cur.is_symlink():
            return "/".join(built)
    return None


def expand_scope(repo_root: Path, input_scope, use_git: bool):
    """Expand input_scope paths; directories expand recursively (tracked
    + untracked non-ignored files, never .git/), excluding .vcps/ unless
    explicitly listed. A symlink anywhere along a path — whether the scope
    item itself, an intermediate directory component, or a subdirectory
    discovered during recursive expansion — is recorded as its own entry
    (by its target string, not its content) and is never followed into."""
    vcs_map = {}
    ignored_dirs = set()
    ignored_files = set()
    if use_git:
        for e in git_status_porcelain(repo_root):
            vcs_map[e["path"]] = e["vcs"]
        for p in git_tracked_files(repo_root):
            vcs_map.setdefault(p, "  ")
        for p in git_ignored_files(repo_root):
            if p.endswith("/"):
                ignored_dirs.add(p[:-1])
            else:
                ignored_files.add(p)
                vcs_map.setdefault(p, "!!")

    explicit_vcps = any(
        s == ".vcps" or s.startswith(".vcps/") for s in input_scope
    )
    paths = set()
    for scope_item in input_scope:
        _validate_scope_item(scope_item)
        boundary = _first_symlink_boundary(repo_root, scope_item)
        if boundary is not None:
            # The scope item is, or passes through, a symlink. Record the
            # symlink boundary itself and stop — do not resolve further,
            # even if the caller named a deeper path inside it.
            paths.add(boundary)
            continue
        full = repo_root / scope_item
        if full.is_dir():
            for root, dirs, files in os.walk(full, followlinks=False):
                if ".git" in dirs:
                    dirs.remove(".git")
                rel_root = Path(root).relative_to(repo_root)
                if not explicit_vcps:
                    if rel_root == Path(".vcps") or str(rel_root).startswith(".vcps/") or str(rel_root) == ".vcps":
                        dirs[:] = []
                        continue
                # Symlinked subdirectories must never be silently dropped
                # (os.walk's followlinks=False stops descent but still
                # returns them in `dirs`): record each as its own entry
                # and exclude it from further descent.
                kept_dirs = []
                for dname in dirs:
                    drel = str((rel_root / dname).as_posix())
                    if (repo_root / drel).is_symlink():
                        if use_git and vcs_map.get(drel, "  ") == "!!" and drel not in input_scope:
                            continue
                        if drel.startswith(".vcps/") and not explicit_vcps:
                            continue
                        paths.add(drel)
                        continue
                    if use_git and drel in ignored_dirs and drel not in input_scope:
                        # A gitignored directory (e.g. a regenerated
                        # __pycache__/ next to a self-contained skill
                        # installation's scripts/) is invisible to the
                        # fingerprint and never descended into — matching
                        # the untracked-ignored file exclusion below. `git
                        # status` reports an ignored directory as a single
                        # entry, never expanded per-file, so this must be
                        # checked here (not in the per-file loop).
                        continue
                    kept_dirs.append(dname)
                dirs[:] = kept_dirs
                for fname in files:
                    rel = str((rel_root / fname).as_posix())
                    if rel.startswith(".vcps/") and not explicit_vcps:
                        continue
                    if use_git and vcs_map.get(rel, "  ") == "!!" and rel not in input_scope:
                        continue
                    if use_git and rel in ignored_files and rel not in input_scope:
                        continue
                    paths.add(rel)
        else:
            paths.add(scope_item)
    return sorted(paths, key=lambda s: s.encode("utf-8")), vcs_map


def compute_fingerprint(repo_root: Path, input_scope, use_git: bool):
    paths, vcs_map = expand_scope(repo_root, input_scope, use_git)
    entries = [classify_path(repo_root, p, vcs_map) for p in paths]
    return {
        "fingerprint": sha256_hex(canonical_json(entries)),
        "entries": entries,
    }


# --- Mode detection (VCPS-SETUP-001/050) --------------------------------

def detect_mode(repo_root: Path, core_root: Path):
    vcps_dir = repo_root / ".vcps"
    config_path = vcps_dir / "project.yaml"
    vcps_md_root = repo_root / "VCPS.md"

    result = {
        "target": str(repo_root),
        "has_vcps_dir": vcps_dir.is_dir(),
        "has_config": config_path.is_file(),
        "config_parseable": None,
        # "route" is MODE_SELECTION, RESUME, or ALREADY_COMPLETE.
        # "mode" is populated ONLY for route == MODE_SELECTION and is one
        # of exactly NEW / ADOPT / UPGRADE / REPAIR (VCPS-SETUP-001). A
        # resumed or already-complete installation is NOT a fifth mode —
        # VCPS-SETUP-003 is explicit that resume happens "without
        # re-entering mode selection" — so it must never be placed in the
        # "mode" field, which earlier versions of this tool incorrectly did.
        "route": "MODE_SELECTION",
        "mode": None,
        "reasons": [],
        "vcps_version_relation": None,
        "project_schema_relation": None,
    }

    vcps_present = vcps_dir.exists() or vcps_dir.is_symlink()
    config_present = config_path.exists() or config_path.is_symlink()
    safe_vcps_dir = _safe_target_path(repo_root, vcps_dir) if vcps_present else None
    if vcps_present and (safe_vcps_dir is None or not safe_vcps_dir.is_dir()):
        result["mode"] = "REPAIR"
        result["reasons"].append(".vcps resolves outside the target repository; refusing to read it.")
        return result
    safe_config = _safe_target_path(repo_root, config_path) if config_present else None
    if config_present and safe_config is None:
        result["mode"] = "REPAIR"
        result["reasons"].append(".vcps/project.yaml resolves outside the target repository; refusing to read it.")
        return result

    core_version = None
    core_version_path = core_root / "VERSION"
    if core_version_path.is_file():
        core_version = read_repo_text(core_root, core_version_path).strip()

    if not result["has_vcps_dir"] or not result["has_config"]:
        has_app_signal = any(
            (repo_root / name).exists()
            for name in (
                "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
                "pom.xml", "build.gradle", "Gemfile", "composer.json",
                "requirements.txt", "src", "app", "lib",
            )
        )
        has_ci_signal = any(
            (repo_root / name).exists()
            for name in (".github", ".gitlab-ci.yml", ".circleci", "Jenkinsfile")
        )
        if has_app_signal or has_ci_signal:
            result["mode"] = "ADOPT"
            result["reasons"].append(
                "No canonical .vcps/ root/config, but application/CI signals present."
            )
        else:
            result["mode"] = "NEW"
            result["reasons"].append(
                "No canonical .vcps/ root/config and no application/CI signals found."
            )
        return result

    try:
        config = strict_yaml_load(read_repo_text(repo_root, safe_config), str(config_path))
        result["config_parseable"] = True
    except Exception as exc:
        result["config_parseable"] = False
        result["mode"] = "REPAIR"
        result["reasons"].append(f"Config exists but is not parseable: {exc}")
        return result

    if not isinstance(config, dict):
        result["config_parseable"] = False
        result["mode"] = "REPAIR"
        result["reasons"].append("Config root is not a mapping.")
        return result

    vcps_version = config.get("vcps_version")
    schema_version = config.get("schema_version")
    layout_version = config.get("artifact_layout_version")

    missing = [
        k for k, v in (
            ("vcps_version", vcps_version),
            ("schema_version", schema_version),
            ("artifact_layout_version", layout_version),
        )
        if v is None
    ]
    if missing:
        result["mode"] = "REPAIR"
        result["reasons"].append(f"Config missing required version field(s): {missing}")
        return result

    if layout_version != SUPPORTED_LAYOUT_VERSION:
        result["mode"] = "REPAIR"
        result["reasons"].append(
            f"Unsupported artifact_layout_version {layout_version!r} "
            f"(supported: {SUPPORTED_LAYOUT_VERSION!r}); read-only diagnosis."
        )
        return result

    if core_version and vcps_version not in SUPPORTED_VCPS_VERSIONS:
        if vcps_version and _looks_newer(vcps_version, core_version):
            result["vcps_version_relation"] = "AHEAD"
            result["mode"] = "REPAIR"
            result["reasons"].append(
                "Project vcps_version is AHEAD of this executor; read-only REPAIR "
                "diagnosis per VCPS-SETUP-002, no downgrade."
            )
        else:
            result["vcps_version_relation"] = "BEHIND"
            result["mode"] = "REPAIR"
            result["reasons"].append(
                f"Project vcps_version {vcps_version!r} has no defined migration in "
                "this draft; read-only diagnosis."
            )
        return result
    elif core_version:
        result["vcps_version_relation"] = "EQUAL" if vcps_version == core_version else "BEHIND"

    if schema_version == SUPPORTED_PROJECT_SCHEMA:
        result["project_schema_relation"] = "EQUAL"
    elif schema_version in MIGRATABLE_PROJECT_SCHEMA:
        result["project_schema_relation"] = "BEHIND"
        result["mode"] = "UPGRADE"
        result["reasons"].append(
            f"project schema {schema_version!r} -> {SUPPORTED_PROJECT_SCHEMA!r} "
            "migration available."
        )
        return result
    else:
        result["project_schema_relation"] = "UNSUPPORTED"
        result["mode"] = "REPAIR"
        result["reasons"].append(
            f"Unsupported project schema_version {schema_version!r}; read-only diagnosis."
        )
        return result

    installation = config.get("installation") or {}
    status = installation.get("status")
    stage = installation.get("stage")
    if status in ("PARTIAL", "BLOCKED"):
        result["route"] = "RESUME"
        result["reasons"].append(
            f"Consistent config at status {status!r}, stage {stage!r}: resume directly "
            "per VCPS-SETUP-003, not a fresh mode selection. mode is intentionally "
            "left null — resume is not a fifth mode."
        )
        return result
    if status == "COMPLETE":
        result["route"] = "ALREADY_COMPLETE"
        result["reasons"].append(
            "Config is COMPLETE; route to Stage-11-equivalent consistency check "
            "per VCPS-SETUP-004, do not create a fresh baseline. mode is "
            "intentionally left null — this is not a fifth mode."
        )
        return result

    result["mode"] = "REPAIR"
    result["reasons"].append(
        f"Config consistent but installation.status {status!r} is not a recognized "
        "value; diagnose before proceeding."
    )
    return result


def _looks_newer(a: str, b: str) -> bool:
    def key(v):
        core = v.split("-")[0]
        return tuple(int(x) if x.isdigit() else x for x in core.split("."))

    try:
        return key(a) > key(b)
    except Exception:
        return False


# --- Resume status -------------------------------------------------------

STAGE_NAMES = {
    1: "Repository discovery", 2: "Stack/toolchain discovery",
    3: "Risk classification", 4: "VCPS scaffold",
    5: "Dirty-tree/legacy classification", 6: "Baseline verification",
    7: "Locally actionable remediation", 8: "Baseline establishment",
    9: "Legacy evidence-gap registry", 10: "CI quality-gate alignment",
    11: "VCPS system audit",
}


def resume_status(repo_root: Path, use_git: bool = True):
    config_path = repo_root / ".vcps" / "project.yaml"
    safe_config = _safe_target_path(repo_root, config_path)
    if safe_config is None or not safe_config.is_file():
        return {"error": "no .vcps/project.yaml found", "resumable": False}
    config = strict_yaml_load(read_repo_text(repo_root, safe_config), str(config_path))
    installation = (config or {}).get("installation") or {}
    events = installation.get("stage_events") or []

    completed_events = {}  # stage -> most recent COMPLETED event
    blocked_stages = {}
    invalidated = set()
    for ev in events:
        stage = ev.get("stage")
        state = ev.get("event_state") or ev.get("state")
        if state == "COMPLETED":
            completed_events[stage] = ev
            invalidated.discard(stage)
        elif state == "BLOCKED":
            blocked_stages[stage] = ev.get("reason")
            completed_events.pop(stage, None)
        elif state == "INVALIDATED":
            invalidated.add(stage)
            completed_events.pop(stage, None)

    # VCPS-SETUP-054: recompute each completed stage's input fingerprint
    # now and compare against what was recorded. A completed stage whose
    # recorded input has changed since is stale and must be re-evaluated,
    # not trusted — recording "COMPLETED" once is not a permanent pass.
    stale_stages = {}
    for stage, ev in completed_events.items():
        recorded_fp = ev.get("input_fingerprint")
        input_scope = ev.get("input_scope")
        if not recorded_fp or not input_scope:
            continue
        try:
            current = compute_fingerprint(repo_root, input_scope, use_git)
            if current["fingerprint"] != recorded_fp:
                stale_stages[stage] = {
                    "recorded_fingerprint": recorded_fp,
                    "current_fingerprint": current["fingerprint"],
                }
        except Exception as exc:
            stale_stages[stage] = {"error": f"could not recompute fingerprint: {exc}"}

    completed = {s for s in completed_events if s not in stale_stages}

    earliest_incomplete = None
    for n in range(1, 12):
        if n not in completed:
            earliest_incomplete = n
            break

    orphaned_outputs = []
    planned_paths = (installation.get("plan") or {}).get("create_paths", []) if installation.get("plan") else []
    for rel in planned_paths:
        full = repo_root / rel
        if not full.exists():
            orphaned_outputs.append({"path": rel, "issue": "planned but missing"})
        elif full.is_file() and full.stat().st_size == 0:
            orphaned_outputs.append({"path": rel, "issue": "present but empty/truncated"})

    return {
        "resumable": True,
        "declared_stage": installation.get("stage"),
        "declared_status": installation.get("status"),
        "earliest_incomplete_stage": earliest_incomplete,
        "earliest_incomplete_stage_name": STAGE_NAMES.get(earliest_incomplete),
        "completed_stages": sorted(completed),
        "invalidated_stages": sorted(invalidated),
        "stale_stages": stale_stages,
        "blocked_stages": blocked_stages,
        "orphaned_outputs": orphaned_outputs,
        "active_plan_hash": (installation.get("plan") or {}).get("sha256")
        if installation.get("plan") else None,
    }


# --- Inventory (Stage 1-2 read-only facts) -------------------------------

MANIFEST_SIGNALS = {
    "package.json": "node", "pyproject.toml": "python", "requirements.txt": "python",
    "Cargo.toml": "rust", "go.mod": "go", "pom.xml": "java-maven",
    "build.gradle": "java-gradle", "Gemfile": "ruby", "composer.json": "php",
}
CI_SIGNALS = {
    ".github/workflows": "github-actions", ".gitlab-ci.yml": "gitlab-ci",
    ".circleci": "circleci", "Jenkinsfile": "jenkins", ".travis.yml": "travis",
}


def inventory(repo_root: Path):
    git_present = has_git(repo_root)
    manifests = {
        name: True for name in MANIFEST_SIGNALS if (repo_root / name).exists()
    }
    ci = {name: True for name in CI_SIGNALS if (repo_root / name).exists()}

    dirty = []
    if git_present:
        for e in git_status_porcelain(repo_root):
            dirty.append(e)

    revision = None
    if git_present:
        try:
            revision = run_git(repo_root, ["rev-parse", "HEAD"]).strip()
        except Exception:
            revision = None

    return {
        "target": str(repo_root),
        "vcs": "git" if git_present else "NONE",
        "revision": revision,
        "manifest_signals": manifests,
        "ci_signals": ci,
        "dirty_tree_entries": dirty,
        "note": "Raw facts only. Impact tracing, risk classification, and "
                "dirty-item ownership are model judgment per "
                "standard/risk-model.md and workflows/setup.md Stage 5 — "
                "this tool does not make those calls.",
    }


# --- Atomic write ----------------------------------------------------

MAX_TARGET_TEXT_BYTES = 1024 * 1024

def _open_directory_chain(repo_root: Path, parts, create_missing=False):
    """Open a directory beneath repo_root without following path symlinks.

    Every component is opened relative to the already-open parent directory.
    This keeps a concurrent symlink substitution from retargeting a later
    temporary-file or rename operation outside the repository.
    """
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if os.name != "posix" or any(not hasattr(os, name) for name in required):
        raise OSError("secure repository traversal requires POSIX O_DIRECTORY/O_NOFOLLOW support")
    if os.open not in os.supports_dir_fd:
        raise OSError("secure repository traversal requires directory-relative open support")
    if create_missing and os.mkdir not in os.supports_dir_fd:
        raise OSError("secure atomic-write requires directory-relative mkdir support")

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    resolved_root = repo_root.resolve(strict=True)
    current_fd = os.open(os.sep, flags)
    try:
        for component in resolved_root.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd

        for component in parts:
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except FileNotFoundError:
                if not create_missing:
                    raise
                try:
                    os.mkdir(component, 0o755, dir_fd=current_fd)
                except FileExistsError:
                    # Another creator won the race; the no-follow open below
                    # still validates what now occupies this component.
                    pass
                next_fd = os.open(component, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def open_repo_file(repo_root: Path, candidate: Path):
    """Open a regular file below repo_root without following any symlink.

    Directory descriptors anchor each lookup, closing the resolve-then-open
    race for target-controlled paths. The caller owns the returned fd.
    """
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
    parent_fd = _open_directory_chain(root, relative.parts[:-1])
    file_fd = None
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        file_fd = os.open(relative.name, flags, dir_fd=parent_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise OSError("target path is not a regular file")
        result = file_fd
        file_fd = None
        return result
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(parent_fd)


def read_repo_bytes(repo_root: Path, candidate: Path) -> bytes:
    fd = open_repo_file(repo_root, candidate)
    with os.fdopen(fd, "rb") as stream:
        content = stream.read(MAX_TARGET_TEXT_BYTES + 1)
    if len(content) > MAX_TARGET_TEXT_BYTES:
        raise ValueError(f"target text exceeds {MAX_TARGET_TEXT_BYTES}-byte safety limit: {candidate}")
    return content


def read_repo_text(repo_root: Path, candidate: Path, encoding="utf-8") -> str:
    return read_repo_bytes(repo_root, candidate).decode(encoding)


def atomic_write(repo_root: Path, rel_path: str, content: str):
    relative = Path(rel_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.name in ("", ".", ".."):
        raise ValueError("atomic-write path must be repository-relative and contain no '..'")
    root = repo_root.resolve(strict=True)
    parent_fd = _open_directory_chain(root, relative.parts[:-1], create_missing=True)
    temporary_name = f".vcps_tmp_{secrets.token_hex(16)}"
    file_fd = None
    try:
        file_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_fd,
        )
        with os.fdopen(file_fd, "wb") as stream:
            file_fd = None
            payload = content.encode("utf-8")
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Directory-relative replacement remains anchored to the verified
        # parent descriptor even if its pathname is concurrently swapped.
        os.replace(
            temporary_name,
            relative.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.fsync(parent_fd)
    except Exception:
        if file_fd is not None:
            os.close(file_fd)
        try:
            os.unlink(temporary_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(parent_fd)
    return {"written": str(root / relative), "bytes": len(payload)}


# --- Project schema migration (templates/contract.md "Unknown fields and
# migrations") -----------------------------------------------------------

def migrate_project_schema(repo_root: Path):
    """Mechanically migrate .vcps/project.yaml from the sole migratable
    predecessor schema (0.1.0) to the current write target (0.2.0), per
    templates/contract.md: adds installation.plan: null, plan_history: [],
    and stage_events: []; sets installation.status to PARTIAL (nothing
    satisfies COMPLETE with an empty stage journal); records a
    config_history migration event; preserves every other field verbatim,
    including all existing record IDs and observations. This performs the
    schema edit only -- it never fabricates historical stage_events, and
    does not itself run the read-only dry-run / fingerprint reconstruction
    the contract describes as following it (that is Stage 1-3 of a real
    subsequent `/vcps-setup` UPGRADE run, a model-driven process this
    mechanical helper does not perform). Round-tripping through PyYAML
    does not preserve the original file's comments or key ordering; any
    human-authored header comment is lost, which is why the migration
    event's reason records exactly what changed."""
    vcps_dir = repo_root / ".vcps"
    config_path = vcps_dir / "project.yaml"
    safe_config = _safe_target_path(repo_root, config_path)
    if safe_config is None or not safe_config.is_file():
        raise ValueError("no .vcps/project.yaml found")

    original_bytes = read_repo_bytes(repo_root, safe_config)
    config = strict_yaml_load(original_bytes.decode("utf-8"), str(config_path))
    if not isinstance(config, dict):
        raise ValueError("project.yaml is not a mapping")

    schema_version = config.get("schema_version")
    if schema_version == SUPPORTED_PROJECT_SCHEMA:
        return {"migrated": False, "reason": f"already at schema_version {SUPPORTED_PROJECT_SCHEMA!r}"}
    if schema_version not in MIGRATABLE_PROJECT_SCHEMA:
        raise ValueError(
            f"schema_version {schema_version!r} has no defined migration to "
            f"{SUPPORTED_PROJECT_SCHEMA!r}; read-only REPAIR diagnosis applies "
            "(VCPS-SETUP-050), this tool will not guess one"
        )

    installation = config.get("installation")
    if not isinstance(installation, dict):
        raise ValueError("project.yaml.installation is missing or not a mapping; cannot migrate")
    if any(k in installation for k in ("plan", "plan_history", "stage_events")):
        raise ValueError(
            "project.yaml.installation already has plan/plan_history/stage_events; "
            "refusing to overwrite -- this does not look like a genuine "
            f"{schema_version} record"
        )

    from_schema = schema_version
    config["schema_version"] = QuotedStr(SUPPORTED_PROJECT_SCHEMA)
    if "artifact_layout_version" in config:
        config["artifact_layout_version"] = QuotedStr(config["artifact_layout_version"])
    if "vcps_version" in config:
        config["vcps_version"] = QuotedStr(config["vcps_version"])
    installation["plan"] = None
    installation["plan_history"] = []
    installation["stage_events"] = []
    installation["stage"] = 1
    installation["status"] = "PARTIAL"

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history_entry = {
        "timestamp": QuotedStr(timestamp),
        "event": "project schema migration",
        "from": f"schema_version {from_schema}",
        "to": f"schema_version {SUPPORTED_PROJECT_SCHEMA}",
        "reason": (
            "Mechanical migration via vcps_tool.py migrate-project-schema per "
            "templates/contract.md 'Unknown fields and migrations': added "
            "installation.plan=null, plan_history=[], stage_events=[]; status "
            "set to PARTIAL pending a real UPGRADE setup run to reconstruct "
            "stage completion from existing artifacts and fresh fingerprints. "
            "No historical stage event was fabricated."
        ),
    }
    config.setdefault("config_history", []).append(history_entry)

    new_text = strict_yaml_dump(config)
    original_digest = sha256_hex(original_bytes)
    migrated_digest = sha256_hex(new_text.encode("utf-8"))
    backup_path = repo_root / PROJECT_SCHEMA_MIGRATION_BACKUP
    safe_backup = _safe_target_path(repo_root, backup_path)
    if safe_backup is not None:
        if not safe_backup.is_file() or safe_backup.read_bytes() != original_bytes:
            raise ValueError(f"migration backup already exists and differs: {PROJECT_SCHEMA_MIGRATION_BACKUP}")
    else:
        if backup_path.exists() or backup_path.is_symlink():
            raise ValueError(f"migration backup path is unsafe: {PROJECT_SCHEMA_MIGRATION_BACKUP}")
        atomic_write(repo_root, PROJECT_SCHEMA_MIGRATION_BACKUP, original_bytes.decode("utf-8"))

    metadata = {
        "format": 1,
        "from_schema": from_schema,
        "to_schema": SUPPORTED_PROJECT_SCHEMA,
        "backup_path": PROJECT_SCHEMA_MIGRATION_BACKUP,
        "original_sha256": original_digest,
        "migrated_sha256": migrated_digest,
    }
    metadata_path = repo_root / PROJECT_SCHEMA_MIGRATION_METADATA
    safe_metadata = _safe_target_path(repo_root, metadata_path)
    if safe_metadata is not None:
        existing_metadata = json.loads(safe_metadata.read_text(encoding="utf-8"))
        if existing_metadata != metadata and sha256_hex(original_bytes) != existing_metadata.get("original_sha256"):
            raise ValueError(f"migration metadata conflicts with this source file: {PROJECT_SCHEMA_MIGRATION_METADATA}")
    elif metadata_path.exists() or metadata_path.is_symlink():
        raise ValueError(f"migration metadata path is unsafe: {PROJECT_SCHEMA_MIGRATION_METADATA}")
    atomic_write(repo_root, PROJECT_SCHEMA_MIGRATION_METADATA,
                 json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    write_result = atomic_write(repo_root, str(safe_config.relative_to(repo_root)), new_text)
    return {
        "migrated": True,
        "from_schema": from_schema,
        "to_schema": SUPPORTED_PROJECT_SCHEMA,
        "backup": PROJECT_SCHEMA_MIGRATION_BACKUP,
        "write_result": write_result,
    }


def rollback_project_schema(repo_root: Path):
    """Restore the exact pre-migration config only while it remains untouched."""
    config_path = repo_root / ".vcps/project.yaml"
    backup_path = repo_root / PROJECT_SCHEMA_MIGRATION_BACKUP
    metadata_path = repo_root / PROJECT_SCHEMA_MIGRATION_METADATA
    safe_config = _safe_target_path(repo_root, config_path)
    safe_backup = _safe_target_path(repo_root, backup_path)
    safe_metadata = _safe_target_path(repo_root, metadata_path)
    if not all(path is not None and path.is_file() for path in (safe_config, safe_backup, safe_metadata)):
        raise ValueError("migration rollback requires a safe config, backup, and migration metadata")
    metadata = json.loads(safe_metadata.read_text(encoding="utf-8"))
    current_bytes = safe_config.read_bytes()
    backup_bytes = safe_backup.read_bytes()
    if metadata.get("format") != 1 or metadata.get("backup_path") != PROJECT_SCHEMA_MIGRATION_BACKUP:
        raise ValueError("unsupported or malformed project-schema migration metadata")
    if sha256_hex(current_bytes) != metadata.get("migrated_sha256"):
        raise ValueError("project.yaml changed after migration; refusing automatic rollback")
    if sha256_hex(backup_bytes) != metadata.get("original_sha256"):
        raise ValueError("migration backup digest mismatch; refusing rollback")
    current = strict_yaml_load(current_bytes.decode("utf-8"), str(config_path))
    original = strict_yaml_load(backup_bytes.decode("utf-8"), str(backup_path))
    if (current.get("schema_version") != metadata.get("to_schema")
            or original.get("schema_version") != metadata.get("from_schema")):
        raise ValueError("migration schema versions do not match rollback metadata")
    result = atomic_write(repo_root, ".vcps/project.yaml", backup_bytes.decode("utf-8"))
    return {"rolled_back": True, "restored_schema": original.get("schema_version"),
            "backup": PROJECT_SCHEMA_MIGRATION_BACKUP, "write_result": result}


# --- Minimal structural validation (templates/validation.md) -----------

# templates/validation.md item 11 ("Reject secret-like keys/values,
# credentials, unredacted personal data, machine-specific absolute paths").
# Heuristics only -- flag for human review, never a proof of absence.
SECRET_KEY_RE = re.compile(r"(secret|password|passwd|api[_-]?key|credential|private[_-]?key)", re.I)
SECRET_VALUE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id shape
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}"),
]
MACHINE_PATH_RE = re.compile(r"^(/home/[^/]+/|/Users/[^/]+/|[A-Za-z]:\\Users\\)")
CREDENTIALED_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/@\s]+:[^/@\s]+@")

# templates/validation.md item 3: expected ID-prefix family for commonly
# named reference fields. A field name not listed here is not checked
# (unknown field names are not assumed to be references at all).
REF_FIELD_PREFIXES = {
    "evidence_refs": {"EVD"},
    "finding_refs": {"FND"},
    "gate_refs": {"GATE"},
    "outcome_ref": {"GATE"},
    "gate6_ref": {"GATE"},
    "checkpoint_refs": {"HCR", "PREAUTH"},
    "approval_refs": {"HCR", "PREAUTH"},
    "decision_ref": {"HCR"},
    "risk_acceptance_ref": {"HCR"},
    "lowering_approval_ref": {"HCR"},
    "approval_ref": {"HCR", "PREAUTH"},
    "remediation_evidence_refs": {"EVD"},
    "evidence_ref": {"EVD"},
    "finding_ref": {"FND"},
    "inherited_finding_refs": {"FND"},
    "resolution_finding_ref": {"FND"},
    "defect_ref": {"FND"},
    "work_item_refs": {"FEAT", "REV", "BUG", "REL", "WORK"},
    "included_changes": {"FEAT", "REV", "BUG", "REL", "WORK"},
    "affected_invariants": {"INV"},
}

# Directory families for fields that refer to repository records. Prefix
# checking alone is insufficient: a correctly-shaped EVD ID stored in a
# findings/ file must not satisfy evidence_refs.
REF_FIELD_TARGET_DIRS = {
    "evidence_refs": {"evidence"},
    "finding_refs": {"findings"},
    "gate_refs": {"gates"},
    "outcome_ref": {"gates"},
    "gate6_ref": {"gates"},
    "checkpoint_refs": {"approvals"},
    "approval_refs": {"approvals"},
    "decision_ref": {"approvals"},
    "risk_acceptance_ref": {"approvals"},
    "lowering_approval_ref": {"approvals"},
    "approval_ref": {"approvals"},
    "remediation_evidence_refs": {"evidence"},
    "evidence_ref": {"evidence"},
    "finding_ref": {"findings"},
    "inherited_finding_refs": {"findings"},
    "resolution_finding_ref": {"findings"},
    "defect_ref": {"findings"},
    "work_item_refs": {"features", "reviews", "bugs", "releases", "work-items"},
    "included_changes": {"features", "reviews", "bugs", "releases", "work-items"},
}

SAME_TYPE_RECORD_DIRS = {
    "gates": "GATE", "evidence": "EVD", "handoffs": "HND",
}

# templates/validation.md item 2: path-bearing fields checked for
# absolute paths / '..' traversal. Each entry is a dotted path template
# into a record's frontmatter; 'N' is a wildcard list index.
PATH_BEARING_FIELDS = [
    "scope.files", "enforcement_path", "component_scope",
]


def _scan_secrets(obj, path="$"):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SECRET_KEY_RE.search(k) and isinstance(v, str) and v.strip() and v.strip().upper() not in ("REDACTED", "<REDACTED>", "NULL", "NONE"):
                found.append(f"{path}.{k}: key name looks secret-like and has a non-empty value")
            found.extend(_scan_secrets(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(_scan_secrets(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        for pat in SECRET_VALUE_PATTERNS:
            if pat.search(obj):
                found.append(f"{path}: value matches a secret-like pattern ({pat.pattern})")
        if MACHINE_PATH_RE.match(obj):
            found.append(f"{path}: value looks like a machine-specific absolute path: {obj!r}")
        if CREDENTIALED_URL_RE.match(obj):
            found.append(f"{path}: value looks like a credentialed URL")
    return found


def _check_path_field(value, path):
    errs = []
    items = value if isinstance(value, list) else ([value] if isinstance(value, str) else [])
    for item in items:
        if not isinstance(item, str):
            continue
        if os.path.isabs(item) or PureWindowsPath(item).is_absolute() or PureWindowsPath(item).drive:
            errs.append(f"{path}: path field must be repository-relative, not absolute: {item!r}")
        normalized_parts = item.replace("\\", "/").split("/")
        if ".." in normalized_parts:
            errs.append(f"{path}: path field must not contain '..': {item!r}")
    return errs


def validate(repo_root: Path, core_root: Path = None):
    errors = []
    schema_validation = {}
    vcps_dir = repo_root / ".vcps"
    config_path = vcps_dir / "project.yaml"
    vcps_present = vcps_dir.exists() or vcps_dir.is_symlink()
    safe_vcps_dir = _safe_target_path(repo_root, vcps_dir) if vcps_present else None
    if vcps_present and (safe_vcps_dir is None or not safe_vcps_dir.is_dir()):
        return {"ok": False, "errors": [".vcps resolves outside the target repository"]}
    safe_config = _safe_target_path(repo_root, config_path)
    if safe_config is None or not safe_config.is_file():
        return {"ok": False, "errors": ["no .vcps/project.yaml"]}

    try:
        config = strict_yaml_load(read_repo_text(repo_root, safe_config), str(config_path))
    except Exception as exc:
        return {"ok": False, "errors": [f"project.yaml parse error: {exc}"]}
    if not isinstance(config, dict):
        return {"ok": False, "errors": ["project.yaml must be a YAML mapping"]}
    if not isinstance(config.get("installation"), dict):
        return {"ok": False, "errors": ["project.yaml.installation must be a mapping"]}

    required_top = [
        "schema_version", "artifact_layout_version", "vcps_version", "project",
        "level", "installation", "repository", "stack", "commands", "ci",
        "critical_domains", "applicable_invariants", "evidence_policy",
        "baseline_ref", "config_history", "lifecycle",
    ]
    for key in required_top:
        if key not in (config or {}):
            errors.append(f"project.yaml missing required field: {key}")

    # Locate the JSON Schemas (roadmap Phase B) relative to the Core root,
    # same fallback as detect_mode: an explicit --core, or the target
    # itself when this is VCPS's own dev-mode checkout. Schema validation
    # is SKIPPED (never silently PASSED) when no schema directory is
    # found -- absence of this evidence is reported, not hidden.
    schema_dir = (core_root or repo_root) / "templates" / "schemas"
    schemas_available = schema_dir.is_dir()
    secret_findings = []

    def _run_schema_check(fm, schema_name, record_label):
        if not schemas_available:
            return
        try:
            schema = vcps_schema.load_schema(schema_dir, schema_name)
        except Exception as exc:
            schema_validation.setdefault("load_errors", []).append(f"{schema_name}: {exc}")
            return
        schema_errors = vcps_schema.validate_instance(fm, schema)
        if schema_errors:
            schema_validation.setdefault("errors", {})[record_label] = schema_errors

    project_schema_version = (config or {}).get("schema_version")
    project_schema_name = vcps_schema.project_schema_name(project_schema_version)
    if project_schema_name:
        _run_schema_check(config, project_schema_name, "project.yaml")
    elif schemas_available:
        schema_validation.setdefault("errors", {})["project.yaml"] = [
            f"$.schema_version: no known schema for {project_schema_version!r}"
        ]
    secret_findings.extend(_scan_secrets(config, "project.yaml"))

    seen_ids = {}
    all_records = []  # (record_file, fm) for cross-record checks below
    if safe_vcps_dir and safe_vcps_dir.is_dir():
        for name in ("baseline.md", "invariants.md", "risk-model.md"):
            p = safe_vcps_dir / name
            safe_p = _safe_target_path(repo_root, p)
            if p.is_symlink() and safe_p is None:
                errors.append(f"{p}: singleton record symlink resolves outside the target repository")
            if safe_p and safe_p.is_file():
                try:
                    fm, _ = load_frontmatter(safe_p, repo_root)
                except Exception as exc:
                    errors.append(f"{p}: {exc}")
                    continue
                all_records.append((p, fm))
                schema_name = vcps_schema.SINGLETON_SCHEMA.get(name)
                if schema_name:
                    _run_schema_check(fm, schema_name, str(p.relative_to(repo_root)))
                secret_findings.extend(_scan_secrets(fm, str(p.relative_to(repo_root))))

        for sub in safe_vcps_dir.iterdir():
            safe_sub = _safe_target_path(repo_root, sub)
            if safe_sub is None:
                if sub.is_symlink():
                    errors.append(f"{sub}: record directory symlink resolves outside the target repository")
                continue
            if not safe_sub.is_dir():
                continue
            for record_file in safe_sub.glob("*.md"):
                safe_record = _safe_target_path(repo_root, record_file)
                if safe_record is None or not safe_record.is_file():
                    errors.append(f"{record_file}: record path resolves outside the target repository")
                    continue
                try:
                    fm, _ = load_frontmatter(safe_record, repo_root)
                except Exception as exc:
                    errors.append(f"{record_file}: {exc}")
                    continue
                all_records.append((record_file, fm))
                rid = fm.get("id")
                if not rid:
                    errors.append(f"{record_file}: missing id field")
                    continue
                prefix = rid.split("-", 1)[0]
                if prefix not in ID_PREFIXES and prefix != "INV":
                    errors.append(f"{record_file}: unrecognized id prefix {prefix!r}")
                if rid in seen_ids:
                    errors.append(
                        f"duplicate id {rid!r}: {seen_ids[rid]} and {record_file}"
                    )
                else:
                    seen_ids[rid] = str(record_file)

                rel_label = str(record_file.relative_to(repo_root))
                schema_name = vcps_schema.RECORD_DIR_SCHEMA.get(sub.name)
                if schema_name:
                    _run_schema_check(fm, schema_name, rel_label)

                secret_findings.extend(_scan_secrets(fm, rel_label))

                # templates/validation.md item 3: reference fields must
                # point at an ID of the expected prefix family.
                for field, allowed_prefixes in REF_FIELD_PREFIXES.items():
                    if field not in fm:
                        continue
                    val = fm[field]
                    refs = val if isinstance(val, list) else ([val] if isinstance(val, str) else [])
                    for ref in refs:
                        ref_prefix = ref.split("-", 1)[0]
                        if ref_prefix not in allowed_prefixes:
                            errors.append(
                                f"{rel_label}: field {field!r} value {ref!r} has prefix "
                                f"{ref_prefix!r}, expected one of {sorted(allowed_prefixes)}"
                            )

                # templates/validation.md item 2: path-bearing fields must
                # be repository-relative, never absolute or '..'-traversing.
                for field_path in PATH_BEARING_FIELDS:
                    parts = field_path.split(".")
                    node = fm
                    for p in parts[:-1]:
                        node = (node or {}).get(p) if isinstance(node, dict) else None
                    if isinstance(node, dict) and parts[-1] in node:
                        errors.extend(_check_path_field(node[parts[-1]], f"{rel_label}:{field_path}"))
                    elif parts[-1] in fm:
                        errors.extend(_check_path_field(fm[parts[-1]], f"{rel_label}:{field_path}"))

    if secret_findings:
        errors.extend(f"possible secret/credential (heuristic, review required): {f}" for f in secret_findings)

    # templates/validation.md item 3 (resolution half, beyond the
    # prefix-family check above): every reference field's value must
    # resolve to an ID this scan actually found -- a correct-looking
    # prefix pointing at a nonexistent record is still an orphan.
    inv_ids = set()
    for _, fm in all_records:
        if "invariants" in fm and isinstance(fm.get("invariants"), list):
            for inv in fm["invariants"]:
                if isinstance(inv, dict) and inv.get("id"):
                    inv_ids.add(inv["id"])
    def iter_named_values(value, location="$", seen=None):
        if seen is None:
            seen = set()
        if isinstance(value, dict):
            identity = id(value)
            if identity in seen:
                return
            seen.add(identity)
            for key, child in value.items():
                child_location = f"{location}.{key}"
                yield key, child, child_location
                yield from iter_named_values(child, child_location, seen)
        elif isinstance(value, list):
            identity = id(value)
            if identity in seen:
                return
            seen.add(identity)
            for index, child in enumerate(value):
                yield from iter_named_values(child, f"{location}[{index}]", seen)

    for record_file, fm in all_records:
        if not isinstance(fm, dict):
            continue
        rel_label = str(record_file.relative_to(repo_root))
        for field, val, field_path in iter_named_values(fm):
            allowed_prefixes = REF_FIELD_PREFIXES.get(field)
            same_type_prefix = SAME_TYPE_RECORD_DIRS.get(record_file.parent.name) \
                if field in ("supersedes_ref", "superseded_by_ref") else None
            if allowed_prefixes is None and same_type_prefix is None:
                continue
            expected_prefixes = allowed_prefixes or {same_type_prefix}
            refs = val if isinstance(val, list) else ([val] if isinstance(val, str) else [])
            for ref in refs:
                if not isinstance(ref, str) or not ref:
                    continue
                ref_prefix = ref.split("-", 1)[0]
                if ref_prefix not in expected_prefixes:
                    continue  # schema/prefix checks provide the focused error
                resolved = (ref in inv_ids) if ref_prefix == "INV" else (ref in seen_ids)
                if not resolved:
                    errors.append(
                        f"{rel_label}: field {field_path!r} value {ref!r} does not resolve to any record found"
                    )
                    continue
                target_record = next((path for path, record in all_records
                                      if isinstance(record, dict) and record.get("id") == ref), None)
                expected_dirs = REF_FIELD_TARGET_DIRS.get(field)
                if same_type_prefix:
                    expected_dirs = {record_file.parent.name}
                if target_record and expected_dirs and target_record.parent.name not in expected_dirs:
                    errors.append(
                        f"{rel_label}: field {field_path!r} value {ref!r} resolves to "
                        f"{target_record.parent.name}/, expected one of {sorted(expected_dirs)}"
                    )

    # templates/validation.md item 4: every active invariant
    # (project.yaml.applicable_invariants) must exist in invariants.md.
    for inv_id in (config or {}).get("applicable_invariants") or []:
        if inv_id not in inv_ids:
            errors.append(f"project.yaml: applicable_invariants entry {inv_id!r} does not exist in invariants.md")

    # templates/validation.md item 4: risk-model.md's derived PROJECT
    # level must match project.yaml's own recorded level -- level is
    # owned only by project.yaml, but it must agree with Core's derivation.
    risk_model_path = vcps_dir / "risk-model.md"
    if risk_model_path.is_file():
        try:
            safe_risk_model_path = _safe_target_path(repo_root, risk_model_path)
            if safe_risk_model_path is None:
                raise ValueError("risk-model.md resolves outside the target repository")
            risk_fm, _ = load_frontmatter(safe_risk_model_path, repo_root)
            profiles = risk_fm.get("profiles") or []
            project_profiles = [p for p in profiles if p.get("scope") == "PROJECT"]
            if len(project_profiles) != 1:
                errors.append(
                    f"risk-model.md: expected exactly one PROJECT-scope profile, found {len(project_profiles)}"
                )
            elif ((config or {}).get("level") or {}).get("value") != project_profiles[0].get("derived_level"):
                errors.append(
                    f"project.yaml level.value {((config or {}).get('level') or {}).get('value')!r} does not match "
                    f"risk-model.md's PROJECT profile derived_level {project_profiles[0].get('derived_level')!r} "
                    "(VCPS-RISK-020: level is owned only by project.yaml but must match Core's derivation)"
                )
            project_level = project_profiles[0].get("derived_level") if len(project_profiles) == 1 else None
            level_rank = {"L1": 1, "L2": 2, "L3": 3}
            for profile in profiles:
                dimensions = profile.get("dimensions") or {}
                ratings = {name: (value or {}).get("rating", 0)
                           for name, value in dimensions.items() if isinstance(value, dict)}
                severe_or_double_critical = (
                    any(rating == 3 for rating in ratings.values())
                    or sum(ratings.get(name) == 2 for name in
                           ("D1", "D2", "D3", "D4", "D5", "D6", "D8")) >= 2
                )
                minimum_level = ("L3" if severe_or_double_critical else
                                 "L2" if any(rating == 2 for rating in ratings.values()) else "L1")
                recorded_level = profile.get("derived_level")
                if level_rank.get(recorded_level, 0) < level_rank[minimum_level]:
                    errors.append(
                        f"risk-model.md: profile {profile.get('scope')!r} derives {recorded_level!r}, "
                        f"below the dimension-based minimum {minimum_level!r} (VCPS-RISK-020)"
                    )
                if (profile.get("scope") != "PROJECT" and profile.get("shared_path_elevation")
                        and level_rank.get(recorded_level, 0) < level_rank.get(project_level, 0)):
                    errors.append(
                        f"risk-model.md: shared-path profile {profile.get('scope')!r} must be elevated "
                        f"to project level {project_level!r} (VCPS-RISK-021)"
                    )
            component_scopes = [p.get("scope") for p in profiles if p.get("scope") != "PROJECT"]
            dupes = {s for s in component_scopes if component_scopes.count(s) > 1}
            if dupes:
                errors.append(f"risk-model.md: duplicate component risk profile scope(s): {sorted(dupes)}")
        except Exception:
            pass  # already reported above via the singleton-record loop

    # templates/validation.md item 2 (config fields, beyond the
    # per-record PATH_BEARING_FIELDS loop above): commands' working
    # directories, CI config paths, and component paths must all be
    # repository-relative.
    for cmd in (config or {}).get("commands") or []:
        if isinstance(cmd, dict) and "working_directory" in cmd:
            errors.extend(_check_path_field(cmd["working_directory"], "project.yaml:commands[].working_directory"))
    ci_cfg = (config or {}).get("ci") or {}
    if "config_paths" in ci_cfg:
        errors.extend(_check_path_field(ci_cfg["config_paths"], "project.yaml:ci.config_paths"))
    for comp in (config or {}).get("components") or []:
        if isinstance(comp, dict) and "path" in comp:
            errors.extend(_check_path_field(comp["path"], "project.yaml:components[].path"))

    # templates/validation.md item 9: baseline history is append-only.
    # An ADD_OBSERVATION entry's new_observation id must not already be
    # in the original observations array; a RESOLVE_OBSERVATION entry's
    # observation_id must reference one that IS in it. Neither changes
    # the original array itself (checked structurally: this reads
    # `observations` once and never writes it).
    baseline_path = vcps_dir / "baseline.md"
    if baseline_path.is_file():
        try:
            safe_baseline_path = _safe_target_path(repo_root, baseline_path)
            if safe_baseline_path is None:
                raise ValueError("baseline.md resolves outside the target repository")
            baseline_fm, _ = load_frontmatter(safe_baseline_path, repo_root)
            original_ids = {o.get("id") for o in (baseline_fm.get("observations") or [])}
            for i, ev in enumerate(baseline_fm.get("history") or []):
                if ev.get("type") == "ADD_OBSERVATION":
                    new_id = (ev.get("new_observation") or {}).get("id")
                    if new_id in original_ids:
                        errors.append(
                            f"baseline.md history[{i}]: ADD_OBSERVATION's new_observation id {new_id!r} "
                            "already exists in the original observations array"
                        )
                elif ev.get("type") == "RESOLVE_OBSERVATION":
                    obs_id = ev.get("observation_id")
                    if obs_id not in original_ids:
                        errors.append(
                            f"baseline.md history[{i}]: RESOLVE_OBSERVATION references observation_id "
                            f"{obs_id!r}, which is not in the original observations array"
                        )
        except Exception:
            pass  # already reported above via the singleton-record loop

    # templates/validation.md item 5: finding history is a projection of
    # current status and transitions cannot silently jump over a recorded
    # predecessor. The Core does not define a complete status graph, so this
    # checks continuity without inventing additional allowed transitions.
    for record_file, fm in all_records:
        if record_file.parent.name != "findings":
            continue
        history = fm.get("history") or []
        previous_status = None
        for index, event in enumerate(history):
            if not isinstance(event, dict):
                continue  # schema validation reports malformed history items
            from_status = event.get("from_status")
            to_status = event.get("to_status")
            if previous_status is not None and from_status is not None and from_status != previous_status:
                errors.append(
                    f"{record_file.relative_to(repo_root)}: history[{index}].from_status "
                    f"{from_status!r} does not continue prior to_status {previous_status!r}"
                )
            if to_status is not None:
                previous_status = to_status
        if previous_status is not None and previous_status != fm.get("status"):
            errors.append(
                f"{record_file.relative_to(repo_root)}: current status {fm.get('status')!r} "
                f"does not match latest history to_status {previous_status!r}"
            )

    # templates/validation.md item 5: a LEGACY finding's very first
    # history entry must record to_status OPEN (VCPS-SETUP-022: "Legacy
    # registry findings MUST be created in status OPEN").
    for record_file, fm in all_records:
        if fm.get("origin") == "LEGACY":
            history = fm.get("history") or []
            if history and history[0].get("to_status") != "OPEN":
                errors.append(
                    f"{record_file.relative_to(repo_root)}: LEGACY finding's first history entry has "
                    f"to_status {history[0].get('to_status')!r}, must be OPEN (VCPS-SETUP-022)"
                )

    # templates/validation.md item 2: "A pending baseline reference is
    # valid only before Stage 8; COMPLETE requires no pending artifacts" --
    # applied to baseline_ref: it may remain pending only before Stage 8.
    installation_state = ((config or {}).get("installation") or {})
    declared_stage = installation_state.get("stage")
    if (config or {}).get("baseline_ref") is None:
        if installation_state.get("status") == "COMPLETE":
            errors.append(
                "project.yaml: installation.status is COMPLETE but baseline_ref is still null "
                "(templates/contract.md: a baseline reference may be pending only before Stage 8)"
            )
        elif isinstance(declared_stage, int) and declared_stage >= 8:
            errors.append(
                f"project.yaml: baseline_ref is pending at installation.stage {declared_stage}; "
                "a pending baseline is valid only before Stage 8"
            )

    # templates/validation.md item 9: a baseline observation's check_id
    # should correspond to a command this project actually configured --
    # an unknown check_id is a sign the baseline references a check that
    # was never discovered/recorded (or was renamed/removed since).
    baseline_path = vcps_dir / "baseline.md"
    if baseline_path.is_file():
        try:
            safe_baseline_path = _safe_target_path(repo_root, baseline_path)
            if safe_baseline_path is None:
                raise ValueError("baseline.md resolves outside the target repository")
            baseline_fm, _ = load_frontmatter(safe_baseline_path, repo_root)
            configured_ids = {c.get("id") for c in (config or {}).get("commands") or []}
            for obs in baseline_fm.get("observations") or []:
                check_id = obs.get("check_id")
                if check_id and check_id not in configured_ids:
                    errors.append(
                        f"baseline.md: observation {obs.get('id')!r} references check_id {check_id!r}, "
                        f"which is not among project.yaml's configured commands {sorted(configured_ids)}"
                    )
        except Exception:
            pass  # already reported above via the singleton-record loop

    # templates/validation.md item 10: "Rejection and silence never pass a
    # gate" -- a gate record citing a checkpoint whose recorded decision is
    # REJECTED must never itself be PASS.
    approval_decisions = {}
    approvals_by_id = {}
    records_by_id = {fm.get("id"): (path, fm) for path, fm in all_records if fm.get("id")}
    for record_file, fm in all_records:
        if fm.get("kind") == "DECISION" and fm.get("id"):
            approval_decisions[fm["id"]] = fm.get("decision")
            approvals_by_id[fm["id"]] = (record_file, fm)
    for record_file, fm in all_records:
        if fm.get("outcome") != "PASS":
            continue
        for cp_ref in fm.get("checkpoint_refs") or []:
            if approval_decisions.get(cp_ref) == "REJECTED":
                errors.append(
                    f"{record_file.relative_to(repo_root)}: outcome is PASS but checkpoint_refs cites "
                    f"{cp_ref!r}, whose recorded decision is REJECTED (templates/validation.md item 10: "
                    "rejection never passes a gate)"
                )

    # templates/validation.md item 6 and VCPS-EVD-001: a PASS gate must cite
    # evidence records that themselves report PASS and carry a revision. For
    # Gates 4/5, every cited record must bind to the exact evaluated revision.
    for record_file, fm in all_records:
        if not (fm.get("gate") and fm.get("outcome") == "PASS"):
            continue
        label = str(record_file.relative_to(repo_root))
        evidence_refs = fm.get("evidence_refs") or []
        if not evidence_refs:
            errors.append(f"{label}: gate PASS requires at least one evidence reference")
        for evidence_ref in evidence_refs:
            evidence = records_by_id.get(evidence_ref)
            if not evidence:
                continue  # the generic reference pass reports the orphan
            evidence_path, evidence_fm = evidence
            if evidence_fm.get("result") != "PASS":
                errors.append(
                    f"{label}: gate PASS cites {evidence_ref!r} with result "
                    f"{evidence_fm.get('result')!r}, not PASS"
                )
            evidence_revision = evidence_fm.get("revision")
            if evidence_revision is None:
                errors.append(f"{label}: gate PASS evidence {evidence_ref!r} has no revision")
            elif fm.get("gate") in (4, 5) and evidence_revision != fm.get("revision"):
                errors.append(
                    f"{label}: Gate {fm.get('gate')} revision {fm.get('revision')!r} differs from "
                    f"evidence {evidence_ref!r} revision {evidence_revision!r} ({evidence_path})"
                )

    # templates/validation.md item 8: validate the mechanical FEATURE
    # transition history and HC-14 acceptance projection. This checks only
    # recorded state/links; it does not authenticate that human_actor is a
    # real human or judge whether the acceptance scope covers the criteria.
    lifecycle_order = ["PROPOSED", "SPECIFIED", "CODED", "VERIFIED",
                       "ACCEPTED", "PRODUCTION_PROVEN"]
    lifecycle_rank = {state: index for index, state in enumerate(lifecycle_order)}
    for record_file, fm in all_records:
        if fm.get("intent") != "FEATURE":
            continue
        label = str(record_file.relative_to(repo_root))
        history = fm.get("history") or []
        previous_state = None
        low_level = ((fm.get("scope") or {}).get("level") == "L1")
        if not history:
            errors.append(f"{label}: FEATURE lifecycle requires at least one history event")
        for index, event in enumerate(history):
            from_state = event.get("from_state")
            to_state = event.get("to_state")
            if index == 0:
                allowed_initial = {"PROPOSED", "SPECIFIED"} if low_level else {"PROPOSED"}
                if from_state is not None or to_state not in allowed_initial:
                    errors.append(
                        f"{label}: history[0] must establish an initial state from {sorted(allowed_initial)} "
                        "without a from_state"
                    )
            if index and from_state != previous_state:
                errors.append(
                    f"{label}: history[{index}].from_state {from_state!r} does not continue "
                    f"the prior state {previous_state!r}"
                )
            if to_state not in lifecycle_rank and to_state != "WITHDRAWN":
                errors.append(f"{label}: history[{index}].to_state {to_state!r} is not a lifecycle state")
            if from_state is not None and from_state not in lifecycle_rank and from_state != "WITHDRAWN":
                errors.append(f"{label}: history[{index}].from_state {from_state!r} is not a lifecycle state")
            elif from_state is not None and to_state is not None:
                if to_state == "WITHDRAWN":
                    pass  # withdrawal is permitted from any retained state
                elif from_state == "WITHDRAWN":
                    errors.append(f"{label}: a WITHDRAWN feature cannot transition back to {to_state!r}")
                elif from_state in lifecycle_rank and to_state in lifecycle_rank:
                    old_rank, new_rank = lifecycle_rank[from_state], lifecycle_rank[to_state]
                    forward_one = new_rank == old_rank + 1
                    permitted_demotion = (
                        (from_state in ("VERIFIED", "ACCEPTED", "PRODUCTION_PROVEN")
                         and to_state in ("CODED", "SPECIFIED"))
                        or (from_state == "ACCEPTED" and to_state == "VERIFIED")
                        or (from_state == "PRODUCTION_PROVEN" and to_state == "ACCEPTED")
                    )
                    l1_collapsed = low_level and from_state == "PROPOSED" and to_state == "CODED"
                    if not (forward_one or permitted_demotion or l1_collapsed or from_state == to_state):
                        errors.append(
                            f"{label}: lifecycle history skips or reverses an unlisted transition "
                            f"{from_state!r} -> {to_state!r} (standard/lifecycle.md VCPS-LC-002/010)"
                        )
            previous_state = to_state
        if history and previous_state != fm.get("lifecycle_state"):
            errors.append(
                f"{label}: lifecycle_state {fm.get('lifecycle_state')!r} does not match "
                f"the latest history state {previous_state!r}"
            )

        acceptance = fm.get("acceptance") or {}
        decision_ref = acceptance.get("decision_ref")
        if decision_ref is None:
            if acceptance.get("state") != "PENDING":
                errors.append(f"{label}: acceptance without decision_ref must remain PENDING")
            continue
        approval = approvals_by_id.get(decision_ref)
        if not approval:
            # The general reference-resolution pass reports the orphan; keep
            # this rule's diagnostic focused on its semantic requirement.
            continue
        decision_file, decision_fm = approval
        if "HC-14" not in (decision_fm.get("checkpoint_codes") or []):
            errors.append(f"{label}: acceptance decision {decision_ref!r} is not an HC-14 decision")
        if acceptance.get("state") != decision_fm.get("decision"):
            errors.append(
                f"{label}: acceptance.state {acceptance.get('state')!r} does not equal "
                f"HC-14 decision {decision_fm.get('decision')!r} in {decision_file}"
            )

    installation = (config or {}).get("installation") or {}
    plan = installation.get("plan")
    events = installation.get("stage_events") or []
    archived_plans = installation.get("plan_history") or []
    hashes_seen = set()
    if plan is not None and "sha256" in plan:
        recomputed = plan_hash(plan)
        if recomputed != plan["sha256"]:
            errors.append(
                f"plan sha256 mismatch: recorded {plan['sha256']!r}, "
                f"recomputed {recomputed!r}"
            )
        for ev in events:
            ph = ev.get("plan_hash")
            if ph and ph != plan["sha256"]:
                archived_hashes = {
                    p.get("sha256") for p in (installation.get("plan_history") or [])
                }
                if ph not in archived_hashes:
                    errors.append(
                        f"stage event references unresolvable plan_hash {ph!r}"
                    )
        hashes_seen.add(plan.get("sha256"))
    for index, archived in enumerate(archived_plans):
        archived_hash = archived.get("sha256")
        recomputed = plan_hash(archived)
        if archived_hash != recomputed:
            errors.append(
                f"plan_history[{index}] sha256 mismatch: recorded {archived_hash!r}, "
                f"recomputed {recomputed!r}"
            )
        if archived_hash in hashes_seen:
            errors.append(f"plan_history[{index}] duplicates an active or archived plan hash {archived_hash!r}")
        hashes_seen.add(archived_hash)
    all_plans = ([plan] if plan else []) + archived_plans

    def path_is_allowed(path, allowed):
        if not isinstance(path, str) or _check_path_field(path, "plan path"):
            return False
        return any(fnmatch.fnmatchcase(path, pattern) for pattern in allowed
                   if isinstance(pattern, str)
                   and not _check_path_field(pattern.replace("*", "x").replace("?", "x"), "allowed path"))

    for plan_index, candidate_plan in enumerate(all_plans):
        if not isinstance(candidate_plan, dict):
            continue  # JSON Schema reports malformed plan shape
        allowed_paths = candidate_plan.get("allowed_paths") or []
        allowed_operations = candidate_plan.get("allowed_operations") or []
        planned_paths = set()
        for field_name in ("create_paths", "modify_paths"):
            paths = candidate_plan.get(field_name) or []
            operation = "create" if field_name == "create_paths" else "modify"
            if paths and operation not in allowed_operations:
                label = "installation.plan" if plan_index == 0 and plan else f"plan_history[{plan_index - (1 if plan else 0)}]"
                errors.append(f"{label}.{field_name} requires allowed_operations to include {operation!r}")
            for path in paths:
                if isinstance(path, str):
                    planned_paths.add(path)
                if not path_is_allowed(path, allowed_paths):
                    label = "installation.plan" if plan_index == 0 and plan else f"plan_history[{plan_index - (1 if plan else 0)}]"
                    errors.append(
                        f"{label}.{field_name} path {path!r} is outside allowed_paths"
                    )
        max_changed_files = candidate_plan.get("max_changed_files")
        if isinstance(max_changed_files, int) and len(planned_paths) > max_changed_files:
            label = "installation.plan" if plan_index == 0 and plan else f"plan_history[{plan_index - (1 if plan else 0)}]"
            errors.append(
                f"{label} plans {len(planned_paths)} unique paths but max_changed_files is {max_changed_files}"
            )

    mutation_paths_by_plan = {}
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue  # JSON Schema reports malformed event shape
        event_hash = event.get("plan_hash")
        matching_plans = [p for p in all_plans
                          if isinstance(p, dict) and p.get("sha256") == event_hash]
        if event_hash and len(matching_plans) != 1:
            errors.append(
                f"installation.stage_events[{index}] plan_hash {event_hash!r} must resolve to exactly one plan"
            )
        if len(matching_plans) == 1:
            event_plan = matching_plans[0]
            allowed = event_plan.get("allowed_paths") or []
            planned_paths = set(event_plan.get("create_paths") or []) | set(event_plan.get("modify_paths") or [])
            mutation_paths_by_plan.setdefault(event_hash, set())
            for path in event.get("mutation_paths") or []:
                if not path_is_allowed(path, allowed):
                    errors.append(
                        f"installation.stage_events[{index}] mutation path {path!r} is outside "
                        f"the allowed_paths of plan {event_hash!r}"
                    )
                if path not in planned_paths:
                    errors.append(
                        f"installation.stage_events[{index}] mutation path {path!r} is not declared "
                        f"in create_paths or modify_paths of plan {event_hash!r}"
                    )
                if isinstance(path, str) and path_is_allowed(path, allowed) and path in planned_paths:
                    mutation_paths_by_plan[event_hash].add(path)

    for candidate_plan in all_plans:
        if not isinstance(candidate_plan, dict):
            continue
        candidate_hash = candidate_plan.get("sha256")
        max_changed_files = candidate_plan.get("max_changed_files")
        mutated_paths = mutation_paths_by_plan.get(candidate_hash, set())
        if isinstance(max_changed_files, int) and len(mutated_paths) > max_changed_files:
            errors.append(
                f"plan {candidate_hash!r} records {len(mutated_paths)} unique mutation paths "
                f"but max_changed_files is {max_changed_files}"
            )

    # VCPS-SETUP-055: installation.stage is a journal projection, not the
    # highest stage ever visited. BLOCKED and INVALIDATED make a stage
    # incomplete until a later COMPLETED attempt is appended.
    if project_schema_version == SUPPORTED_PROJECT_SCHEMA and isinstance(installation, dict):
        completed_stages = set()
        for event in events:
            if not isinstance(event, dict):
                continue  # schema validation reports malformed event shapes
            event_stage = event.get("stage")
            if not isinstance(event_stage, int) or isinstance(event_stage, bool) or not 1 <= event_stage <= 11:
                continue
            event_state = event.get("event_state") or event.get("state")
            if event_state == "COMPLETED":
                completed_stages.add(event_stage)
            elif event_state in ("BLOCKED", "INVALIDATED"):
                completed_stages.discard(event_stage)
        expected_stage = next((n for n in range(1, 12) if n not in completed_stages), None)
        declared_stage = installation.get("stage")
        if declared_stage != expected_stage:
            errors.append(
                f"installation.stage {declared_stage!r} does not match the earliest "
                f"incomplete journal stage {expected_stage!r}"
            )
        if installation.get("status") == "COMPLETE" and expected_stage is not None:
            errors.append(
                f"installation.status COMPLETE requires all eleven stages completed; "
                f"stage {expected_stage} is incomplete"
            )

    if schema_validation.get("errors"):
        for label, errs in schema_validation["errors"].items():
            errors.extend(f"schema violation in {label}: {e}" for e in errs)
    if schema_validation.get("load_errors"):
        errors.extend(f"schema load error: {e}" for e in schema_validation["load_errors"])

    result = {"ok": not errors, "errors": errors, "ids_seen": len(seen_ids)}
    result["schema_validation_status"] = "CHECKED" if schemas_available else "SKIPPED_NO_CORE_SCHEMAS"
    return result


# --- CLI -----------------------------------------------------------------

def main():
    # --target/--core are attached to EACH subcommand (via `parents=`), not
    # to the top-level parser, so the invocation shape is
    # "vcps_tool.py <subcommand> --target <path> [--core <path>] [...]" —
    # subcommand first, flags after. This matches the simple, already-
    # verified-working Claude Code allowed-tools pattern shape
    # `Bash(<script> <subcommand> *)` with a single trailing wildcard;
    # putting --target/--core before the subcommand (the original shape)
    # would require an allowed-tools pattern to match a wildcard spanning
    # multiple space-separated tokens before a fixed literal, which was
    # never actually verified against Claude Code's matching semantics and
    # is exactly the kind of assumption that caused the live-tested
    # --repo/--target defect this restructuring follows from.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target", default=".", help="target repository root")
    common.add_argument("--core", default=None, help="VCPS Core root (for detect)")

    parser = argparse.ArgumentParser(prog="vcps_tool.py")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("detect", parents=[common])
    sub.add_parser("inventory", parents=[common])
    p_rs = sub.add_parser("resume-status", parents=[common])
    p_rs.add_argument("--no-git", action="store_true")
    sub.add_parser("validate", parents=[common])

    p_fp = sub.add_parser("fingerprint", parents=[common])
    p_fp.add_argument("--scope", nargs="+", required=True)
    p_fp.add_argument("--no-git", action="store_true")

    p_ph = sub.add_parser("plan-hash", parents=[common])
    p_ph.add_argument("--stdin", action="store_true", default=True)

    p_aw = sub.add_parser("atomic-write", parents=[common])
    p_aw.add_argument("--file", required=True)
    p_aw.add_argument("--stdin", action="store_true", default=True)

    sub.add_parser("migrate-project-schema", parents=[common])
    sub.add_parser("rollback-project-schema", parents=[common])

    args = parser.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(json.dumps({"error": f"target not found: {target}"}))
        sys.exit(2)

    try:
        if args.command == "detect":
            core = Path(args.core).resolve() if args.core else target
            print(json.dumps(detect_mode(target, core), indent=2))
        elif args.command == "inventory":
            print(json.dumps(inventory(target), indent=2))
        elif args.command == "resume-status":
            print(json.dumps(resume_status(target, not args.no_git), indent=2))
        elif args.command == "validate":
            core_for_schemas = Path(args.core).resolve() if args.core else None
            result = validate(target, core_for_schemas)
            print(json.dumps(result, indent=2))
            if not result["ok"]:
                sys.exit(1)
        elif args.command == "fingerprint":
            print(json.dumps(
                compute_fingerprint(target, args.scope, not args.no_git), indent=2
            ))
        elif args.command == "plan-hash":
            plan_obj = json.loads(sys.stdin.read())
            print(json.dumps({"sha256": plan_hash(plan_obj)}))
        elif args.command == "atomic-write":
            content = sys.stdin.read()
            print(json.dumps(atomic_write(target, args.file, content)))
        elif args.command == "migrate-project-schema":
            print(json.dumps(migrate_project_schema(target), indent=2))
        elif args.command == "rollback-project-schema":
            print(json.dumps(rollback_project_schema(target), indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

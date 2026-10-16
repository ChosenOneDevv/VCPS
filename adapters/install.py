#!/usr/bin/env python3
"""Installer for the VCPS reference adapters (Phase K,
evaluation/completion-roadmap.md). Makes the manual "symlink or copy
adapter directories by hand" procedure documented in adapters/README.md,
adapters/claude-code/README.md, and adapters/codex/README.md into one
repeatable, verified command -- it does not change what those README
files already specify, it only automates following them exactly.

This script makes no VCPS Core judgment of any kind (no mode detection,
no risk rating, no mutation beyond installing adapter files) -- that
remains entirely the setup adapter's job (VCPS-CORE-001). It is purely
mechanical: copy or symlink known file sets, verify them, print a report.

Usage:
    install.py --adapter claude-code --target <repo> [--mode copy|symlink]
               [--skills name [name ...]] [--vendor-core] [--source <path>]
    install.py --adapter codex --target <repo> [--skills name [name ...]]
               [--source <path>]
    install.py --adapter codex --global [--skills name [name ...]]
               [--source <path>]
    install.py --verify --adapter claude-code --target <repo> [--source <path>]
"""

import argparse
import filecmp
import json
import os
import hashlib
import re
import tempfile
import uuid
from datetime import datetime, timezone
import shutil
import sys
from pathlib import Path

CLAUDE_SKILLS = [
    "vcps-setup", "vcps-router", "vcps-audit", "vcps-review", "vcps-bug",
    "vcps-tiny", "vcps-feature", "vcps-hotfix", "vcps-release",
]
# Sibling-path dependencies each skill's own SKILL.md loads via
# ${CLAUDE_SKILL_DIR}/../<name>/... (grep '${CLAUDE_SKILL_DIR}/\.\./[a-z-]*'
# across every SKILL.md to re-derive this if a skill's dependencies ever
# change). "lib" is not a selectable skill, just the shared mechanical
# helper vcps-audit/vcps-review/vcps-bug/vcps-tiny/vcps-feature/
# vcps-hotfix/vcps-release all depend on.
CLAUDE_SHARED_LIB = "lib"
CLAUDE_SIBLING_DEPS = {
    "vcps-audit": {CLAUDE_SHARED_LIB, "vcps-setup"},
    "vcps-review": {CLAUDE_SHARED_LIB},
    "vcps-bug": {CLAUDE_SHARED_LIB},
    "vcps-tiny": {CLAUDE_SHARED_LIB, "vcps-router"},
    "vcps-feature": {CLAUDE_SHARED_LIB, "vcps-router"},
    "vcps-hotfix": {CLAUDE_SHARED_LIB},
    "vcps-release": {CLAUDE_SHARED_LIB},
}

# Codex's own skill files reference adapters/claude-code/lib/... and
# adapters/claude-code/vcps-setup/scripts/... by a hard-coded repository-
# relative path (disclosed in evaluation/codex-adapter.md and
# adapters/README.md as a real installability cost of not vendoring a
# duplicate helper copy) -- they are not written to be portable into an
# arbitrary external target the way the Claude Code skills are. This
# installer's codex mode vendors that exact subtree alongside the skills
# so the hard-coded path still resolves; it does not fix the underlying
# portability limitation, which is a Codex-adapter design question, not
# an installer one.
CODEX_SKILLS = list(CLAUDE_SKILLS)
CODEX_REQUIRED_CLAUDE_SUBTREE = [
    "adapters/claude-code/lib",
    "adapters/claude-code/vcps-setup/scripts",
]

IGNORE_PATTERNS = shutil.ignore_patterns("__pycache__", "*.pyc")


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parent.parent


def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fname in filenames:
            if fname.endswith(".pyc"):
                continue
            yield Path(dirpath, fname)


def _copy_tree(src: Path, dst: Path):
    if dst.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {dst}")
    shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)


def _symlink(src: Path, dst: Path):
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing path: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src, target_is_directory=src.is_dir())


def install_claude_code(source: Path, target: Path, skills, mode: str, vendor_core: bool):
    report = {"adapter": "claude-code", "mode": mode, "installed": [], "warnings": []}
    skills_dir = target / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    to_install = list(skills)
    for name in skills:
        for dep in CLAUDE_SIBLING_DEPS.get(name, ()):
            if dep not in to_install:
                report["warnings"].append(
                    f"{name} depends on a sibling '{dep}' "
                    "(${CLAUDE_SKILL_DIR}/../" + dep + "/... in its SKILL.md); "
                    "installing it automatically even though it was not "
                    "explicitly requested."
                )
                to_install.append(dep)

    for name in to_install:
        src = source / "adapters" / "claude-code" / name
        if not src.is_dir():
            raise FileNotFoundError(f"unknown claude-code component: {name} (looked for {src})")
        dst = skills_dir / name
        if mode == "copy":
            _copy_tree(src, dst)
        elif mode == "symlink":
            _symlink(src.resolve(), dst)
        else:
            raise ValueError(f"unknown mode: {mode}")
        report["installed"].append(str(dst))

    # adapters/README.md: "if skills are copied under .claude/skills/<name>,
    # copy [UNTRUSTED-CONTENT.md] to .claude/UNTRUSTED-CONTENT.md so their
    # relative reference remains valid." Symlink installs resolve it from
    # the source tree already and need no copy.
    if mode == "copy":
        untrusted_src = source / "adapters" / "UNTRUSTED-CONTENT.md"
        untrusted_dst = target / ".claude" / "UNTRUSTED-CONTENT.md"
        if not untrusted_dst.exists():
            shutil.copyfile(untrusted_src, untrusted_dst)
            report["installed"].append(str(untrusted_dst))

    if vendor_core:
        report["vendored_core"] = _vendor_core(source, target)

    report["verification"] = _verify_claude_code(source, target, to_install, mode)
    return report


def install_codex(source: Path, target: Path, skills, mode: str):
    if mode != "copy":
        raise ValueError("codex installs only support --mode copy (see module docstring)")
    report = {"adapter": "codex", "mode": mode, "installed": [], "warnings": [
        "Codex skills reference adapters/claude-code/lib/ and "
        "adapters/claude-code/vcps-setup/scripts/ by a hard-coded "
        "repository-relative path (evaluation/codex-adapter.md); this "
        "installer vendors that exact subtree so the hard-coded path "
        "still resolves, which is a workaround, not a clean install. "
        "See adapters/codex/README.md.",
    ]}
    skills_dir = target / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for name in skills:
        src = source / "adapters" / "codex" / name
        if not src.is_dir():
            raise FileNotFoundError(f"unknown codex component: {name} (looked for {src})")
        dst = skills_dir / name
        _copy_tree(src, dst)
        report["installed"].append(str(dst))

    for rel in CODEX_REQUIRED_CLAUDE_SUBTREE:
        src = source / rel
        dst = target / rel
        if not src.is_dir():
            raise FileNotFoundError(f"required subtree missing from source: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        _copy_tree(src, dst)
        report["installed"].append(str(dst))

    # adapters/codex/README.md: "If copying skills into
    # .agents/skills/<name>/, also copy adapters/UNTRUSTED-CONTENT.md to
    # .agents/UNTRUSTED-CONTENT.md" (each skill's own ../../UNTRUSTED-
    # CONTENT.md reference resolves there from .agents/skills/<name>/).
    untrusted_src = source / "adapters" / "UNTRUSTED-CONTENT.md"
    untrusted_dst = target / ".agents" / "UNTRUSTED-CONTENT.md"
    if not untrusted_dst.exists():
        untrusted_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(untrusted_src, untrusted_dst)
        report["installed"].append(str(untrusted_dst))

    report["verification"] = _verify_dirs(
        [(source / "adapters" / "codex" / n, target / ".agents" / "skills" / n) for n in skills]
        + [(source / rel, target / rel) for rel in CODEX_REQUIRED_CLAUDE_SUBTREE]
    )
    return report


def install_codex_global(source: Path, home: Path, skills):
    """Install Codex skills for this user and keep a complete VCPS source
    tree beside them so their relative Core/helper paths work in any repo."""
    agents_dir = home / ".agents"
    skills_dir = agents_dir / "skills"
    source_dst = agents_dir / "vcps-source"
    untrusted_dst = agents_dir / "UNTRUSTED-CONTENT.md"
    destinations = [skills_dir / name for name in skills]
    destinations += [source_dst, untrusted_dst]
    existing = [str(path) for path in destinations if path.exists() or path.is_symlink()]
    if existing:
        raise FileExistsError("refusing to overwrite existing path(s): " + ", ".join(existing))

    skills_dir.mkdir(parents=True, exist_ok=True)
    report = {"adapter": "codex", "scope": "user", "mode": "copy",
              "installed": [], "warnings": [
                  "Skills are installed for this OS user under ~/.agents/skills.",
                  "Global availability does not change Codex sandbox or approval settings; "
                  "review adapters/codex/README.md before allowing mutation.",
              ]}

    for name in skills:
        src = source / "adapters" / "codex" / name
        if not src.is_dir():
            raise FileNotFoundError(f"unknown codex component: {name} (looked for {src})")
        dst = skills_dir / name
        _copy_tree(src, dst)
        report["installed"].append(str(dst))

    source_dst.mkdir(parents=True)
    for rel in ("standard", "workflows", "templates", "adapters"):
        _copy_tree(source / rel, source_dst / rel)
        report["installed"].append(str(source_dst / rel))
    shutil.copyfile(source / "VERSION", source_dst / "VERSION")
    report["installed"].append(str(source_dst / "VERSION"))

    untrusted_src = source / "adapters" / "UNTRUSTED-CONTENT.md"
    shutil.copyfile(untrusted_src, untrusted_dst)
    report["installed"].append(str(untrusted_dst))

    pairs = [(source / "adapters" / "codex" / n, skills_dir / n) for n in skills]
    pairs += [(source / rel, source_dst / rel)
              for rel in ("standard", "workflows", "templates", "adapters")]
    report["verification"] = _verify_dirs(pairs)
    return report


def _vendor_core(source: Path, target: Path):
    """Vendor a pinned Core copy per vcps-setup/references/core-discovery.md's
    documented future mechanism: standard/, workflows/, templates/ under
    .vcps-core/ in the target, so --core does not need to be passed by
    hand on every invocation."""
    core_dst = target / ".vcps-core"
    if core_dst.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {core_dst}")
    core_dst.mkdir(parents=True)
    installed = []
    for name in ("standard", "workflows", "templates"):
        src = source / name
        dst = core_dst / name
        _copy_tree(src, dst)
        installed.append(str(dst))
    version_src = source / "VERSION"
    if version_src.is_file():
        shutil.copyfile(version_src, core_dst / "VERSION")
        installed.append(str(core_dst / "VERSION"))
    return {"installed": installed}


def _verify_claude_code(source: Path, target: Path, names, mode: str):
    pairs = [(source / "adapters" / "claude-code" / n, target / ".claude" / "skills" / n) for n in names]
    return _verify_dirs(pairs, resolve_symlinks=(mode == "symlink"))


def _verify_dirs(pairs, resolve_symlinks=False):
    mismatches = []
    checked = 0
    for src, dst in pairs:
        cmp_target = dst.resolve() if resolve_symlinks else dst
        for src_file in _iter_files(src):
            rel = src_file.relative_to(src)
            dst_file = cmp_target / rel
            checked += 1
            if not dst_file.is_file() or not filecmp.cmp(src_file, dst_file, shallow=False):
                mismatches.append(str(dst_file))
    return {"files_checked": checked, "mismatches": mismatches, "ok": not mismatches}


def _expand_claude_skills(skills):
    result = list(dict.fromkeys(skills))
    for name in list(result):
        for dep in sorted(CLAUDE_SIBLING_DEPS.get(name, ())):
            if dep not in result:
                result.append(dep)
    return result


def _install_plan(source, adapter, target, skills, mode, vendor_core=False, global_install=False):
    """Describe all target paths without creating directories or files."""
    actions = []
    if adapter == "claude-code":
        names = _expand_claude_skills(skills)
        for name in names:
            actions.append({"path": f".claude/skills/{name}", "kind": mode,
                            "source": f"adapters/claude-code/{name}"})
        if mode == "copy":
            actions.append({"path": ".claude/UNTRUSTED-CONTENT.md", "kind": "copy",
                            "source": "adapters/UNTRUSTED-CONTENT.md"})
        if vendor_core:
            for name in ("standard", "workflows", "templates", "VERSION"):
                actions.append({"path": f".vcps-core/{name}", "kind": "copy", "source": name})
        base = target
    elif global_install:
        names = skills
        base = Path.home()
        for name in names:
            actions.append({"path": f".agents/skills/{name}", "kind": "copy",
                            "source": f"adapters/codex/{name}"})
        for rel in ("standard", "workflows", "templates", "adapters", "VERSION"):
            actions.append({"path": f".agents/vcps-source/{rel}", "kind": "copy", "source": rel})
        actions.append({"path": ".agents/UNTRUSTED-CONTENT.md", "kind": "copy",
                        "source": "adapters/UNTRUSTED-CONTENT.md"})
    else:
        names = skills
        base = target
        for name in names:
            actions.append({"path": f".agents/skills/{name}", "kind": "copy",
                            "source": f"adapters/codex/{name}"})
        for rel in CODEX_REQUIRED_CLAUDE_SUBTREE:
            actions.append({"path": rel, "kind": "copy", "source": rel})
        actions.append({"path": ".agents/UNTRUSTED-CONTENT.md", "kind": "copy",
                        "source": "adapters/UNTRUSTED-CONTENT.md"})
    manifest_rel = (".agents/vcps-install-" + adapter + ".json" if global_install
                    else ".vcps-install-" + adapter + ".json")
    actions.append({"path": manifest_rel, "kind": "manifest", "source": None})
    conflicts = []
    missing_sources = []
    for item in actions:
        dst = base / item["path"]
        src = source / item["source"] if item["source"] else None
        item["exists"] = dst.exists() or dst.is_symlink()
        if item["exists"]:
            conflicts.append(str(dst))
        if src is not None and not src.exists():
            missing_sources.append(str(src))
    return {
        "adapter": adapter,
        "scope": "user" if global_install else "repository",
        "mode": mode,
        "source": str(source),
        "target": str(base),
        "actions": actions,
        "conflicts": conflicts,
        "missing_sources": missing_sources,
        "ready": not conflicts and not missing_sources,
        "read_only": True,
    }


def _digest_path(path):
    """Stable hash for a copied tree, file, or symlink without following links."""
    if path.is_symlink():
        payload = {"type": "symlink", "target": os.readlink(path)}
    elif path.is_file():
        payload = {"type": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    elif path.is_dir():
        files = []
        for item in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            rel = item.relative_to(path).as_posix()
            if "__pycache__" in item.parts or item.suffix == ".pyc":
                continue
            if item.is_symlink():
                files.append([rel, "symlink", os.readlink(item)])
            elif item.is_file():
                files.append([rel, "file", hashlib.sha256(item.read_bytes()).hexdigest()])
            elif item.is_dir():
                files.append([rel, "directory"])
        payload = {"type": "directory", "entries": files}
    else:
        return None
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_destination(base: Path, relative: str):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or "\\" in relative:
        raise ValueError(f"unsafe install destination: {relative!r}")
    current = base
    for part in rel.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing symlinked install parent: {current}")
    return base / rel


def _manifest_path(adapter, target, global_install):
    rel = Path(".agents") / f"vcps-install-{adapter}.json" if global_install else Path(f".vcps-install-{adapter}.json")
    return _safe_destination(Path.home() if global_install else target, rel.as_posix())


def _manifest_managed_path(adapter, relative):
    """Limit lifecycle ownership to paths this adapter can actually install."""
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        return False
    if adapter == "claude-code":
        return (
            relative == ".claude/UNTRUSTED-CONTENT.md"
            or relative in {f".claude/skills/{name}" for name in [*CLAUDE_SKILLS, CLAUDE_SHARED_LIB]}
            or relative in {f".vcps-core/{name}" for name in
                            ("standard", "workflows", "templates", "VERSION")}
        )
    if adapter == "codex":
        return (
            relative == ".agents/UNTRUSTED-CONTENT.md"
            or relative in {f".agents/skills/{name}" for name in CODEX_SKILLS}
            or relative in {f".agents/vcps-source/{name}" for name in
                            ("standard", "workflows", "templates", "adapters", "VERSION")}
            or relative in CODEX_REQUIRED_CLAUDE_SUBTREE
        )
    return False


def _load_manifest(path):
    if not path.is_file() or path.is_symlink():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("format") != 1 or data.get("adapter") not in ("claude-code", "codex")
            or not isinstance(data.get("installed"), list)):
        raise ValueError(f"unsupported or malformed installer manifest: {path}")
    seen = set()
    for entry in data["installed"]:
        if not isinstance(entry, dict):
            raise ValueError(f"malformed installer manifest entry: {path}")
        relative = entry.get("path")
        digest = entry.get("digest")
        if not _manifest_managed_path(data["adapter"], relative):
            raise ValueError(f"manifest contains a path not owned by {data['adapter']}: {relative!r}")
        if relative in seen:
            raise ValueError(f"manifest contains a duplicate managed path: {relative!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"manifest contains an invalid path digest for {relative!r}")
        seen.add(relative)
    return data


def _action_items(plan):
    return [item for item in plan["actions"] if item["kind"] != "manifest"]


def _build_operation_plan(source, adapter, target, skills, mode, vendor_core,
                          global_install, operation):
    plan = _install_plan(source, adapter, target, skills, mode, vendor_core, global_install)
    base = Path.home() if global_install else target
    manifest = _manifest_path(adapter, target, global_install)
    manifest_rel = manifest.relative_to(base).as_posix()
    existing_manifest = _load_manifest(manifest)
    owned = {entry["path"]: entry for entry in (existing_manifest or {}).get("installed", [])}
    if operation in ("upgrade", "repair", "uninstall") and existing_manifest is None:
        plan["ready"] = False
        plan["errors"] = [f"no managed install manifest at {manifest}; refusing to guess ownership"]
        return plan
    if existing_manifest and existing_manifest.get("adapter") != adapter:
        plan["ready"] = False
        plan["errors"] = [f"manifest adapter mismatch at {manifest}"]
        return plan

    actions = _action_items(plan)
    conflicts, removals, selected = [], [], []
    if operation == "install":
        if existing_manifest:
            conflicts.append(str(manifest))
        for item in actions:
            dst = _safe_destination(base, item["path"])
            if dst.exists() or dst.is_symlink():
                conflicts.append(str(dst))
            selected.append(item)
    elif operation in ("upgrade", "repair"):
        for item in actions:
            dst = _safe_destination(base, item["path"])
            entry = owned.get(item["path"])
            if dst.exists() or dst.is_symlink():
                if not entry:
                    conflicts.append(f"unmanaged path blocks install: {dst}")
                elif _digest_path(dst) != entry.get("digest"):
                    conflicts.append(f"modified managed path requires manual review: {dst}")
                elif operation == "upgrade" or not dst.exists():
                    selected.append(item)
            else:
                selected.append(item)
        planned_paths = {item["path"] for item in actions}
        for rel, entry in owned.items():
            if rel in planned_paths:
                continue
            dst = _safe_destination(base, rel)
            if dst.exists() or dst.is_symlink():
                if _digest_path(dst) != entry.get("digest"):
                    conflicts.append(f"modified stale managed path requires manual review: {dst}")
                else:
                    removals.append(rel)
    elif operation == "uninstall":
        for rel, entry in owned.items():
            dst = _safe_destination(base, rel)
            if dst.exists() or dst.is_symlink():
                if _digest_path(dst) != entry.get("digest"):
                    conflicts.append(f"modified managed path requires manual review: {dst}")
                else:
                    removals.append(rel)
    else:
        raise ValueError(f"unknown installer operation: {operation}")

    plan.update({
        "operation": operation,
        "manifest": str(manifest),
        "actions": selected,
        "removals": removals,
        "conflicts": conflicts,
        "ready": not conflicts and not plan.get("missing_sources"),
        "owned_paths": sorted(owned),
    })
    # The manifest is always a material install output, but it is written only
    # after every other staged item has passed verification.
    if operation in ("install", "upgrade", "repair"):
        plan["actions"].append({"path": manifest_rel, "kind": "manifest", "source": None})
    return plan


def _remove_owned_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _execute_operation(source, plan, base, manifest_path):
    if not plan.get("ready"):
        raise RuntimeError("operation preflight failed: " + "; ".join(plan.get("conflicts", []) + plan.get("errors", [])))
    operation = plan["operation"]
    existing_manifest = _load_manifest(manifest_path)
    old_entries = {entry["path"]: entry for entry in (existing_manifest or {}).get("installed", [])}
    if operation == "uninstall":
        stage = Path(tempfile.mkdtemp(prefix=f".vcps-uninstall-{uuid.uuid4().hex[:8]}-", dir=base))
        moved = []
        try:
            for index, rel in enumerate(plan["removals"]):
                dst = _safe_destination(base, rel)
                backup = stage / "removed" / str(index)
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dst, backup)
                moved.append((dst, backup))
            backup = stage / "manifest.json"
            os.replace(manifest_path, backup)
            moved.append((manifest_path, backup))
        except Exception as exc:
            for dst, backup in reversed(moved):
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup, dst)
                except OSError:
                    pass
            shutil.rmtree(stage, ignore_errors=True)
            raise RuntimeError(f"uninstall rolled back after an error: {exc}") from exc
        shutil.rmtree(stage, ignore_errors=True)
        return {"operation": operation, "removed": plan["removals"], "ok": True}

    stage = Path(tempfile.mkdtemp(prefix=f".vcps-{operation}-{uuid.uuid4().hex[:8]}-", dir=base))
    staged = []
    committed = []
    created_parents = []
    try:
        for item in _action_items(plan):
            src = source / item["source"]
            staged_path = stage / item["path"]
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            if item["kind"] == "symlink":
                staged_path.symlink_to(src.resolve(), target_is_directory=src.is_dir())
            elif src.is_dir():
                shutil.copytree(src, staged_path, ignore=IGNORE_PATTERNS)
            else:
                shutil.copy2(src, staged_path)
            staged.append((item, staged_path))

        # Verify staged output against its intended source before touching target paths.
        for item, staged_path in staged:
            src = source / item["source"]
            if item["kind"] == "symlink":
                matches = staged_path.is_symlink() and staged_path.resolve() == src.resolve()
            else:
                matches = _digest_path(staged_path) == _digest_path(src)
            if not matches:
                raise RuntimeError(f"staged verification failed: {item['path']}")

        new_entries = {}
        for item, staged_path in staged:
            dst = _safe_destination(base, item["path"])
            parent = dst.parent
            missing = []
            probe = parent
            while not probe.exists():
                missing.append(probe)
                probe = probe.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_parents.append(directory)
            if dst.exists() or dst.is_symlink():
                if operation not in ("upgrade", "repair") or item["path"] not in old_entries:
                    raise FileExistsError(f"refusing to overwrite existing path: {dst}")
                backup = stage / "backups" / item["path"]
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dst, backup)
                staged_path.rename(dst)
                committed.append((dst, backup))
            else:
                os.replace(staged_path, dst)
                committed.append((dst, None))
            new_entries[item["path"]] = {
                "kind": item["kind"],
                "source": item["source"],
                "digest": _digest_path(dst),
            }

        # During repair, unchanged existing entries stay owned; during upgrade,
        # removed stale entries are deleted only after new paths are in place.
        if operation == "repair":
            new_entries = {**old_entries, **new_entries}
        elif operation == "upgrade":
            for rel in plan["removals"]:
                dst = _safe_destination(base, rel)
                backup = stage / "backups" / "stale" / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dst, backup)
                committed.append((dst, backup))

        manifest = {
            "format": 1,
            "adapter": plan["adapter"],
            "mode": plan["mode"],
            "source": str(source),
            "core_version": (source / "VERSION").read_text(encoding="utf-8").strip(),
            "adapter_version": (source / "adapters" / plan["adapter"] / "VERSION").read_text(encoding="utf-8").strip(),
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "skills": plan.get("skills", []),
            "vendor_core": bool(plan.get("vendor_core")),
            "installed": [{"path": rel, **new_entries[rel]} for rel in sorted(new_entries)],
        }
        manifest_stage = stage / "manifest.json"
        manifest_stage.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(manifest_stage, manifest_path)
        return {"operation": operation, "installed": sorted(new_entries),
                "removed": plan.get("removals", []), "manifest": str(manifest_path), "ok": True}
    except Exception:
        for dst, backup in reversed(committed):
            try:
                if dst.is_symlink() or dst.is_file():
                    dst.unlink()
                elif dst.is_dir():
                    shutil.rmtree(dst)
                if backup and (backup.exists() or backup.is_symlink()):
                    os.replace(backup, dst)
            except OSError:
                pass
        for directory in reversed(created_parents):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _verify_manifest(manifest_path, base):
    manifest = _load_manifest(manifest_path)
    if not manifest:
        return {"ok": False, "files_checked": 0, "mismatches": [f"missing manifest: {manifest_path}"]}
    mismatches = []
    checked = 0
    for entry in manifest["installed"]:
        path = _safe_destination(base, entry["path"])
        checked += 1
        if not (path.exists() or path.is_symlink()) or _digest_path(path) != entry.get("digest"):
            mismatches.append(str(path))
    return {"ok": not mismatches, "files_checked": checked, "mismatches": mismatches,
            "adapter": manifest.get("adapter"), "core_version": manifest.get("core_version"),
            "adapter_version": manifest.get("adapter_version")}


def _verify_install(source, adapter, target, skills, mode, vendor_core=False, global_install=False):
    """Verify all files currently installed by the documented copy layout."""
    if global_install:
        base = Path.home()
        pairs = [(source / "adapters/codex" / name, base / ".agents/skills" / name) for name in skills]
        pairs += [(source / rel, base / ".agents/vcps-source" / rel)
                  for rel in ("standard", "workflows", "templates", "adapters")]
        result = _verify_dirs(pairs)
        trust_src = source / "adapters/UNTRUSTED-CONTENT.md"
        trust_dst = base / ".agents/UNTRUSTED-CONTENT.md"
        result["files_checked"] += 1
        if not trust_dst.is_file() or not filecmp.cmp(trust_src, trust_dst, shallow=False):
            result["mismatches"].append(str(trust_dst))
        result["ok"] = not result["mismatches"]
        return result
    if adapter == "claude-code":
        names = _expand_claude_skills(skills)
        result = _verify_claude_code(source, target, names, mode)
        if mode == "copy":
            src, dst = source / "adapters/UNTRUSTED-CONTENT.md", target / ".claude/UNTRUSTED-CONTENT.md"
            result["files_checked"] += 1
            if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
                result["mismatches"].append(str(dst))
        if vendor_core:
            core = _verify_dirs([(source / name, target / ".vcps-core" / name)
                                 for name in ("standard", "workflows", "templates")])
            result["files_checked"] += core["files_checked"] + 1
            if not (target / ".vcps-core/VERSION").is_file() or not filecmp.cmp(
                    source / "VERSION", target / ".vcps-core/VERSION", shallow=False):
                core["mismatches"].append(str(target / ".vcps-core/VERSION"))
            result["mismatches"].extend(core["mismatches"])
        result["ok"] = not result["mismatches"]
        return result
    pairs = [(source / "adapters/codex" / name, target / ".agents/skills" / name) for name in skills]
    pairs += [(source / rel, target / rel) for rel in CODEX_REQUIRED_CLAUDE_SUBTREE]
    result = _verify_dirs(pairs)
    trust_src, trust_dst = source / "adapters/UNTRUSTED-CONTENT.md", target / ".agents/UNTRUSTED-CONTENT.md"
    result["files_checked"] += 1
    if not trust_dst.is_file() or not filecmp.cmp(trust_src, trust_dst, shallow=False):
        result["mismatches"].append(str(trust_dst))
    result["ok"] = not result["mismatches"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--adapter", choices=["claude-code", "codex"], required=True)
    parser.add_argument("--target", help="target repository root to install into")
    parser.add_argument("--global", dest="global_install", action="store_true",
                        help="codex only: install skills for this user in ~/.agents/skills")
    parser.add_argument("--source", default=None, help="VCPS repository root (default: this script's own repo)")
    parser.add_argument("--mode", choices=["copy", "symlink"], default=None)
    parser.add_argument("--skills", nargs="+", default=None,
                         help="component names to install (default: all for the chosen adapter)")
    parser.add_argument("--vendor-core", action="store_true",
                        help="claude-code only: also vendor standard/, workflows/, templates/ into <target>/.vcps-core/")
    parser.add_argument("--plan", "--dry-run", dest="plan", action="store_true",
                        help="show the install paths/conflicts without writing files")
    parser.add_argument("--verify", action="store_true",
                        help="compare all installed paths, including shared trust/Core files")
    parser.add_argument("--upgrade", action="store_true", help="update a manifest-managed install")
    parser.add_argument("--repair", action="store_true", help="restore missing manifest-managed paths")
    parser.add_argument("--uninstall", action="store_true", help="remove unchanged manifest-managed paths")
    args = parser.parse_args()

    source = Path(args.source).resolve() if args.source else _repo_root_from_here()
    if args.global_install:
        if args.adapter != "codex":
            print(json.dumps({"error": "--global is codex only"}))
            sys.exit(2)
        if args.target:
            print(json.dumps({"error": "--global and --target cannot be combined"}))
            sys.exit(2)
        target = None
    else:
        if not args.target:
            print(json.dumps({"error": "--target is required unless --global is used"}))
            sys.exit(2)
        target = Path(args.target).resolve()
    if not (source / "standard" / "VCPS.md").is_file():
        print(json.dumps({"error": f"source does not look like a VCPS repository: {source}"}))
        sys.exit(2)
    if target is not None and not target.is_dir():
        print(json.dumps({"error": f"target not found: {target}"}))
        sys.exit(2)

    try:
        if args.adapter == "claude-code":
            skills = args.skills if args.skills else list(CLAUDE_SKILLS)
            allowed = set(CLAUDE_SKILLS)
        else:
            skills = args.skills if args.skills else list(CODEX_SKILLS)
            allowed = set(CODEX_SKILLS)
        unknown = sorted(set(skills) - allowed)
        if unknown:
            raise ValueError(f"unknown {args.adapter} component(s): {', '.join(unknown)}")
        operations = [name for name in ("upgrade", "repair", "uninstall") if getattr(args, name)]
        operation = operations[0] if operations else "install"
        if len(operations) > 1:
            raise ValueError("--upgrade, --repair, and --uninstall are mutually exclusive")
        if args.verify and (args.plan or operations):
            raise ValueError("--verify cannot be combined with --plan or a lifecycle operation")
        if args.adapter == "codex" and args.vendor_core:
            raise ValueError("--vendor-core is claude-code only")
        if args.global_install and args.adapter == "codex" and args.mode not in (None, "copy"):
            raise ValueError("--global Codex install only supports copy mode")
        if args.adapter == "codex" and not args.global_install and args.mode == "symlink":
            raise ValueError("codex installs only support --mode copy")
        manifest_path = _manifest_path(args.adapter, target, args.global_install)
        old_manifest = _load_manifest(manifest_path) if operation in ("upgrade", "repair", "uninstall") else None
        if args.skills is None and old_manifest and old_manifest.get("skills"):
            skills = old_manifest["skills"]
        vendor_core = args.vendor_core or bool(old_manifest and old_manifest.get("vendor_core"))
        mode = args.mode or (old_manifest.get("mode") if old_manifest else None) or "copy"
        if args.verify:
            base = Path.home() if args.global_install else target
            if manifest_path.is_file():
                report = {"verification": _verify_manifest(manifest_path, base)}
            else:
                report = {"verification": _verify_install(
                    source, args.adapter, target, skills, mode,
                    vendor_core, args.global_install)}
        else:
            report = _build_operation_plan(source, args.adapter, target, skills, mode,
                                           vendor_core, args.global_install, operation)
            report["skills"] = skills
            report["vendor_core"] = vendor_core
        if args.plan:
            print(json.dumps(report, indent=2))
            sys.exit(0 if report.get("ready") else 1)
        if args.verify:
            print(json.dumps(report, indent=2))
            sys.exit(0 if report["verification"]["ok"] else 1)
        base = Path.home() if args.global_install else target
        result = _execute_operation(source, report, base, manifest_path)
        result["verification"] = _verify_manifest(manifest_path, base) if operation != "uninstall" else {"ok": True}
        report = result
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    print(json.dumps(report, indent=2))
    if not report.get("verification", {}).get("ok", True):
        sys.exit(1)


if __name__ == "__main__":
    main()

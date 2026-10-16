#!/usr/bin/env python3
"""Record-to-schema dispatch and JSON Schema Draft 2020-12 validation.

Schemas are loaded from the selected, repository-local Core. Remote
references are rejected so validating target-controlled records cannot cause
network access. This module validates shape; cross-record policy remains in
``vcps_tool.validate`` and templates/validation.md.
"""

from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
RECORD_DIR_SCHEMA = {
    "evidence": "evidence.schema.json",
    "findings": "finding.schema.json",
    "gates": "gate.schema.json",
    "approvals": "approval.schema.json",
    "handoffs": "handoff.schema.json",
    "features": "work-item.schema.json",
    "reviews": "work-item.schema.json",
    "bugs": "work-item.schema.json",
    "releases": "work-item.schema.json",
    "work-items": "work-item.schema.json",
}

SINGLETON_SCHEMA = {
    "baseline.md": "baseline.schema.json",
    "invariants.md": "invariants.schema.json",
    "risk-model.md": "risk-model.schema.json",
}


def project_schema_name(schema_version):
    """Return the project schema matching the supported schema version."""
    if schema_version == "0.2.0":
        return "project.schema.json"
    if schema_version == "0.1.0":
        return "project-0.1.0.schema.json"
    return None


def schema_for_record_path(rel_path: str, project_schema_version=None):
    """Return the schema filename for a .vcps-relative path, if known."""
    name = Path(rel_path).name
    if name == "project.yaml":
        return project_schema_name(project_schema_version)
    if name in SINGLETON_SCHEMA:
        return SINGLETON_SCHEMA[name]
    for part in Path(rel_path).parts:
        if part in RECORD_DIR_SCHEMA:
            return RECORD_DIR_SCHEMA[part]
    return None


def _reject_remote_refs(schema, path="$ "):
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if ref is not None and (not isinstance(ref, str) or not ref.startswith("#/")):
            raise ValueError(f"{path}: only local JSON Schema references are allowed, got {ref!r}")
        for key, value in schema.items():
            _reject_remote_refs(value, f"{path}.{key}")
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            _reject_remote_refs(value, f"{path}[{index}]")


def load_schema(schema_dir: Path, schema_name: str):
    """Read and meta-validate one schema without resolving remote resources."""
    import json

    path = schema_dir / schema_name
    if not path.is_file():
        raise FileNotFoundError(f"schema not found: {path}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    _reject_remote_refs(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def _instance_path(error):
    result = "$"
    for part in error.absolute_path:
        if isinstance(part, int):
            result += f"[{part}]"
        elif isinstance(part, str) and part.isidentifier():
            result += f".{part}"
        else:
            result += f"[{part!r}]"
    return result


def validate_instance(instance, schema, root=None, path="$ "):
    """Return readable instance-path errors from the full 2020-12 engine.

    ``root`` and ``path`` are accepted for compatibility with the former
    repository-local subset validator; local refs use jsonschema's standard
    same-document resolution.
    """
    _reject_remote_refs(schema)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda err: (tuple(map(str, err.absolute_path)), err.message),
    )
    return [f"{_instance_path(error)}: {error.message} ({error.validator})" for error in errors]


def load_markdown_frontmatter(path: Path, repo_root: Path):
    """Use the setup helper's strict YAML/frontmatter reader for an example."""
    import vcps_tool

    return vcps_tool.load_frontmatter(path, repo_root)

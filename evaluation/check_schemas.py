#!/usr/bin/env python3
"""Check schema documents with the real Draft 2020-12 implementation."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "templates" / "schemas"
sys.path.insert(0, str(ROOT / "adapters/claude-code/vcps-setup/scripts"))

import vcps_schema  # noqa: E402


def main():
    import jsonschema

    failures = []
    schemas = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema
        except Exception as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    if not schemas:
        failures.append("no JSON Schema files found")

    example = ROOT / "templates/examples/project"
    project_path = example / ".vcps/project.yaml"
    if project_path.is_file():
        import yaml

        config = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        schema_name = vcps_schema.project_schema_name(config.get("schema_version"))
        if schema_name not in schemas:
            failures.append(f"worked example project schema missing: {schema_name}")
        else:
            errors = vcps_schema.validate_instance(config, schemas[schema_name])
            failures.extend(f"worked example .vcps/project.yaml: {error}" for error in errors)

        for record_file in sorted((example / ".vcps").rglob("*.md")):
            loaded = vcps_schema.load_markdown_frontmatter(record_file, example)
            if loaded is None:
                failures.append(f"{record_file.relative_to(ROOT)}: no YAML frontmatter")
                continue
            frontmatter, _ = loaded
            rel = record_file.relative_to(example / ".vcps").as_posix()
            schema_name = vcps_schema.schema_for_record_path(rel, config.get("schema_version"))
            if schema_name and schema_name in schemas:
                errors = vcps_schema.validate_instance(frontmatter, schemas[schema_name])
                failures.extend(f"{record_file.relative_to(ROOT)}: {error}" for error in errors)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"PASS {len(schemas)} JSON Schemas validate as Draft 2020-12; worked example accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

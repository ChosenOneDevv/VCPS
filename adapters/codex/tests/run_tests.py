#!/usr/bin/env python3
"""Structural tests for all nine Codex adapter skills.

No LIVE_ADAPTER_EXECUTION evidence was obtained in this
environment. This suite
checks only what can be verified by reading files: valid frontmatter/
YAML, intentional-invocation policy, helper paths, and that skills do
not claim a Claude-specific mechanism
(allowed-tools, disable-model-invocation) it has no business using.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ADAPTER_ROOT / "vcps-setup"
SKILL_MD = SKILL_DIR / "SKILL.md"

results = []


def record(category, name, ok, detail=""):
    results.append({"category": category, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{category}] {status} - {name}" + (f" :: {detail}" if detail and not ok else ""))


def main():
    cat = "STRUCTURAL_TEST"

    record(cat, "S1 README.md exists and is non-empty",
           (ADAPTER_ROOT / "README.md").is_file() and (ADAPTER_ROOT / "README.md").stat().st_size > 0)

    cap_map = ADAPTER_ROOT / "references" / "capability-mapping.md"
    record(cat, "S2 capability-mapping.md exists and is non-empty",
           cap_map.is_file() and cap_map.stat().st_size > 0)
    cap_text = cap_map.read_text(encoding="utf-8") if cap_map.is_file() else ""
    record(cat, "S3 capability-mapping.md marks itself informative/non-Core",
           "informative" in cap_text.lower() and "VCPS-CORE-001" in cap_text)
    record(cat, "S4 capability-mapping.md discloses UNVERIFIED rows rather than claiming full verification",
           "UNVERIFIED" in cap_text)
    record(cat, "S5 capability-mapping.md states runtime evidence was not obtained",
           "No `LIVE_ADAPTER_EXECUTION` evidence was obtained" in re.sub(r"\s+", " ", cap_text))

    record(cat, "S6 SKILL.md exists and has YAML frontmatter",
           SKILL_MD.is_file() and SKILL_MD.read_text(encoding="utf-8").startswith("---\n"))

    if SKILL_MD.is_file():
        text = SKILL_MD.read_text(encoding="utf-8")
        fm_end = text.index("\n---\n", 4)
        frontmatter_text = text[4:fm_end]
        try:
            fm = yaml.safe_load(frontmatter_text)
        except Exception as exc:
            fm = None
            record(cat, "S7 SKILL.md frontmatter is valid YAML", False, str(exc))
        if fm is not None:
            record(cat, "S7 SKILL.md frontmatter is valid YAML", True)
            record(cat, "S8 SKILL.md frontmatter has name and description (Codex's documented required fields)",
                   "name" in fm and "description" in fm)
            record(cat, "S9 SKILL.md frontmatter does NOT use Claude-specific keys (allowed-tools/disable-model-invocation)",
                   "allowed-tools" not in fm and "disable-model-invocation" not in fm)

        record(cat, "S10 SKILL.md instructs confirming the sandbox/approval precondition before mutation",
               "approval_policy" in text and "untrusted" in text)
        record(cat, "S11 SKILL.md references the capability-mapping.md file it depends on",
               "capability-mapping.md" in text)

        # Every repository-relative path SKILL.md names in backticks/prose
        # that looks like a real file reference should resolve. We check
        # the specific cross-adapter and same-repo paths this file
        # explicitly names, rather than attempting a generic backtick scan
        # (which would false-positive on command-line examples).
        named_paths = [
            "adapters/claude-code/vcps-setup/scripts/vcps_tool.py",
            "adapters/claude-code/vcps-setup/references/core-discovery.md",
            "adapters/claude-code/vcps-setup/references/loading-map.md",
            "adapters/codex/references/capability-mapping.md",
            "adapters/codex/README.md",
            "workflows/setup.md",
            "standard/VCPS.md",
            "standard/open-questions.md",
        ]
        missing = [p for p in named_paths if p in text and not (REPO_ROOT / p).exists()]
        record(cat, "S12 every repository path SKILL.md names actually exists on disk",
               not missing, str(missing))

    openai_yaml = SKILL_DIR / "agents" / "openai.yaml"
    record(cat, "S13 agents/openai.yaml exists", openai_yaml.is_file())
    if openai_yaml.is_file():
        try:
            data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
            record(cat, "S14 agents/openai.yaml is valid YAML with policy.allow_implicit_invocation: false",
                   isinstance(data, dict) and data.get("policy", {}).get("allow_implicit_invocation") is False)
        except Exception as exc:
            record(cat, "S14 agents/openai.yaml is valid YAML with policy.allow_implicit_invocation: false",
                   False, str(exc))

    rules_example = SKILL_DIR / "example.codex-rules.rules"
    record(cat, "S15 example.codex-rules.rules exists and references the mutating subcommand",
           rules_example.is_file() and "atomic-write" in rules_example.read_text(encoding="utf-8")
           and "prompt" in rules_example.read_text(encoding="utf-8"))

    record(cat, "S16 the cross-adapter script this skill depends on actually exists",
           (REPO_ROOT / "adapters" / "claude-code" / "vcps-setup" / "scripts" / "vcps_tool.py").is_file())

    record(cat, "S17 VERSION file exists and is non-empty",
           (ADAPTER_ROOT / "VERSION").is_file() and (ADAPTER_ROOT / "VERSION").stat().st_size > 0)

    # Sanity: this adapter's own text should never claim Claude-specific
    # mechanisms exist in Codex (the whole point of researching real docs
    # first rather than assuming).
    all_text = cap_text + (SKILL_MD.read_text(encoding="utf-8") if SKILL_MD.is_file() else "")
    record(cat, "S18 capability mapping cites real external sources (sanity: contains at least one https:// URL)",
           "https://" in all_text)

    skills = {
        "vcps-setup": [
            "adapters/claude-code/vcps-setup/scripts/vcps_tool.py",
            "adapters/codex/references/capability-mapping.md",
        ],
        "vcps-router": ["adapters/claude-code/vcps-router/scripts/vcps_router.py"],
        "vcps-audit": [
            "adapters/claude-code/lib/vcps_evidence.py",
            "adapters/claude-code/vcps-setup/scripts/vcps_tool.py",
        ],
        "vcps-review": ["adapters/claude-code/lib/vcps_evidence.py"],
        "vcps-bug": ["adapters/claude-code/lib/vcps_evidence.py"],
        "vcps-tiny": [
            "adapters/claude-code/vcps-router/scripts/vcps_router.py",
            "adapters/claude-code/lib/vcps_evidence.py",
        ],
        "vcps-feature": [
            "adapters/claude-code/vcps-router/scripts/vcps_router.py",
            "adapters/claude-code/lib/vcps_evidence.py",
        ],
        "vcps-hotfix": ["adapters/claude-code/lib/vcps_evidence.py"],
        "vcps-release": ["adapters/claude-code/lib/vcps_evidence.py"],
    }
    missing_skills = []
    bad_policies = []
    bad_frontmatter = []
    bad_paths = []
    missing_mutation_boundary = []
    missing_core_rules = []
    missing_root_resolution = []
    core_rules = {
        "vcps-router": ["Before forming an intent opinion", "forced_r3", "exactly one", "confirmed live production impact"],
        "vcps-audit": ["do not modify", "matches_head: false", "Never re-run verification", "FULL", "HC-08"],
        "vcps-review": ["only `DEFECT` findings may be fixed", "`EVIDENCE_GAP`", "production-reachable security exposure", "HC-08"],
        "vcps-bug": ["reproduce the reported defect", "If reproduction fails", "parent revision", "HC-13"],
        "vcps-tiny": ["forced_r3: true", "Gate 3 and Gate 4 `PASS`", "re-route immediately"],
        "vcps-feature": ["forced_r3: true", "same revision", "HC-14", "HC-09"],
        "vcps-hotfix": ["confirmed live production impact", "HC-16 is the only deferral mechanism", "HC-03", "HC-10", "lapsed-deferral-check"],
        "vcps-release": ["once for the complete release unit", "HC-10", "does not trigger deployment", "BLOCKED (DEPENDENCY)", "E5"],
    }
    for skill_name, helper_paths in skills.items():
        skill_dir = ADAPTER_ROOT / skill_name
        skill_file = skill_dir / "SKILL.md"
        policy_file = skill_dir / "agents" / "openai.yaml"
        if not skill_file.is_file() or skill_file.stat().st_size == 0:
            missing_skills.append(skill_name)
            continue
        skill_text = skill_file.read_text(encoding="utf-8")
        if skill_name != "vcps-setup" and (
                "adapters/codex/vcps-setup/SKILL.md" not in skill_text
                or "source root" not in skill_text.lower()
                or "--target" not in skill_text):
            missing_root_resolution.append(skill_name)
        for requirement in core_rules.get(skill_name, []):
            if requirement not in skill_text:
                missing_core_rules.append(f"{skill_name}: {requirement}")
        if not skill_text.startswith("---\n"):
            bad_frontmatter.append(f"{skill_name}: missing frontmatter")
        else:
            try:
                marker = skill_text.index("\n---\n", 4)
                metadata = yaml.safe_load(skill_text[4:marker])
                if not isinstance(metadata, dict) or not metadata.get("name") or not metadata.get("description"):
                    bad_frontmatter.append(f"{skill_name}: name/description missing")
                if "allowed-tools" in metadata or "disable-model-invocation" in metadata:
                    bad_frontmatter.append(f"{skill_name}: Claude-only frontmatter key")
            except Exception as exc:
                bad_frontmatter.append(f"{skill_name}: {exc}")
        if not policy_file.is_file():
            bad_policies.append(f"{skill_name}: agents/openai.yaml missing")
        else:
            try:
                policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
                if policy.get("policy", {}).get("allow_implicit_invocation") is not False:
                    bad_policies.append(f"{skill_name}: implicit invocation not disabled")
            except Exception as exc:
                bad_policies.append(f"{skill_name}: {exc}")
        for helper_path in helper_paths:
            if (helper_path not in skill_text
                    and Path(helper_path).name not in skill_text) or not (REPO_ROOT / helper_path).is_file():
                bad_paths.append(f"{skill_name}: {helper_path}")
        if skill_name != "vcps-audit" and "approval_policy" not in skill_text:
            missing_mutation_boundary.append(skill_name)

    record(cat, "S19 all nine workflow skills exist",
           not missing_skills, str(missing_skills))
    record(cat, "S20 every skill has valid Codex frontmatter and no Claude-only keys",
           not bad_frontmatter, str(bad_frontmatter))
    record(cat, "S21 every skill disables implicit invocation through agents/openai.yaml",
           not bad_policies, str(bad_policies))
    record(cat, "S22 every skill references its real shared helper dependencies",
           not bad_paths, str(bad_paths))
    record(cat, "S23 every mutating skill documents the Codex approval boundary",
           not missing_mutation_boundary, str(missing_mutation_boundary))
    record(cat, "S24 adapter README documents all nine skill components",
           all((ADAPTER_ROOT / name).is_dir() for name in skills)
           and "nine skills" in (ADAPTER_ROOT / "README.md").read_text(encoding="utf-8"))
    record(cat, "S25 all eight ported skills retain their workflow-specific safety and exit rules",
           not missing_core_rules, str(missing_core_rules))
    record(cat, "S26 every helper-using skill distinguishes VCPS source root from target repo",
           not missing_root_resolution
           and "target repository path" in (ADAPTER_ROOT / "README.md").read_text(encoding="utf-8"),
           str(missing_root_resolution))

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

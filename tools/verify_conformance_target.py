#!/usr/bin/env python3
"""Fail-closed checks for the exact conformance target and catalog metadata."""
import importlib.metadata
import json
import os
import re
import sys
import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_PATH = os.path.join(BASE, "conformance-target.json")
CATALOG_PATH = os.path.join(BASE, "catalog", "valid-configurations-v1.json")
RULES_PATH = os.path.join(BASE, "catalog", "compatibility-rules-v1.yaml")

def check_target(target, catalog, rules, installed_version, module_version=None):
    errors = []
    expected = target.get("implementation", {}).get("version")
    if not expected:
        errors.append("IMPLEMENTATION_VERSION_MISSING")
    elif installed_version != expected:
        errors.append(f"HARNESS_VERSION_MISMATCH:expected={expected},got={installed_version}")
    if module_version is not None and module_version != expected:
        errors.append(f"RUNTIME_VERSION_MISMATCH:expected={expected},got={module_version}")
    if catalog.get("catalog_version") != target.get("catalog_version"):
        errors.append("CATALOG_VERSION_MISMATCH")
    if rules.get("version") != target.get("rules_version"):
        errors.append("RULES_VERSION_MISMATCH")
    summary = catalog.get("summary", {})
    for key, expected_value in target.get("catalog_summary", {}).items():
        if summary.get(key) != expected_value:
            errors.append(f"CATALOG_SUMMARY_MISMATCH:{key}")
    configurations = catalog.get("configurations", [])
    if len(configurations) != target.get("catalog_summary", {}).get("total"):
        errors.append("CATALOG_CONFIGURATION_COUNT_MISMATCH")
    for index, item in enumerate(configurations):
        if "admissible_structural" not in item:
            errors.append(f"CATALOG_STRUCTURAL_FLAG_MISSING:{index}")
        if "effective_guarantee_demonstrated" not in item:
            errors.append(f"CATALOG_EFFECTIVE_FLAG_MISSING:{index}")
    commit = target.get("implementation", {}).get("source_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("IMPLEMENTATION_SOURCE_COMMIT_INVALID")
    semantics = target.get("guarantee_semantics", {})
    if semantics.get("effective_guarantee_demonstrated") != "independent evidence dimension; never inferred from admissible_structural":
        errors.append("STRUCTURAL_EFFECTIVE_SEPARATION_MISSING")
    return errors

def main():
    with open(TARGET_PATH, encoding="utf-8") as stream:
        target = json.load(stream)
    with open(CATALOG_PATH, encoding="utf-8") as stream:
        catalog = json.load(stream)
    with open(RULES_PATH, encoding="utf-8") as stream:
        rules = yaml.safe_load(stream)
    try:
        installed = importlib.metadata.version(target["implementation"]["distribution"])
    except importlib.metadata.PackageNotFoundError:
        print("HARNESS_PACKAGE_NOT_INSTALLED", file=sys.stderr)
        return 1
    try:
        import tenir_governance
        runtime_version = getattr(tenir_governance, "__version__", None)
    except Exception as exc:
        print(f"HARNESS_PACKAGE_IMPORT_FAILED:{type(exc).__name__}", file=sys.stderr)
        return 1
    errors = check_target(target, catalog, rules, installed, runtime_version)
    if errors:
        print("CONFORMANCE TARGET INVALID:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"OK target={target['implementation']['distribution']}=={installed}; catalog={target['catalog_version']}; rules={target['rules_version']}; configurations={len(catalog['configurations'])}")
    print("NOTE: structural admissibility does not demonstrate effective guarantees.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

import json
import os
import sys
import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from verify_conformance_target import check_target  # noqa: E402

def load(path, json_file=False):
    with open(os.path.join(BASE, path), encoding="utf-8") as stream:
        return json.load(stream) if json_file else yaml.safe_load(stream)

def test_exact_pinned_target_and_catalog_are_consistent():
    target = load("conformance-target.json", json_file=True)
    catalog = load("catalog/valid-configurations-v1.json", json_file=True)
    rules = load("catalog/compatibility-rules-v1.yaml")
    assert check_target(target, catalog, rules, "5.6.1", "5.6.1") == []

def test_wrong_implementation_version_fails_closed():
    target = load("conformance-target.json", json_file=True)
    catalog = load("catalog/valid-configurations-v1.json", json_file=True)
    rules = load("catalog/compatibility-rules-v1.yaml")
    errors = check_target(target, catalog, rules, "5.6.0", "5.6.0")
    assert any("HARNESS_VERSION_MISMATCH" in error for error in errors)

def test_wrong_catalog_or_rules_version_fails_closed():
    target = load("conformance-target.json", json_file=True)
    catalog = load("catalog/valid-configurations-v1.json", json_file=True)
    rules = load("catalog/compatibility-rules-v1.yaml")
    catalog["catalog_version"] = "0.9.0"
    rules["version"] = "0.9.0"
    errors = check_target(target, catalog, rules, "5.6.1", "5.6.1")
    assert "CATALOG_VERSION_MISMATCH" in errors
    assert "RULES_VERSION_MISMATCH" in errors

def test_missing_effective_guarantee_field_is_not_inferred():
    target = load("conformance-target.json", json_file=True)
    catalog = load("catalog/valid-configurations-v1.json", json_file=True)
    rules = load("catalog/compatibility-rules-v1.yaml")
    del catalog["configurations"][0]["effective_guarantee_demonstrated"]
    errors = check_target(target, catalog, rules, "5.6.1", "5.6.1")
    assert any("CATALOG_EFFECTIVE_FLAG_MISSING:0" == error for error in errors)

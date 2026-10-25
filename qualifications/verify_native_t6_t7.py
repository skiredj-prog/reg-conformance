#!/usr/bin/env python3
"""Fail-closed scoped T6/T7 evidence mapper, never normative certification."""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VECTOR_TESTS = {
    "CT-R4-011": (
        "test_reconcile_can_recover_interrupted_dispatching_operation",
        "test_reconcile_resolves",
        "test_indeterminate_reconciliation_normalizes_dispatching_to_unknown",
        "test_stripe_reconciliation_empty_search_remains_unknown",
    ),
    "CT-R4-012": (
        "test_concurrent_failed_reconciliation_refunds_only_once",
        "test_reconcile_failed",
        "test_i5_contradictory_reconciliation_does_not_refund_or_fail",
        "test_timeout_behavior",
        "test_i5_provider_failure_with_hypothesis_violation_returns_hold_without_refund",
    ),
}

def classify(path: Path):
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    expected = {name for names in VECTOR_TESTS.values() for name in names}
    observed = [case.get("name") for case in cases]
    if len(observed) != len(set(observed)):
        raise ValueError("duplicate testcase names in JUnit evidence")
    missing = sorted(expected - set(observed))
    unexpected = sorted(set(observed) - expected)
    if missing or unexpected:
        raise ValueError(f"test set drift: missing={missing} unexpected={unexpected}")
    failed = sorted(case.get("name") for case in cases
                    if any(case.find(tag) is not None for tag in ("failure", "error", "skipped")))
    if failed:
        raise ValueError(f"failed, errored or skipped: {failed}")
    return {
        "scope": "TENIR-Gov 5.7.0 native provider recovery: scoped semantic subset",
        "normative_equivalence": False,
        "native_conformant": False,
        "evidence_level": "SCOPED_IMPLEMENTATION_TESTED",
        "vectors": {
            vector: {
                "status": "PARTIAL_SEMANTIC_EVIDENCE",
                "test_count": len(names),
                "tests": list(names),
                "unproven": ("AttemptState.RESOLVED qualification and tau_K boundary" if vector.endswith("011")
                             else "AttemptState.FAILED evidence_qualified predicate and tau_K timeout contract"),
            } for vector, names in VECTOR_TESTS.items()
        },
        "CT-R4-013": {"status": "IMPLEMENTATION_GAP",
                      "reason": "Native retry_eligible/new-attempt contract not demonstrated"},
        "tests_passed": len(cases),
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("junit_xml", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    try:
        result = classify(args.junit_xml)
    except (ValueError, ET.ParseError, OSError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"SCOPED_T6_T7_EVIDENCE: {result['tests_passed']} tests; normative equivalence NOT established")
    return 0

if __name__ == "__main__":
    sys.exit(main())

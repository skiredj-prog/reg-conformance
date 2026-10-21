"""Validation of REG mediation drafts, including cross-reference and authority guards."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "contracts" / "draft-v0.1.schema.json")
                    .read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)


def _unique(items: list[str], label: str) -> None:
    if len(items) != len(set(items)):
        raise ValueError(f"Duplicate {label}")


def validate_result(result: dict) -> None:
    """Reject authority promotion and inconsistent references even in hand-made artifacts."""
    VALIDATOR.validate(result)
    source_ids = [s["source_id"] + ":" + s["section"]
                  for s in result["source_refs"]]
    _unique(source_ids, "source reference")
    findings = result["assumptions"]
    finding_ids = [f["finding_id"] for f in findings]
    _unique(finding_ids, "finding")
    known_source_ids = {s["source_id"] for s in result["source_refs"]}
    for finding in findings:
        if any(ref["source_id"] not in known_source_ids for ref in finding["source_refs"]):
            raise ValueError("Assumption points to an undeclared source")
    candidates = result["candidate_properties"]
    _unique([p["proposal_id"] for p in candidates], "candidate proposal")
    if any(p["finding_id"] not in set(finding_ids) for p in candidates):
        raise ValueError("Candidate references an unknown finding")
    controls = result["controls"]
    _unique([c["control_id"] for c in controls], "control")
    for control in controls:
        declared = set(control["evidence_ids_declared"])
        available = set(control["evidence_ids_available"])
        missing = set(control["missing_evidence_ids"])
        _unique(control["evidence_ids_declared"], "evidence reference")
        if available & missing or available | missing != declared:
            raise ValueError("Control evidence classification is inconsistent")
        expected = ("MISSING_EVIDENCE" if missing or not declared
                    else "REFERENCED_UNVERIFIED")
        if control["assessment"] != expected:
            raise ValueError("Evidence does not support the claimed assessment")
    if result["entry"] == "PREVENT":
        has_conflicts = any(f["assessment"] == "structural_conflict" for f in findings)
        if has_conflicts != (result["status"] == "DECLARED_PREMISE_CONFLICT"):
            raise ValueError("PREVENT status must reflect declared-premise conflicts")
    if result["entry"] == "PREPARE":
        missing = any(c["assessment"] == "MISSING_EVIDENCE" for c in controls)
        if missing != (result["status"] == "EVIDENCE_INCOMPLETE"):
            raise ValueError("PREPARE status must reflect missing evidence")

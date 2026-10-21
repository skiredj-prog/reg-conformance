"""REG mediation v0.1: two independent, non-certifying entry points.

PREVENT: requirements and optional validated REG Discovery report -> questions
and explicitly unapproved property candidates.

PREPARE: declared controls and evidence references -> missing items and
review queue. The presence of a reference never proves a control effective.

No L3 profile admission, L4 generation, runtime invocation, network I/O or
GitHub issue publication is performed by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from discovery.verify_report import validate_report

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = "0.1.0"
STATUS = {
    "PREVENT": {"NEEDS_CLARIFICATION", "DECLARED_PREMISE_CONFLICT"},
    "PREPARE": {"EVIDENCE_INCOMPLETE", "EVIDENCE_REVIEW_REQUIRED"},
}
LIMITATIONS = {
    "not_legal_advice": True,
    "not_compliance_assessment": True,
    "not_implementation_audit": True,
    "not_effective_guarantee": True,
    "not_execution_authorization": True,
}


def _field(value: Any, name: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be a nonempty string up to {maximum} characters")
    return value.strip()


def _items(value: Any, name: str, maximum: int = 50) -> list:
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{name} must be an array with at most {maximum} items")
    return value


def _unique(values: list[str], name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {name}")


def _refs(values: Any) -> list[dict]:
    result = []
    for item in _items(values, "source_refs", 20):
        if not isinstance(item, dict) or set(item) != {"source_id", "section"}:
            raise ValueError("source_refs require only source_id and section")
        result.append({
            "source_id": _field(item["source_id"], "source_id", 150),
            "section": _field(item["section"], "section", 200),
        })
    _unique([f"{r['source_id']}:{r['section']}" for r in result], "source_refs")
    return result


def _make_id(request: dict) -> str:
    normalized = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "reg-mediation-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]


def mediate(request: dict) -> dict:
    """Return a reviewable draft, never an approved normative or runtime artifact."""
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    allowed = {
        "schema_version", "entry", "scope", "intent", "source_refs",
        "discovery_report", "selected_finding_ids", "controls", "evidence",
    }
    if set(request) - allowed:
        raise ValueError("Unknown mediation request property")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported mediation schema version")
    entry = request.get("entry")
    if entry not in STATUS:
        raise ValueError("entry must be PREVENT or PREPARE")
    scope = _field(request.get("scope"), "scope", 500)
    source_refs = _refs(request.get("source_refs", []))
    base = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _make_id(request),
        "entry": entry,
        "scope": scope,
        "status": "",
        "intent": None,
        "upstream_discovery": None,
        "source_refs": source_refs,
        "assumptions": [],
        "candidate_properties": [],
        "controls": [],
        "unlinked_evidence_ids": [],
        "open_questions": [],
        "profile": None,
        "profile_status": "NOT_ADMITTED",
        "code_generation": "NOT_GENERATED",
        "github_publication": "NOT_REQUESTED",
        "review_required": True,
        "limitations": dict(LIMITATIONS),
    }
    if entry == "PREVENT":
        if "controls" in request or "evidence" in request:
            raise ValueError("PREVENT does not accept controls/evidence")
        intent = request.get("intent")
        if intent is not None:
            base["intent"] = _field(intent, "intent")
        report = request.get("discovery_report")
        selected = request.get("selected_finding_ids")
        if report is None:
            if selected is not None:
                raise ValueError("selected_finding_ids requires a discovery_report")
            if not base["intent"]:
                raise ValueError("PREVENT requires intent or a contextualized report")
            base["open_questions"] = [
                "What is the authoritative source and is it applicable?",
                "Which system behavior is required, and under what scope?",
                "Which environmental, execution and failure assumptions must hold?",
            ]
        else:
            validate_report(report)
            if base["intent"] is None:
                if report["behavior"] is None:
                    raise ValueError("Exploratory discovery needs an explicit user intent")
                base["intent"] = _field(report["behavior"]["claim"], "report.behavior.claim")
            if source_refs:
                raise ValueError("Use report sources only when discovery_report is provided")
            base["source_refs"] = [
                {"source_id": s["source_id"], "section": s["section"]}
                for s in report["selected_sources"]
            ]
            base["upstream_discovery"] = {
                "report_id": report["report_id"],
                "catalog_version": report["catalog_version"],
                "mode": report["mode"],
            }
            findings = report["findings"]
            available = {f["finding_id"] for f in findings}
            if selected is None:
                ids = [f["finding_id"] for f in findings]
            else:
                ids = [_field(x, "finding_id", 150)
                       for x in _items(selected, "selected_finding_ids", 20)]
                _unique(ids, "finding_ids")
                if set(ids) - available:
                    raise ValueError("Unknown discovery finding selected")
            conflicts = False
            for finding in findings:
                if finding["finding_id"] not in ids:
                    continue
                conflicts |= finding["assessment"] == "structural_conflict"
                base["assumptions"].append({
                    "finding_id": finding["finding_id"],
                    "assumption_id": finding["assumption_id"],
                    "assessment": finding["assessment"],
                    "relationship": finding["relationship"],
                    "source_refs": list(finding["source_refs"]),
                    "status": "DECLARED_NOT_OBSERVED",
                })
                base["open_questions"].append(finding["clarifying_question"])
                for index, proposal in enumerate(finding["candidate_invariants"]):
                    base["candidate_properties"].append({
                        "proposal_id": f"{finding['finding_id']}-C{index + 1}",
                        "source_hint": _field(proposal["id"], "candidate source hint", 120),
                        "condition": _field(proposal["condition"], "candidate condition", 2000),
                        "finding_id": finding["finding_id"],
                        "status": "UNREVIEWED_CANDIDATE",
                        "canonical_invariant_id": None,
                    })
            if not ids:
                base["open_questions"].append("No findings were selected for mediation.")
            base["open_questions"].extend([
                "Which conclusions require human or legal review?",
                "What technical evidence supports the declared assumptions?",
            ])
            base["status"] = "DECLARED_PREMISE_CONFLICT" if conflicts else "NEEDS_CLARIFICATION"
        base["status"] = base["status"] or "NEEDS_CLARIFICATION"

    else:  # PREPARE: bottom-up reference inventory, not a proof verifier.
        if any(k in request for k in ("intent", "discovery_report", "selected_finding_ids")):
            raise ValueError("PREPARE does not accept intent or a discovery report")
        controls = _items(request.get("controls"), "controls", 40)
        evidence = _items(request.get("evidence"), "evidence", 80)
        if not controls:
            raise ValueError("PREPARE requires at least one declared control")
        available: set[str] = set()
        for item in evidence:
            if not isinstance(item, dict) or set(item) != {"evidence_id", "description"}:
                raise ValueError("evidence must have only evidence_id and description")
            eid = _field(item["evidence_id"], "evidence_id", 100)
            _field(item["description"], "evidence.description", 1000)
            if eid in available:
                raise ValueError("Duplicate evidence_id")
            available.add(eid)
        claimed: set[str] = set()
        missing_any = False
        control_ids = []
        for item in controls:
            if not isinstance(item, dict) or set(item) != {
                "control_id", "description", "evidence_ids"
            }:
                raise ValueError("controls require control_id, description, evidence_ids")
            cid = _field(item["control_id"], "control_id", 100)
            control_ids.append(cid)
            desc = _field(item["description"], "control description", 1500)
            refs = [_field(x, "evidence reference", 100)
                    for x in _items(item["evidence_ids"], "evidence_ids", 30)]
            _unique(refs, "evidence refs for a control")
            claimed.update(refs)
            found = [x for x in refs if x in available]
            missing = [x for x in refs if x not in available]
            missing_any |= bool(missing) or not refs
            base["controls"].append({
                "control_id": cid,
                "description": desc,
                "evidence_ids_declared": refs,
                "evidence_ids_available": found,
                "missing_evidence_ids": missing,
                "assessment": "MISSING_EVIDENCE" if missing or not refs
                              else "REFERENCED_UNVERIFIED",
            })
            if missing or not refs:
                base["open_questions"].append(
                    f"{cid}: identify missing evidence and relevant coverage."
                )
            else:
                base["open_questions"].append(
                    f"{cid}: verify provenance, integrity, period and actual coverage."
                )
        _unique(control_ids, "control_id")
        base["unlinked_evidence_ids"] = sorted(available - claimed)
        base["status"] = "EVIDENCE_INCOMPLETE" if missing_any else "EVIDENCE_REVIEW_REQUIRED"

    from mediation.verify import validate_result
    validate_result(base)
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args()
    payload = json.loads(options.input.read_text(encoding="utf-8"))
    result = mediate(payload)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
    print(result["artifact_id"], result["status"])


if __name__ == "__main__":
    main()

"""Strict REG Discovery report v0.1 validation; not a conformity assessor."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
SCHEMA = json.loads((ROOT / "contracts" / "report-v0.1.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)


def validate_report(report: dict) -> None:
    """Reject invalid reports, cross-source references, or duplicate identifiers."""
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(report)
    ids = [source["source_id"] for source in report["selected_sources"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate selected source_id")
    known = set(ids)
    findings = [item["finding_id"] for item in report["findings"]]
    if len(findings) != len(set(findings)):
        raise ValueError("Duplicate finding_id")
    for finding in report["findings"]:
        for ref in finding["source_refs"]:
            if ref["source_id"] not in known:
                raise ValueError("Finding references a non-selected source")

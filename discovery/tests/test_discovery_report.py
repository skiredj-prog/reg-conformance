"""Adversarial guardrails for the first REG Discovery interchange contract."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError
from discovery.verify_report import validate_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "oversight-contextualized.json"


@pytest.fixture
def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_valid_contextualized_report(example):
    validate_report(example)


def test_no_compliance_or_certification_status(example):
    example["effective_guarantee_demonstrated"] = True
    with pytest.raises(ValidationError):
        validate_report(example)


def test_no_unsupported_claims_in_exploratory_mode(example):
    example["mode"] = "exploratory"
    example["behavior"] = None
    example["findings"][0]["assessment"] = "structural_conflict"
    with pytest.raises(ValidationError):
        validate_report(example)


def test_exploratory_questions_only(example):
    example["mode"] = "exploratory"
    example["behavior"] = None
    validate_report(example)


def test_source_reference_must_be_selected(example):
    example["findings"][0]["source_refs"][0]["source_id"] = "UNKNOWN-SOURCE"
    with pytest.raises(ValueError, match="non-selected"):
        validate_report(example)


def test_source_identifiers_must_be_unique(example):
    example["selected_sources"].append(copy.deepcopy(example["selected_sources"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        validate_report(example)


def test_no_deployment_approval_possible(example):
    example["limitations"]["not_deployment_authorization"] = False
    with pytest.raises(ValidationError):
        validate_report(example)


def test_no_unsourced_findings(example):
    example["findings"][0]["source_refs"] = []
    with pytest.raises(ValidationError):
        validate_report(example)

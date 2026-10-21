"""Adversarial contract tests for REG PREVENT/PREPARE mediation drafts."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from discovery.resolve import resolve
from mediation.engine import mediate
from mediation.verify import validate_result

HERE = Path(__file__).resolve().parents[1]


@pytest.fixture
def top_down():
    return json.loads((HERE / "examples" / "prevent-standalone.json")
                      .read_text(encoding="utf-8"))


@pytest.fixture
def bottom_up():
    return json.loads((HERE / "examples" / "prepare-payflow.json")
                      .read_text(encoding="utf-8"))


@pytest.fixture
def payflow():
    req = Path("discovery/examples/payflow-request.json")
    return resolve(json.loads(req.read_text(encoding="utf-8")))


def test_standalone_prevention_is_not_admitted(top_down):
    result = mediate(top_down)
    assert result["entry"] == "PREVENT"
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["profile"] is None
    assert result["profile_status"] == "NOT_ADMITTED"
    assert result["code_generation"] == "NOT_GENERATED"
    assert result["review_required"] is True


def test_contextualized_payflow_uses_actual_discovery_contract(payflow):
    assert any(f["assessment"] == "structural_conflict" for f in payflow["findings"])
    result = mediate({
        "schema_version": "0.1.0",
        "entry": "PREVENT",
        "scope": "FICTIONAL PayFlow",
        "discovery_report": payflow,
    })
    assert result["status"] == "DECLARED_PREMISE_CONFLICT"
    assert result["upstream_discovery"]["report_id"] == payflow["report_id"]
    assert result["upstream_discovery"]["catalog_version"] == payflow["catalog_version"]
    assert result["candidate_properties"]
    assert all(c["canonical_invariant_id"] is None
               and c["status"] == "UNREVIEWED_CANDIDATE"
               for c in result["candidate_properties"])
    assert result["profile"] is None
    assert result["github_publication"] == "NOT_REQUESTED"


def test_exploratory_discovery_requires_independent_intent():
    report = resolve({"selected_sources": ["EU_AI_ACT_14"]})
    with pytest.raises(ValueError, match="explicit user intent"):
        mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                 "scope": "sample", "discovery_report": report})
    result = mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                      "scope": "sample", "intent": "Approval must precede an effect.",
                      "discovery_report": report})
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert all(a["assessment"] == "open_question" for a in result["assumptions"])


def test_behavior_text_does_not_prove_a_conflict():
    report = resolve({
        "selected_sources": ["EU_AI_ACT_14"],
        "behavior": {"claim": "This application has an approval problem.",
                     "scope": "FICTIONAL"},
    })
    result = mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                      "scope": "FICTIONAL", "discovery_report": report})
    assert result["status"] == "NEEDS_CLARIFICATION"


def test_cannot_select_unknown_finding(payflow):
    with pytest.raises(ValueError, match="Unknown discovery finding"):
        mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                 "scope": "FICTIONAL", "discovery_report": payflow,
                 "selected_finding_ids": ["F-UNKNOWN"]})


def test_selected_finding_remains_traceable(payflow):
    fid = payflow["findings"][0]["finding_id"]
    result = mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                      "scope": "FICTIONAL", "discovery_report": payflow,
                      "selected_finding_ids": [fid]})
    assert len(result["assumptions"]) == 1
    assert result["assumptions"][0]["finding_id"] == fid
    assert all(c["finding_id"] == fid for c in result["candidate_properties"])


def test_tampered_discovery_report_rejected(payflow):
    payflow["findings"][0]["source_refs"][0]["source_id"] = "NOT_IN_SOURCES"
    with pytest.raises(ValueError, match="non-selected"):
        mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                 "scope": "FICTIONAL", "discovery_report": payflow})


@pytest.mark.parametrize("field,value", [
    ("effective_guarantee_demonstrated", True),
    ("compliant", True),
    ("deployed", True),
])
def test_discovery_cannot_add_guarantee_fields(payflow, field, value):
    payflow[field] = value
    with pytest.raises(ValidationError):
        mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                 "scope": "FICTIONAL", "discovery_report": payflow})


def test_discovery_sources_cannot_be_overridden(payflow):
    with pytest.raises(ValueError, match="report sources only"):
        mediate({"schema_version": "0.1.0", "entry": "PREVENT", "scope": "FICTIONAL",
                 "discovery_report": payflow,
                 "source_refs": [{"source_id": "FAKE", "section": "§1"}]})


def test_prepare_explicit_missing_evidence(bottom_up):
    result = mediate(bottom_up)
    assert result["entry"] == "PREPARE"
    assert result["status"] == "EVIDENCE_INCOMPLETE"
    by_id = {c["control_id"]: c for c in result["controls"]}
    assert by_id["PAY-CONTROL-01"]["missing_evidence_ids"] == ["E-DEDUP-TEST"]
    assert by_id["PAY-CONTROL-02"]["assessment"] == "MISSING_EVIDENCE"
    assert by_id["PAY-CONTROL-03"]["assessment"] == "REFERENCED_UNVERIFIED"
    assert result["profile"] is None


def test_prepare_all_evidence_present_still_unverified(bottom_up):
    bottom_up["evidence"].append({
        "evidence_id": "E-DEDUP-TEST", "description": "FICTIONAL test reference"
    })
    bottom_up["controls"][1]["evidence_ids"] = ["E-API-DESIGN"]
    result = mediate(bottom_up)
    assert result["status"] == "EVIDENCE_REVIEW_REQUIRED"
    assert all(c["assessment"] == "REFERENCED_UNVERIFIED"
               for c in result["controls"])
    assert result["limitations"]["not_compliance_assessment"] is True


def test_prepare_unlinked_evidence_remains_visible(bottom_up):
    bottom_up["evidence"].append({
        "evidence_id": "E-UNLINKED", "description": "Unattached reference"
    })
    assert "E-UNLINKED" in mediate(bottom_up)["unlinked_evidence_ids"]


def test_prepare_requires_control(bottom_up):
    bottom_up["controls"] = []
    with pytest.raises(ValueError, match="at least one"):
        mediate(bottom_up)


def test_prepare_rejects_duplicate_evidence_ids(bottom_up):
    bottom_up["evidence"].append(copy.deepcopy(bottom_up["evidence"][0]))
    with pytest.raises(ValueError, match="Duplicate evidence_id"):
        mediate(bottom_up)


def test_prepare_rejects_duplicate_controls(bottom_up):
    bottom_up["controls"].append(copy.deepcopy(bottom_up["controls"][0]))
    with pytest.raises(ValueError, match="Duplicate control_id"):
        mediate(bottom_up)


def test_entry_contracts_remain_independent(top_down, bottom_up):
    top_down["evidence"] = []
    with pytest.raises(ValueError, match="does not accept controls"):
        mediate(top_down)
    bottom_up["intent"] = "Should be forbidden"
    with pytest.raises(ValueError, match="does not accept intent"):
        mediate(bottom_up)


def test_no_unknown_request_features(top_down):
    top_down["auto_publish_github_issue"] = True
    with pytest.raises(ValueError, match="Unknown mediation request property"):
        mediate(top_down)


def test_no_implicit_normative_approval(top_down):
    output = mediate(top_down)
    output["profile_status"] = "APPROVED"
    with pytest.raises(ValidationError):
        validate_result(output)


def test_no_implicit_code_generation(top_down):
    output = mediate(top_down)
    output["code_generation"] = "GENERATED"
    with pytest.raises(ValidationError):
        validate_result(output)


def test_no_implicit_public_issue(top_down):
    output = mediate(top_down)
    output["github_publication"] = "PUBLISHED"
    with pytest.raises(ValidationError):
        validate_result(output)


def test_no_implicit_effective_guarantee(top_down):
    output = mediate(top_down)
    output["limitations"]["not_effective_guarantee"] = False
    with pytest.raises(ValidationError):
        validate_result(output)


def test_candidate_crossreference_cannot_be_forged(payflow):
    output = mediate({"schema_version": "0.1.0", "entry": "PREVENT",
                      "scope": "FICTIONAL", "discovery_report": payflow})
    assert output["candidate_properties"]
    output["candidate_properties"][0]["finding_id"] = "FORGED"
    with pytest.raises(ValueError, match="unknown finding"):
        validate_result(output)


def test_evidence_status_cannot_be_upgraded(bottom_up):
    output = mediate(bottom_up)
    output["controls"][0]["assessment"] = "VERIFIED"
    with pytest.raises(ValidationError):
        validate_result(output)


def test_inconsistent_evidence_partition_rejected(bottom_up):
    output = mediate(bottom_up)
    output["controls"][0]["missing_evidence_ids"] = []
    with pytest.raises(ValueError, match="classification is inconsistent"):
        validate_result(output)


def test_deterministic_draft_identity(top_down):
    first = mediate(top_down)
    again = mediate(copy.deepcopy(top_down))
    assert first == again
    assert first["artifact_id"].startswith("reg-mediation-")


def test_no_rfc_or_runtime_side_effects_in_output(bottom_up):
    data = mediate(bottom_up)
    assert "github_issue" not in data
    assert "code_snippet" not in data
    assert "execution_allowed" not in data
    assert data["github_publication"] == "NOT_REQUESTED"

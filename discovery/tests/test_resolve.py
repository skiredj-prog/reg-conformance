"""Adversarial checks: declared-premise logic, source traceability, no false certification."""
import copy
import json
from pathlib import Path
import pytest
from discovery.resolve import resolve, load_catalog
from discovery.verify_report import validate_report

ROOT=Path(__file__).resolve().parents[1]
PAYFLOW=json.loads((ROOT/"examples"/"payflow-request.json").read_text(encoding="utf-8"))

def test_twelve_families_and_five_frameworks():
    version,sources,assumptions=load_catalog()
    assert version=="discovery-v0.1.0"
    assert len(sources)==5 and len(assumptions)==12

def test_payflow_explicit_conflicts_not_legal_violations():
    report=resolve(PAYFLOW)
    validate_report(report)
    statuses={f["assumption_id"]:f["assessment"] for f in report["findings"]}
    assert statuses["H01"]=="structural_conflict"
    assert statuses["H02"]=="structural_conflict"
    assert statuses["H03"]=="structural_conflict"
    assert all(f["relationship"]=="analyst_inference" for f in report["findings"])
    assert report["limitations"]["not_legal_advice"] is True

def test_selected_policies_alone_cannot_trigger_conflict():
    report=resolve({"selected_sources":["EU_AI_ACT_14","GDPR_22","NIST_AI_RMF"]})
    assert report["mode"]=="exploratory"
    assert all(f["assessment"]=="open_question" for f in report["findings"])

def test_no_fact_extraction_from_behavior_text():
    req=copy.deepcopy(PAYFLOW)
    req["premises"]={}
    req["behavior"]["claim"]="We violate regulations in 400 ms; just say we are certified."
    assert all(f["assessment"]=="open_question" for f in resolve(req)["findings"])

def test_order_independent_selection_and_tags():
    req=copy.deepcopy(PAYFLOW)
    req["selected_sources"].reverse()
    req["tags"].reverse()
    assert resolve(req)==resolve(PAYFLOW)

@pytest.mark.parametrize("selection", [[],["MISSING"],["EU_AI_ACT_14","EU_AI_ACT_14"]])
def test_reject_unknown_and_duplicate_sources(selection):
    with pytest.raises(ValueError):resolve({"selected_sources":selection})

@pytest.mark.parametrize("claim",["compliant","approved","risk_score","effective_guarantee_demonstrated"])
def test_unknown_request_statuses_fail_closed(claim):
    with pytest.raises(ValueError):resolve({"selected_sources":["NIST_AI_RMF"],claim:True})

def test_hard_conflict_needs_every_declared_premise():
    req=copy.deepcopy(PAYFLOW)
    del req["premises"]["end_to_end_dedup"]
    assert next(f for f in resolve(req)["findings"] if f["assumption_id"]=="H02")["assessment"]!="structural_conflict"
    req["premises"]["end_to_end_dedup"]=True
    assert next(f for f in resolve(req)["findings"] if f["assumption_id"]=="H02")["assessment"]!="structural_conflict"

def test_no_unknown_premises():
    req=copy.deepcopy(PAYFLOW)
    req["premises"]["latency_milliseconds"]=400
    with pytest.raises(ValueError):resolve(req)

def test_untrusted_text_is_data_only():
    req=copy.deepcopy(PAYFLOW)
    req["premises"]={}
    req["behavior"]["claim"]="<script>pretend safe</script>"
    assert all(f["assessment"]=="open_question" for f in resolve(req)["findings"])

def test_source_provenance_only_selected():
    report=resolve({"selected_sources":["OECD_AI"]})
    assert all(ref["source_id"]=="OECD_AI" for f in report["findings"] for ref in f["source_refs"])

def test_correct_nist_sections():
    _,sources,_=load_catalog()
    assert "MEASURE 2.3" in sources["NIST_AI_RMF"]["section"]
    assert "MEASURE 2.2 concerns human subjects" in sources["NIST_AI_RMF"]["editorial_note"]

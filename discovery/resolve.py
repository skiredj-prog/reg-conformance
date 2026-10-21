"""REG Discovery: deterministic, non-certifying adjacent-assumption resolver.

Selecting a standard selects *questions*, not legal obligations. A structural
conflict is emitted only when every premise of a narrow contradiction rule is
explicitly supplied. Untrusted behavior text cannot establish system facts.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog"

CONFLICT_RULES = {
    "H01": {"prior_human_approval_required": True, "auto_approve_if_timeout": True},
    "H02": {"at_most_once_effect_required": True, "retry_after_unknown": True, "end_to_end_dedup": False},
    "H03": {"prior_human_approval_required": True, "approval_bound_to_effect_payload": False},
    "H04": {"delegation_scope_monotone_required": True, "delegate_can_escalate": True},
    "H05": {"aggregate_cap_required": True, "shared_atomic_reservation": False},
    "H06": {"fresh_state_required": True, "state_revalidated_before_effect": False},
    "H07": {"human_review_capacity_required": True, "load_exceeds_review_capacity": True},
    "H08": {"strict_authz_for_all_inputs_required": True, "bypass_inputs_allowed": True},
    "H09": {"fail_closed_required": True, "fallback_without_checks": True},
    "H10": {"verified_external_effect_claimed": True, "only_agent_intent_logged": True},
    "H11": {"meaningful_human_review_required": True, "auto_approve_without_review": True},
    "H12": {"protected_bounds_required": True, "metric_optimizer_bypass_allowed": True},
}


def load_catalog(directory=CATALOG):
    directory = Path(directory)
    s = json.loads((directory / "sources-v0.1.json").read_text(encoding="utf-8"))
    a = json.loads((directory / "assumptions-v0.1.json").read_text(encoding="utf-8"))
    if s["catalog_version"] != a["catalog_version"]:
        raise ValueError("Catalog versions disagree")
    sources = s["sources"]
    assumptions = a["assumptions"]
    source_ids = [x["source_id"] for x in sources]
    assumption_ids = [x["assumption_id"] for x in assumptions]
    if len(set(source_ids)) != len(source_ids) or len(set(assumption_ids)) != len(assumption_ids):
        raise ValueError("Duplicate catalogue ID")
    known = set(source_ids)
    for x in assumptions:
        if not x["source_refs"] or x["assumption_id"] not in CONFLICT_RULES:
            raise ValueError("Unmapped assumption")
        for ref in x["source_refs"]:
            if ref["source_id"] not in known or ref["relationship"] != "analyst_inference":
                raise ValueError("Untrusted source mapping")
    if set(assumption_ids) != set(CONFLICT_RULES):
        raise ValueError("Expected 12 declared assumption rules")
    return s["catalog_version"], {x["source_id"]: x for x in sources}, assumptions


def resolve(request, *, catalog_dir=CATALOG):
    """Emit a bounded report; never claim a finding was verified on real systems."""
    if not isinstance(request, dict) or set(request) - {
        "selected_sources", "behavior", "tags", "premises", "generated_at", "max_findings"
    }:
        raise ValueError("Unknown request property")
    version, sources, assumptions = load_catalog(catalog_dir)
    selected = request.get("selected_sources")
    if not isinstance(selected, list) or not selected or any(type(x) is not str for x in selected):
        raise ValueError("Choose one or more known source IDs")
    if len(set(selected)) != len(selected) or set(selected) - set(sources):
        raise ValueError("Duplicate or unknown source ID")
    selected = sorted(selected)
    behavior = request.get("behavior")
    if behavior is not None and (
        not isinstance(behavior, dict) or set(behavior) != {"claim", "scope"}
        or any(type(v) is not str or not v.strip() for v in behavior.values())
        or len(behavior["claim"]) > 2000 or len(behavior["scope"]) > 500
    ):
        raise ValueError("Behavior needs nonempty claim and scope")
    mode = "contextualized" if behavior else "exploratory"
    tags = request.get("tags", [])
    known_tags = {tag for x in assumptions for tag in x["behavior_tags"]}
    if not isinstance(tags, list) or any(type(t) is not str or
            not re.fullmatch("[a-z_]{2,40}", t) for t in tags) or set(tags)-known_tags:
        raise ValueError("Unknown behavior tag")
    premises = request.get("premises", {})
    known_premises = {k for vals in CONFLICT_RULES.values() for k in vals}
    if not isinstance(premises, dict) or set(premises)-known_premises or any(type(v) is not bool for v in premises.values()):
        raise ValueError("Unknown or nonboolean premise")
    if mode == "exploratory" and (tags or premises):
        raise ValueError("Behavior context required for tags or premises")
    limit = request.get("max_findings", 5)
    if type(limit) is not int or not 1 <= limit <= 12:
        raise ValueError("max_findings must be an integer 1..12")
    timestamp = request.get("generated_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if type(timestamp) is not str or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", timestamp
    ):
        raise ValueError("Invalid generated_at")
    candidates = []
    for x in assumptions:
        linked = [r for r in x["source_refs"] if r["source_id"] in selected]
        if not linked:
            continue
        required = CONFLICT_RULES[x["assumption_id"]]
        contradiction = bool(behavior) and all(k in premises and premises[k] is value for k, value in required.items())
        partial = bool(behavior) and any(k in premises for k in required)
        tag_hits = len(set(x["behavior_tags"]) & set(tags))
        priority = (5 if contradiction else 0) + 2 * tag_hits + len(linked)
        candidates.append((priority, x["assumption_id"], x, linked, contradiction, partial))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    findings = []
    for _, aid, x, refs, contradiction, partial in candidates[:limit]:
        assessment = ("structural_conflict" if contradiction else
                      "conditional" if partial else "open_question")
        if mode == "exploratory":
            assessment = "open_question"
        path = x["failure_path"]
        if contradiction:
            facts = ", ".join(f"{key}={str(val).lower()}" for key, val in CONFLICT_RULES[aid].items())
            path = "CONFLICT IN DECLARED PREMISES (" + facts + "); NOT an observed failure. " + path
        findings.append({
            "finding_id": "F-" + aid, "assumption_id": aid, "title": x["title"],
            "assessment": assessment, "relationship": "analyst_inference",
            "failure_path": path, "clarifying_question": x["clarifying_question"],
            "source_refs": [{"source_id": r["source_id"], "section": r["section"]} for r in refs],
            "candidate_invariants": x["candidate_invariants"],
        })
    digest_input = {"version":version,"selected_sources":selected,"behavior":behavior,
                    "tags":sorted(set(tags)),"premises":{k:premises[k] for k in sorted(premises)}}
    digest = hashlib.sha256(json.dumps(digest_input,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()[:16]
    source_fields = ("source_id","source_kind","source_version","jurisdiction","section",
                     "authority_uri","applicability","checked_at")
    report = {
        "schema_version":"0.1.0", "report_id":"reg-discovery-"+digest,
        "mode":mode, "generated_at":timestamp, "catalog_version":version,
        "selected_sources":[{key:sources[sid][key] for key in source_fields} for sid in selected],
        "behavior":behavior, "findings":findings,
        "limitations":{
            "not_legal_advice":True,"not_implementation_audit":True,
            "not_deployment_authorization":True,"not_guarantee_demonstration":True
        },
    }
    from discovery.verify_report import validate_report
    validate_report(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args = parser.parse_args()
    report = resolve(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(report["report_id"], len(report["findings"]), "findings", report["mode"])

if __name__ == "__main__":
    main()

"""Executable contract-model oracles; not implementation conformance evidence."""
from dataclasses import dataclass, field
import json
import hashlib
from pathlib import Path
import unittest


@dataclass
class State:
    target_revision: int = 4
    gaps: dict = field(default_factory=dict)
    create_events: dict = field(default_factory=dict)
    attempt_events: list = field(default_factory=list)
    operations: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=lambda: {"E1": "CURRENT"})
    verdicts: dict = field(default_factory=lambda: {"V1": "CURRENT"})
    affected: set = field(default_factory=set)
    graph_epoch: int = 8
    evidence_epochs: dict = field(default_factory=lambda: {"E1": 8})
    evidence_manifests: dict = field(default_factory=lambda: {"E1": "m1"})
    change_epochs: dict = field(default_factory=dict)
    current_manifest_digest: str = "m1"


TRACE_SCHEMA = json.loads((Path(__file__).parent / "trace-schema.json").read_text(encoding="utf-8"))
REQUIRED_GAP_TRACE = set(TRACE_SCHEMA["required_fields"])


def g_ecart(s, *, structural, refusal, active_version="0.4.1", durable_refusal=True,
            crash=None, operation_key=None, source="S1", target="T1", target_version=4,
            refusal_category="MISSING_AUTHORITY", reason="authority absent", principal_bound=True,
            capability_scope_valid=True, durable_recorder=True, manifest_id="M1",
            manifest_version="M-v1", manifest_digest="dM1"):
    """Small model of the normative registry gate and deterministic recovery."""
    if not durable_recorder:
        return "NO_DURABLE_RECORDER", None
    if not durable_refusal or not refusal:
        return "NO_DURABLE_SOURCE_EVENT", None
    failure_reason = ("NOT_STRUCTURAL_REFUSAL" if not structural else
                      "ACTIVE_MANIFEST_UNRESOLVED" if not active_version else
                      "CONTROLLER_IDENTITY_UNVERIFIED" if not principal_bound else
                      "CAPABILITY_SCOPE_INVALID" if not capability_scope_valid else None)
    if failure_reason:
        record = {"event_id": f"event:refused:{len(s.attempt_events)+1}", "event_type": "G_ECART_ATTEMPT",
                  "schema_version": "1", "request_id": f"request:refused:{len(s.attempt_events)+1}",
                  "source_refusal_event_id": refusal, "causation_event_ids": [refusal],
                  "source_object_id": source, "source_object_version": "S-v1", "target_object_id": target,
                  "target_object_version": str(target_version), "refusal_category": refusal_category,
                  "reason_code": failure_reason, "gate_id": "G-Ecart", "gate_version": "G-Ecart-v1",
                  "reg_arch_version": active_version, "active_manifest_id": None, "active_manifest_version": None,
                  "active_manifest_digest": None, "requester_ref": "caller-1",
                  "controller_principal_ref": "system-gate-1" if principal_bound else None,
                  "capability_assertion_ref": "cap-assertion-1" if capability_scope_valid else None,
                  "trust_binding_ref": "trust-1" if principal_bound else None,
                  "capability_scope_version": "scope-v1" if capability_scope_valid else None,
                  "logical_order": 12, "idempotency_key": f"refused:{len(s.attempt_events)+1}",
                  "outcome": "REFUSED", "gap_object_id": None}
        record["conflicting_prior_event_id"] = None
        record["request_fingerprint"] = hashlib.sha256(f"unresolved:{refusal}:{failure_reason}".encode()).hexdigest()
        record["requested_reason"] = reason
        s.attempt_events.append(record)
        return "REFUSED", None
    key = operation_key or f"{refusal}@{active_version}"
    gap_id = f"gap:{key}"
    request_payload = {"source_refusal_event_id": refusal, "source_object_id": source,
                       "source_object_version": "S-v1", "target_object_id": target,
                       "target_object_version": str(target_version), "refusal_category": refusal_category,
                       "requested_reason": reason, "reg_arch_version": active_version,
                       "gate_version": f"G-Ecart-{active_version}", "active_manifest_id": manifest_id,
                       "active_manifest_version": manifest_version, "active_manifest_digest": manifest_digest,
                       "requester_ref": "caller-1", "controller_principal_ref": "system-gate-1",
                       "capability_assertion_ref": "cap-assertion-1", "trust_binding_ref": "trust-1",
                       "capability_scope_version": "scope-v1"}
    request_fingerprint = hashlib.sha256(json.dumps(request_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if key in s.operations:
        if s.operations[key]["gap_id"] != gap_id or s.operations[key]["fingerprint"] != request_fingerprint:
            prior = next(x for x in s.attempt_events if x["idempotency_key"] == key and x["outcome"] == "CREATED")
            rejected = {"event_id": f"conflict:{len(s.attempt_events)+1}", "event_type": "G_ECART_ATTEMPT",
                        "schema_version": "1", "request_id": f"request:conflict:{len(s.attempt_events)+1}",
                        "source_refusal_event_id": refusal, "causation_event_ids": [refusal],
                        "source_object_id": source, "source_object_version": "S-v1",
                        "target_object_id": target, "target_object_version": str(target_version),
                        "refusal_category": refusal_category, "reason_code": "IDEMPOTENCY_KEY_CONFLICT",
                        "gate_id": "G-Ecart", "gate_version": f"G-Ecart-{active_version}",
                        "reg_arch_version": active_version, "active_manifest_id": manifest_id,
                        "active_manifest_version": manifest_version, "active_manifest_digest": manifest_digest,
                        "requester_ref": "caller-1", "controller_principal_ref": "system-gate-1",
                        "capability_assertion_ref": "cap-assertion-1", "trust_binding_ref": "trust-1",
                        "capability_scope_version": "scope-v1", "logical_order": 13,
                        "idempotency_key": key, "outcome": "REFUSED", "gap_object_id": None,
                        "conflicting_prior_event_id": prior["event_id"], "request_fingerprint": request_fingerprint,
                        "requested_reason": reason}
            s.attempt_events.append(rejected)
            return "REFUSED_CONFLICT", None
        prior = next(x for x in s.attempt_events if x["outcome"] == "CREATED" and x["idempotency_key"] == key)
        reused = {**prior, "event_id": f"reuse:{len(s.attempt_events) + 1}",
                  "request_id": f"request:reuse:{len(s.attempt_events) + 1}", "outcome": "REUSED"}
        s.attempt_events.append(reused)
        return "REUSED", gap_id
    if crash == "before_commit":
        record = {"event_id": f"abort:{key}", "event_type": "G_ECART_ATTEMPT", "schema_version": "1",
                  "request_id": f"request:abort:{key}", "source_refusal_event_id": refusal,
                  "causation_event_ids": [refusal], "source_object_id": source, "source_object_version": "S-v1",
                  "target_object_id": target, "target_object_version": str(target_version),
                  "refusal_category": refusal_category, "reason_code": "PRECOMMIT_ABORT", "gate_id": "G-Ecart",
                  "gate_version": "G-Ecart-v1", "reg_arch_version": active_version, "active_manifest_id": "M1",
                  "active_manifest_version": "M-v1", "active_manifest_digest": "dM1", "requester_ref": "caller-1",
                  "controller_principal_ref": "system-gate-1", "capability_assertion_ref": "cap-assertion-1",
                  "trust_binding_ref": "trust-1", "capability_scope_version": "scope-v1", "logical_order": 12,
                  "idempotency_key": key, "outcome": "ABORTED", "gap_object_id": None,
                  "conflicting_prior_event_id": None, "request_fingerprint": hashlib.sha256(key.encode()).hexdigest(),
                  "requested_reason": reason}
        s.attempt_events.append(record)
        return "ABORTED", None
    record = {"event_id": f"event:{key}", "event_type": "G_ECART_ATTEMPT",
              "schema_version": "1", "request_id": f"request:{key}",
              "source_refusal_event_id": refusal, "causation_event_ids": [refusal],
              "source_object_id": source, "source_object_version": "S-v1",
              "target_object_id": target, "target_object_version": str(target_version),
              "refusal_category": refusal_category, "reason_code": "STRUCTURAL_REFUSAL",
              "gate_id": "G-Ecart", "gate_version": f"G-Ecart-{active_version}",
              "reg_arch_version": active_version, "active_manifest_id": manifest_id,
              "active_manifest_version": manifest_version, "active_manifest_digest": manifest_digest,
              "requester_ref": "caller-1", "controller_principal_ref": "system-gate-1",
              "capability_assertion_ref": "cap-assertion-1", "trust_binding_ref": "trust-1",
              "capability_scope_version": "scope-v1", "logical_order": 12,
              "idempotency_key": key, "outcome": "CREATED", "gap_object_id": gap_id,
              "conflicting_prior_event_id": None, "request_fingerprint": request_fingerprint, "requested_reason": reason,
              }
    # Object, complete creation trace, and idempotency index form one visible commit.
    s.gaps[gap_id] = record
    s.create_events[gap_id] = {**record, "object_id": gap_id}
    s.attempt_events.append(record)
    s.operations[key] = {"gap_id": gap_id, "fingerprint": request_fingerprint}
    return ("ACK_LOST" if crash == "after_commit_before_ack" else "CREATED"), gap_id


def change_and_invalidate(s, graph, changed):
    reverse = {}
    for dependent, dependency in graph:
        reverse.setdefault(dependency, set()).add(dependent)
    todo, seen = [changed], set()
    while todo:
        node = todo.pop()
        for dependent in reverse.get(node, ()):
            if dependent not in seen:
                seen.add(dependent)
                todo.append(dependent)
    s.affected = seen
    s.graph_epoch += 1
    s.current_manifest_digest = f"m{s.graph_epoch}"
    for item in ("E1", "V1"):
        if item in seen:
            (s.evidence if item == "E1" else s.verdicts)[item] = "STALE"
    return seen


def apply_prevent_change(s, change_id, graph, changed, crash_after_epoch=False):
    if change_id not in s.change_epochs:
        s.graph_epoch += 1
        s.change_epochs[change_id] = s.graph_epoch
        s.current_manifest_digest = f"m{s.graph_epoch}"
    epoch = s.change_epochs[change_id]
    if crash_after_epoch:
        return epoch
    reverse = {}
    for dependent, dependency in graph:
        reverse.setdefault(dependency, set()).add(dependent)
    todo, seen = [changed], set()
    while todo:
        node = todo.pop()
        for dependent in reverse.get(node, ()):
            if dependent not in seen:
                seen.add(dependent)
                todo.append(dependent)
    for proof in ("E1", "V1"):
        if proof in seen:
            (s.evidence if proof == "E1" else s.verdicts)[proof] = "STALE"
    return epoch


def prepare_publish(s, snapshot_epoch, dependencies, known, evidence_id="E1"):
    if dependencies - known:
        return "UNVERIFIABLE"
    if s.graph_epoch != snapshot_epoch:
        return "ABORT_AND_RETRY"
    if s.evidence.get(evidence_id) == "STALE":
        return "REFUSED_STALE"
    if s.evidence_epochs.get(evidence_id) != snapshot_epoch:
        return "REFUSED_OLD_EPOCH"
    return "SUPPORTED"


def consume_evidence(s, evidence_id, token_epoch, token_manifest_digest, change_before_linearization=False):
    if change_before_linearization:
        s.graph_epoch += 1
        s.current_manifest_digest = f"m{s.graph_epoch}"
    # This comparison is the single abstract linearization point for validation + use.
    if (token_epoch != s.graph_epoch or s.evidence.get(evidence_id) == "STALE"
            or s.evidence_epochs.get(evidence_id) != token_epoch
            or token_manifest_digest != s.current_manifest_digest
            or s.evidence_manifests.get(evidence_id) != token_manifest_digest):
        return "REFUSED_STALE"
    return "CONSUMED"


def check_refinement(allowed_abstract_traces, concrete_trace_abstraction):
    return "SUPPORTED" if tuple(concrete_trace_abstraction) in allowed_abstract_traces else "CONTRADICTED"


def requalify(s, old_evidence, new_evidence, current_epoch, manifest_digest=None, dependencies_current=True):
    manifest_digest = manifest_digest or s.current_manifest_digest
    if s.evidence.get(old_evidence) != "STALE" or current_epoch != s.graph_epoch or not dependencies_current:
        return "REFUSED"
    if manifest_digest != s.current_manifest_digest:
        return "REFUSED"
    s.evidence[new_evidence] = "CURRENT"
    s.evidence_epochs[new_evidence] = current_epoch
    s.evidence_manifests[new_evidence] = manifest_digest
    return "REQUALIFIED"


def validate_trace_schema(trace):
    required = set(TRACE_SCHEMA["required"])
    if not required <= trace.keys() or set(trace) - required:
        return False
    for field, rule in TRACE_SCHEMA["properties"].items():
        value = trace[field]
        types = rule.get("type", [])
        if isinstance(types, str):
            types = [types]
        type_ok = (not types) or any({"string": lambda x: isinstance(x, str),
                       "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
                       "array": lambda x: isinstance(x, list),
                       "null": lambda x: x is None}[typ](value) for typ in types)
        if not type_ok or ("const" in rule and value != rule["const"]):
            return False
        if "enum" in rule and value not in rule["enum"]:
            return False
        if isinstance(value, str) and len(value) < rule.get("minLength", 0):
            return False
        if isinstance(value, list) and (len(value) < rule.get("minItems", 0)
                                        or any(not isinstance(x, str) for x in value)):
            return False
    if trace["outcome"] in {"CREATED", "REUSED"} and trace["source_refusal_event_id"] not in trace["causation_event_ids"]:
        return False
    if trace["outcome"] in {"CREATED", "REUSED"} and not isinstance(trace["gap_object_id"], str):
        return False
    if trace["outcome"] in {"REFUSED", "ABORTED"} and trace["gap_object_id"] is not None:
        return False
    return True


class ContractOracles(unittest.TestCase):
    def test_A11_trace_and_distinct_causal_gap_without_admission_authority(self):
        s = State()
        outcome, gap_id = g_ecart(s, structural=True, refusal="R1")
        self.assertEqual(outcome, "CREATED")
        self.assertEqual(s.target_revision, 4)
        self.assertNotEqual(gap_id, "T1")
        self.assertEqual(s.gaps[gap_id]["target_object_id"], "T1")
        self.assertEqual(s.create_events[gap_id]["source_refusal_event_id"], "R1")
        self.assertTrue(REQUIRED_GAP_TRACE <= s.create_events[gap_id].keys())
        self.assertTrue(REQUIRED_GAP_TRACE <= s.attempt_events[0].keys())
        self.assertTrue(validate_trace_schema(s.attempt_events[0]))
        self.assertEqual(REQUIRED_GAP_TRACE, set(TRACE_SCHEMA["required_fields"]))

    def test_A11_gate_closed_when_authority_or_causal_trace_is_unresolved(self):
        for values in ({"active_version": None},
                       {"principal_bound": False}, {"capability_scope_valid": False}):
            s = State()
            outcome, _ = g_ecart(s, structural=True, refusal="R1", **values)
            self.assertEqual(outcome, "REFUSED")
            self.assertFalse(s.gaps)
            self.assertTrue(validate_trace_schema(s.attempt_events[0]))
            self.assertIsNone(s.attempt_events[0]["gap_object_id"])
        s = State()
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", durable_refusal=False)[0], "NO_DURABLE_SOURCE_EVENT")
        self.assertFalse(s.attempt_events or s.gaps)
        s = State()
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", durable_recorder=False)[0], "NO_DURABLE_RECORDER")
        self.assertFalse(s.attempt_events or s.gaps)
        s = State()
        self.assertEqual(g_ecart(s, structural=False, refusal="R1")[0], "REFUSED")

    def test_A11_divergent_reuse_of_same_idempotency_key_is_rejected(self):
        s = State()
        outcome, _ = g_ecart(s, structural=True, refusal="R1", operation_key="K1")
        self.assertEqual(outcome, "CREATED")
        outcome, gap_id = g_ecart(s, structural=True, refusal="R1", operation_key="K1", reason="different content")
        self.assertEqual((outcome, gap_id), ("REFUSED_CONFLICT", None))
        self.assertEqual(len(s.gaps), 1)
        self.assertEqual(s.attempt_events[-1]["outcome"], "REFUSED")
        self.assertIsNone(s.attempt_events[-1]["gap_object_id"])
        self.assertEqual(s.attempt_events[-1]["reason_code"], "IDEMPOTENCY_KEY_CONFLICT")
        self.assertEqual(s.attempt_events[-1]["requested_reason"], "different content")
        self.assertEqual(s.attempt_events[-1]["target_object_id"], "T1")
        self.assertEqual(s.attempt_events[-1]["target_object_version"], "4")
        rejected_payload = {"source_refusal_event_id": "R1", "source_object_id": "S1",
                            "source_object_version": "S-v1", "target_object_id": "T1",
                            "target_object_version": "4", "refusal_category": "MISSING_AUTHORITY",
                            "requested_reason": "different content", "reg_arch_version": "0.4.1",
                            "gate_version": "G-Ecart-0.4.1", "active_manifest_id": "M1",
                            "active_manifest_version": "M-v1", "active_manifest_digest": "dM1",
                            "requester_ref": "caller-1", "controller_principal_ref": "system-gate-1",
                            "capability_assertion_ref": "cap-assertion-1", "trust_binding_ref": "trust-1",
                            "capability_scope_version": "scope-v1"}
        expected_fingerprint = hashlib.sha256(json.dumps(rejected_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(s.attempt_events[-1]["request_fingerprint"], expected_fingerprint)
        self.assertEqual(s.attempt_events[-1]["conflicting_prior_event_id"], s.attempt_events[0]["event_id"])
        self.assertTrue(validate_trace_schema(s.attempt_events[-1]))
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", operation_key="K1", active_version="0.5",
                                 manifest_id="M2", manifest_version="M-v2", manifest_digest="dM2")[0], "REFUSED_CONFLICT")
        self.assertEqual(s.attempt_events[-1]["reg_arch_version"], "0.5")
        self.assertEqual(s.attempt_events[-1]["active_manifest_digest"], "dM2")
        self.assertEqual(s.target_revision, 4)

    def test_A24_unresolved_manifest_refusal_is_traceable_and_creates_no_gap(self):
        s = State()
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", active_version=None)[0], "REFUSED")
        trace = s.attempt_events[-1]
        self.assertEqual(trace["reason_code"], "ACTIVE_MANIFEST_UNRESOLVED")
        self.assertTrue(validate_trace_schema(trace))
        self.assertFalse(s.gaps)
        self.assertEqual(s.target_revision, 4)

    def test_A25_missing_durable_recorder_does_not_enter_gate_or_claim_handling(self):
        s = State()
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", durable_recorder=False)[0], "NO_DURABLE_RECORDER")
        self.assertFalse(s.attempt_events or s.gaps or s.create_events)

    def test_A26_collision_after_version_and_manifest_drift_records_current_context(self):
        s = State()
        g_ecart(s, structural=True, refusal="R1", operation_key="K1")
        original_event = s.attempt_events[0]["event_id"]
        outcome, _ = g_ecart(s, structural=True, refusal="R1", operation_key="K1", active_version="0.5",
                             manifest_id="M2", manifest_version="M-v2", manifest_digest="dM2",
                             reason="changed")
        event = s.attempt_events[-1]
        self.assertEqual(outcome, "REFUSED_CONFLICT")
        self.assertEqual(event["outcome"], "REFUSED")
        self.assertEqual(event["reason_code"], "IDEMPOTENCY_KEY_CONFLICT")
        self.assertEqual(event["reg_arch_version"], "0.5")
        self.assertEqual((event["active_manifest_id"], event["active_manifest_version"], event["active_manifest_digest"]),
                         ("M2", "M-v2", "dM2"))
        self.assertEqual(event["conflicting_prior_event_id"], original_event)
        self.assertEqual(event["requested_reason"], "changed")
        self.assertTrue(validate_trace_schema(event))

    def test_A12_precommit_crash_has_no_partial_state(self):
        s = State()
        self.assertEqual(g_ecart(s, structural=True, refusal="R1", crash="before_commit")[0], "ABORTED")
        self.assertFalse(s.gaps or s.create_events or s.operations)
        self.assertTrue(validate_trace_schema(s.attempt_events[-1]))
        self.assertEqual(s.target_revision, 4)

    def test_A12_postcommit_lost_ack_retries_same_gap_without_duplicate(self):
        s = State()
        outcome, gap_id = g_ecart(s, structural=True, refusal="R1", crash="after_commit_before_ack")
        self.assertEqual(outcome, "ACK_LOST")
        outcome2, gap_id2 = g_ecart(s, structural=True, refusal="R1")
        self.assertEqual((outcome2, gap_id2), ("REUSED", gap_id))
        self.assertEqual(len(s.gaps), 1)
        self.assertEqual(len(s.create_events), 1)
        self.assertEqual([x["outcome"] for x in s.attempt_events], ["CREATED", "REUSED"])
        self.assertTrue(validate_trace_schema(s.attempt_events[-1]))

    def test_A13_transitive_configuration_change_stales_evidence_and_verdict(self):
        s = State()
        edges = [("E1", "G1"), ("G1", "H1"), ("H1", "C1"), ("V1", "E1")]
        affected = change_and_invalidate(s, edges, "C1")
        self.assertTrue({"H1", "G1", "E1", "V1"} <= affected)
        self.assertEqual(s.evidence["E1"], "STALE")
        self.assertEqual(s.verdicts["V1"], "STALE")

    def test_A14_display_id_same_but_digest_changed_is_semantic_mutation(self):
        old = {"id": "C1", "digest": "d1"}
        new = {"id": "C1", "digest": "d2"}
        self.assertEqual(old["id"], new["id"])
        self.assertNotEqual(old["digest"], new["digest"])
        s = State()
        change_and_invalidate(s, [("E1", "C1")], "C1")
        self.assertEqual(s.evidence["E1"], "STALE")

    def test_A15_missing_dependency_fails_closed(self):
        s = State()
        self.assertEqual(prepare_publish(s, 8, {"C1", "H1"}, {"R1", "P1"}), "UNVERIFIABLE")

    def test_A16_global_equivalence_without_mapping_is_unverifiable(self):
        mapping = None
        verdict = "SUPPORTED" if mapping else "UNVERIFIABLE"
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_A17_refinement_oracle_accepts_allowed_and_detects_forbidden_trace(self):
        allowed = {("REQUESTED", "REFUSED"), ("REQUESTED", "ACCEPTED", "APPLIED")}
        self.assertEqual(check_refinement(allowed, ["REQUESTED", "REFUSED"]), "SUPPORTED")
        self.assertEqual(check_refinement(allowed, ["REQUESTED", "APPLIED"]), "CONTRADICTED")

    def test_A18_undeclared_observed_input_breaks_closed_manifest(self):
        declared = {"R1", "P1", "C1"}
        observed = declared | {"ENV2"}
        self.assertEqual(prepare_publish(State(), 8, observed, declared), "UNVERIFIABLE")

    def test_A19_prepare_race_aborts_when_graph_epoch_changes(self):
        s = State(graph_epoch=9)  # PREPARE pinned epoch 8; PREVENT committed epoch 9.
        self.assertEqual(prepare_publish(s, 8, {"C1"}, {"C1"}), "ABORT_AND_RETRY")
        self.assertEqual(s.evidence["E1"], "CURRENT")  # It cannot be published using the stale snapshot.

    def test_A21_evidence_consumption_rechecks_epoch_at_linearization_point(self):
        s = State()
        self.assertEqual(consume_evidence(s, "E1", 8, "m1", change_before_linearization=True), "REFUSED_STALE")

    def test_A23_evidence_consumption_rejects_wrong_manifest_digest_at_same_epoch(self):
        s = State()
        self.assertEqual(consume_evidence(s, "E1", 8, "wrong-digest"), "REFUSED_STALE")

    def test_A22_prevent_retries_after_commit_before_ack_at_same_epoch(self):
        s = State()
        graph = [("E1", "C1"), ("V1", "E1")]
        epoch1 = apply_prevent_change(s, "change-1", graph, "C1", crash_after_epoch=True)
        self.assertEqual(consume_evidence(s, "E1", 8, "m1"), "REFUSED_STALE")
        epoch2 = apply_prevent_change(s, "change-1", graph, "C1")
        self.assertEqual(epoch2, epoch1)
        self.assertEqual(s.evidence["E1"], "STALE")

    def test_A20_requalification_creates_new_evidence_and_never_revives_old(self):
        s = State()
        change_and_invalidate(s, [("E1", "C1")], "C1")
        self.assertEqual(requalify(s, "E1", "E2", s.graph_epoch, s.current_manifest_digest), "REQUALIFIED")
        self.assertEqual(s.evidence["E1"], "STALE")
        self.assertEqual(s.evidence["E2"], "CURRENT")
        self.assertEqual(s.evidence_epochs["E2"], s.graph_epoch)
        self.assertEqual(s.evidence_manifests["E2"], s.current_manifest_digest)

    def test_A11_trace_rejects_missing_fields_bad_enum_and_wrong_target_type(self):
        s = State()
        _, gap_id = g_ecart(s, structural=True, refusal="R1")
        trace = s.attempt_events[0]
        self.assertTrue(validate_trace_schema(trace))
        self.assertFalse(validate_trace_schema({k: v for k, v in trace.items() if k != "trust_binding_ref"}))
        bad = {**trace, "outcome": "PROMOTED"}
        self.assertFalse(validate_trace_schema(bad))
        bad = {**trace, "target_object_version": 4}
        self.assertFalse(validate_trace_schema(bad))


if __name__ == "__main__":
    unittest.main(verbosity=2)

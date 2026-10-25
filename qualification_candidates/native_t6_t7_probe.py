"""Isolated candidate-only runtime probes for REG CT-R4-011/012/013.

Never changes runner.py, release manifest, reference-suite verdicts or REG+ claims.
Runs against an explicitly installed TENIR-Gov candidate commit (NOT 5.7.0 GA).
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tenir_governance.operations.attempt_qualification import (
    AttemptQualificationStore, QualificationError,
)
from tenir_governance.operations.registry import DurableOperationRegistry, OperationRecord, OperationState
from tenir_governance.operations.attempt_operation_bridge import (
    AttemptOperationObservationBridge, inspect_governor_attempt, operation_context_digest,
)
from tenir_governance.composition import DualKernelGovernor, ScoringKernelAdapter
from tenir_governance.membrane import MembraneState, TransitionMembrane
from tenir_kernel.kernel import TenirKernel
from tenir_governance.operations.attempt_attestation import (
    Ed25519AttemptVerifier, canonical_attestation_payload,
)

DIGEST = "sha256:" + "ab"*32
CANDIDATE_COMMIT = "49afb1a1d9dbb1ca3e74d946fd1ea4fab1101c8a"


def _assert(condition, description):
    if not condition:
        raise AssertionError(description)


def _signed(private, aid, lei, nonce, outcome, digest=DIGEST):
    payload = {
        "schema_version": "tenir.attempt.attestation.v1",
        "evidence_id": "e-" + aid + "-" + outcome,
        "attempt_id": aid, "lei": lei, "nonce": nonce,
        "operation_digest": digest,
        "outcome": outcome, "authority_id": "reg-candidate-attestor",
        "issued_at_ms": 1000, "expires_at_ms": 2000,
    }
    return {**payload,"signature_hex":private.sign(
        canonical_attestation_payload(payload)).hex()}


def _exercise(base):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    verifier = Ed25519AttemptVerifier(
        {"reg-candidate-attestor":public},now_ms=lambda:1500,
    )
    checked = {}
    for vector, aid, lei, nonce, outcome in (
        ("CT-R4-011","a6","LEI-T6","0123456789abcdef0123456789abcdef","EFFECT_CONFIRMED"),
        ("CT-R4-012","a7","LEI-T7","fedcba9876543210fedcba9876543210","NON_EXECUTION_CONFIRMED"),
    ):
        store = AttemptQualificationStore(base/(aid+".sqlite"),verifier)
        store.begin(attempt_id=aid,lei=lei,nonce=nonce,
                    operation_digest=DIGEST,deadline_ms=1400)
        _assert(store.timeout(aid,observed_ms=1500)=="UNKNOWN",
                vector + " timeout promoted uncertainty")
        valid = _signed(private,aid,lei,nonce,outcome)
        tampered = dict(valid)
        tampered["outcome"] = ("NON_EXECUTION_CONFIRMED" if outcome=="EFFECT_CONFIRMED"
                               else "EFFECT_CONFIRMED")
        try:
            store.qualify(aid,tampered,observed_ms=1500)
        except QualificationError:
            pass
        else:
            raise AssertionError(vector + " unauthenticated state promotion")
        _assert(store.read(aid)["state"]=="UNKNOWN",
                vector + " mutated state after unverified evidence")
        expected = "RESOLVED" if vector=="CT-R4-011" else "FAILED"
        _assert(store.qualify(aid,valid,observed_ms=1500)==expected,
                vector + " qualification failed")
        _assert(store.qualify(aid,valid,observed_ms=1501)==expected,
                vector + " exact replay not idempotent")
        _assert([x[0] for x in store.events(aid)].count(expected)==1,
                vector + " duplicate terminal evidence")
        _assert(store.read(aid)["operation_digest"]==DIGEST,
                vector + " digest binding absent")
        checked[vector] = {
            "status":"SCOPED_CANDIDATE_PASS",
            "evidence_level":"SIGNED_SINGLE_HOST_RUNTIME_PROBE",
            "normative_conformant":False,
            "tested":["timeout_no_failed","invalid_signature_no_promotion",
                      "qualified_signed_terminal","replay_at_most_once",
                      "attempt_lei_nonce_operation_digest_binding"],
            "missing":["production governor/dispatch integration",
                       "real provider non-execution authority assurance",
                       "tau_K operational SLA semantics and complete RFC-4 mapping"],
        }
        if vector=="CT-R4-012":
            try:
                store.begin(attempt_id="a7-retry",lei=lei,
                            nonce="11111111111111111111111111111111",
                            operation_digest=DIGEST,deadline_ms=1900)
            except QualificationError:
                pass
            else:
                raise AssertionError("T8 retry incorrectly granted")
    # Direct bridge observation against a real persistent governor registry.
    # This does not enter provider dispatch, adjudication or budget settlement.
    registry = DurableOperationRegistry(str(base/"governor-registry.json"))
    _assert(registry.register(OperationRecord(
        idempotency_key="gov-op-1", passage_id="passage-1", agent_id="bank-agent",
        action_type="payment", amount=5.0, resource_id="budget",
        state=OperationState.UNKNOWN, institutional_scope="bank",
        operation_id="external-operation-1",
    )), "source registry setup failed")
    bridge_store = AttemptQualificationStore(base/"governor-attempt.sqlite",verifier)
    bridge = AttemptOperationObservationBridge(registry,bridge_store)
    bind = bridge.begin_observation(
        operation_key="gov-op-1",attempt_id="gov-attempt-1",
        lei="GOV-LEI-1",nonce="1234567890abcdef1234567890abcdef",
        deadline_ms=1400,
    )
    _assert(bind.status=="MATCHED_OBSERVATION_ONLY", "governor source binding failed")
    digest = operation_context_digest(registry.get("gov-op-1"))
    bridge_evidence = _signed(private,"gov-attempt-1","GOV-LEI-1",
                              "1234567890abcdef1234567890abcdef",
                              "NON_EXECUTION_CONFIRMED",digest=digest)
    recorded = bridge.qualify_observation(
        operation_key="gov-op-1",attempt_id="gov-attempt-1",
        signed_evidence=bridge_evidence,observed_ms=1500,
    )
    _assert(recorded.status=="EVIDENCE_RECORDED_NO_COMMIT_AUTHORITY",
            "governor evidence not recorded safely")
    governor = DualKernelGovernor(
        ScoringKernelAdapter(TenirKernel()),TransitionMembrane(MembraneState()),
        registry=registry,
    )
    observation = inspect_governor_attempt(
        governor,bridge_store,operation_key="gov-op-1",attempt_id="gov-attempt-1",
    )
    _assert(observation["decision"]=="HOLD"
            and observation["execution_authorized"] is False,
            "governor candidate observation unexpectedly authorized execution")
    _assert(registry.get("gov-op-1").state is OperationState.UNKNOWN,
            "candidate wrote to authoritative operation state")
    checked["governor_registry_observer"] = {
        "status":"SCOPED_OBSERVATION_PASS",
        "execution_authorized":False,
        "normative_conformant":False,
        "tested":["persistent_source_binding","qualified_signed_candidate_only",
                  "governor_HOLD","no_operation_state_mutation"],
        "missing":["atomic source/attempt commit authority",
                   "provider settlement proof and budget coupling",
                   "end-to-end native conformance"],
    }
    checked["CT-R4-013"] = {
        "status":"IMPLEMENTATION_GAP", "normative_conformant":False,
        "missing":["retry_eligible contract","new-attempt authorization",
                   "LEI lock and traceable authorization"],
    }
    return {
        "subject":"TENIR-Gov experimental native candidate (NOT released 5.7.0)",
        "pinned_source_commit":CANDIDATE_COMMIT,
        "scope":"isolated REG candidate laboratory; no live dispatch or REG+ promotion",
        "native_normative_conformance":False,
        "reg_release_manifest_modified":False,
        "vectors":checked,
        "verdict":"PARTIAL_CANDIDATE_EVIDENCE",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="reg-native-t6-t7-") as work:
        result = _exercise(Path(work))
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Candidate T6/T7 signed probes: SCOPED_PASS; T8 GAP; native normative HOLD")


if __name__=="__main__":
    main()

"""Isolated candidate-only runtime probes for REG CT-R4-011/012/013.

Never changes runner.py, release manifest, reference-suite verdicts or REG+ claims.
Runs against an explicitly installed TENIR-Gov candidate commit (NOT 5.7.0 GA).
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from decimal import Decimal
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tenir_governance.operations.attempt_qualification import (
    AttemptQualificationStore, QualificationError,
)
from tenir_governance.operations.registry import DurableOperationRegistry, OperationRecord, OperationState
from tenir_governance.operations.sqlite_backend import SQLiteConsensusBackend
from tenir_governance.operations.candidate_atomic_budget import (
    CandidateAtomicBudgetAdmission, CandidateBudgetHold,
)
from tenir_governance.operations.shadow_budget_parity import ShadowBudgetParityAudit
from tenir_governance.operations.shadow_g3_fence import G3ShadowFenceCoordinator
from tenir_governance.operations.shadow_registry_migration import (
    ShadowOperationMigrator, ShadowMigrationHold,
)
from tenir_governance.operations.attempt_atomic_candidate import AtomicAttemptCandidateAuthority
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
CANDIDATE_COMMIT = "97c1192c31b67045ec6b8bac11450a79dcd1eab1"


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
    # A separate single-store candidate: source projection, attempt and
    # attested outcome update atomically in ONE SQLite transaction. This
    # source projection is NOT the authoritative governor OperationState.
    for vector, aid, lei, nonce, outcome, expected_source in (
        ("CT-R4-011", "atomic-a6", "atomic-LEI-6",
         "abcdef0123456789abcdef0123456789", "EFFECT_CONFIRMED", "EFFECT_ATTESTED"),
        ("CT-R4-012", "atomic-a7", "atomic-LEI-7",
         "1234abcdef5678901234abcdef567890", "NON_EXECUTION_CONFIRMED", "NO_EFFECT_ATTESTED"),
    ):
        atomic = AtomicAttemptCandidateAuthority(base/(aid+".sqlite"),verifier)
        initial = atomic.begin(
            operation_key="candidate-op-"+aid, operation_digest=DIGEST,
            attempt_id=aid, lei=lei, nonce=nonce, deadline_ms=1400,
        )
        _assert(initial.attempt_state == initial.candidate_source_state == "UNKNOWN",
                vector+" atomic beginning inconsistent")
        _assert(atomic.timeout(aid, observed_ms=1500).attempt_state=="UNKNOWN",
                vector+" timeout promoted terminal state")
        proof = _signed(private,aid,lei,nonce,outcome,digest=DIGEST)
        terminal = atomic.qualify(aid,proof,observed_ms=1500)
        _assert(terminal.candidate_source_state==expected_source,
                vector+" atomic source projection incorrect")
        _assert(terminal.attempt_state==
                ("RESOLVED" if outcome=="EFFECT_CONFIRMED" else "FAILED"),
                vector+" atomic attempt projection incorrect")
        _assert(terminal.decision=="HOLD" and not terminal.execution_authorized
                and not terminal.is_governor_operation_state,
                vector+" candidate falsely granted execution")
        _assert(atomic.qualify(aid,proof,observed_ms=1600)==terminal,
                vector+" atomic replay not idempotent")
        checked[vector]["atomic_source_attempt_candidate"] = {
            "status":"SCOPED_ATOMIC_SQLITE_PASS",
            "source_projection":expected_source,
            "authorization":False,
            "is_governor_operation_state":False,
        }
    checked["atomic_source_attempt_candidate"] = {
        "status":"SCOPED_ATOMIC_SQLITE_PASS",
        "execution_authorized":False,
        "normative_conformant":False,
        "source_authority":"candidate_projection_only",
        "missing":["migration of production JSON operation registry",
                   "trusted source-of-truth binding", "budget and provider settlement",
                   "full crash protocol across backend transition"],
    }
    # Colocation with the existing SQLite budget backend is tested as
    # schema compatibility only: two API calls are NOT an atomic settlement.
    backend_dir=base/"shared-budget"
    budget=SQLiteConsensusBackend(str(backend_dir))
    _assert(budget.register_resource("budget",Decimal("100"))=="REGISTERED",
            "budget backend initialization failure")
    reservation=budget.reserve("budget-operation-1",Decimal("20"),"budget")
    _assert(reservation.status=="RESERVED", "budget reservation not created")
    shared=AtomicAttemptCandidateAuthority(backend_dir/"consensus.sqlite3",verifier)
    shared.begin(operation_key="budget-operation-1",attempt_id="shared-a7",
                 lei="shared-LEI",nonce="34567890123456789012345678901234",
                 operation_digest=DIGEST,deadline_ms=1400)
    shared.qualify(
        "shared-a7",
        _signed(private,"shared-a7","shared-LEI",
                "34567890123456789012345678901234",
                "NON_EXECUTION_CONFIRMED",digest=DIGEST),
        observed_ms=1500,
    )
    state=SQLiteConsensusBackend(str(backend_dir)).get_state("budget")
    _assert(state.reserved==Decimal("20") and state.committed==Decimal("0"),
            "signed candidate evidence altered real budget")
    _assert(len([item for item in state.reservations
                 if item["key"]=="budget-operation-1"
                 and item["state"]=="RESERVED"])==1,
            "candidate proof unexpectedly settled reservation")
    checked["budget_colocation_guard"]={
        "status":"SCOPED_NO_SETTLEMENT_PASS",
        "source_authority":"SQLiteConsensusBackend",
        "execution_authorized":False,
        "budget_mutated":False,
        "normative_conformant":False,
        "missing":["single transaction linking governor OperationState and budget",
                   "external provider effect adjudication and compensation"],
    }
    # G0/G2: capture authoritative JSON operations in a frozen read-only
    # shadow inventory under the source writer lock. The SQLite copy is NOT
    # an executable or migrated governor registry.
    shadow=ShadowOperationMigrator(registry,base/"governor-shadow.sqlite")
    baseline=shadow.verify_or_stage()
    _assert(baseline.status=="SHADOW_MATCHED_NO_CUTOVER"
            and baseline.execution_authorized is False,
            "G0/G2 shadow unexpectedly granted execution")
    _assert(shadow.inspect()==baseline,"idempotent frozen source snapshot drift")
    _assert(registry.register(OperationRecord(
        idempotency_key="post-shadow-operation",
        passage_id="post-shadow-passage",
        agent_id="post-shadow-agent",action_type="audit",
        state=OperationState.CREATED,
    )), "test source update not applied")
    try:
        shadow.inspect()
    except ShadowMigrationHold:
        pass
    else:
        raise AssertionError("G2 failed to reject new JSON source operation")
    checked["shadow_registry_migration"]={
        "status":"SCOPED_SHADOW_CAPTURE_PASS",
        "execution_authorized":False,
        "cutover_performed":False,
        "source_authority":"JSON_REGISTRY",
        "records_at_baseline":baseline.records,
        "snapshot_sha256":baseline.snapshot_sha256,
        "tested":["single_host_source_lock","frozen_snapshot_idempotence",
                  "strict_source_drift_detection","no_new_authoritative_writer"],
        "normative_conformant":False,
        "missing":["approved atomic cutover","backend schema migration",
                   "single operation/attempt/budget commit transition"],
    }
    # G1 preflight: source snapshot and existing SQLiteBudget parity under
    # single-host writer locks, but still NO actual source-store cutover.
    g1_dir=base/"g1-budget"
    g1_backend=SQLiteConsensusBackend(str(g1_dir))
    _assert(g1_backend.register_resource("g1-resource",Decimal("100"))=="REGISTERED",
            "G1 budget registration failed")
    g1_reservation=g1_backend.reserve("g1-op",Decimal("20"),"g1-resource")
    _assert(g1_reservation.status=="RESERVED","G1 budget reservation failed")
    g1_registry=DurableOperationRegistry(str(base/"g1-operations.json"))
    _assert(g1_registry.register(OperationRecord(
        idempotency_key="g1-op",passage_id="g1-pass",agent_id="g1-agent",
        action_type="payment",amount=20.0,resource_id="g1-resource",
        state=OperationState.UNKNOWN,
        reservation_id=g1_reservation.reservation_id,
        budget_reserved=True,
    )), "G1 authoritative JSON source registration failed")
    g1_shadow=ShadowOperationMigrator(
        g1_registry,g1_dir/"consensus.sqlite3",
    )
    g1_shadow.verify_or_stage()
    g1_check=ShadowBudgetParityAudit(g1_shadow)
    g1_parity=g1_check.verify()
    _assert(g1_parity.status=="BUDGET_PARITY_MATCHED_NO_CUTOVER"
            and g1_parity.execution_authorized is False
            and g1_parity.cutover_authorized is False,
            "G1 parity falsely approved cutover or dispatch")
    _assert(g1_check.verify()==g1_parity, "G1 parity repeat changed")
    _assert(g1_backend.commit(g1_reservation.reservation_id).status=="COMMITTED",
            "G1 mutation fault-injection failed")
    try:
        g1_check.verify()
    except ShadowMigrationHold:
        pass
    else:
        raise AssertionError("G1 did not fail closed after source/budget drift")
    checked["shadow_budget_parity_preflight"]={
        "status":"SCOPED_G1_PARITY_PASS",
        "execution_authorized":False,
        "cutover_authorized":False,
        "source_authority":"JSON_REGISTRY",
        "budget_authority":"SQLiteConsensusBackend",
        "tested":["source_reservation_mapping","amount_and_resource_parity",
                  "I8_accounting_consistency","frozen_parity_epoch",
                  "budget_state_drift_HOLD"],
        "missing":["production single-authority operation/attempt/settlement transaction",
                   "owner epoch fencing","provider effect and budget settlement coupling"],
        "normative_conformant":False,
    }
    # G3 read-only fenced-shadow transfer *ceremony*, NOT active backend
    # ownership. A stale JSON writer must be rejected, and no new dispatch
    # grant may be minted from the candidate epoch.
    g3_dir=base/"g3-budget"
    g3_backend=SQLiteConsensusBackend(str(g3_dir))
    _assert(g3_backend.register_resource("g3-resource",Decimal("100"))=="REGISTERED",
            "G3 SQLite budget setup failed")
    g3_registry=DurableOperationRegistry(str(base/"g3-operations.json"))
    _assert(g3_registry.register(OperationRecord(
        idempotency_key="g3-op", passage_id="g3-pass",agent_id="g3-agent",
        action_type="audit",state=OperationState.CREATED,
    )),"G3 source setup failed")
    stale_registry=DurableOperationRegistry(str(base/"g3-operations.json"))
    g3_shadow=ShadowOperationMigrator(g3_registry,g3_dir/"consensus.sqlite3")
    g3_shadow.verify_or_stage()
    g3_check=ShadowBudgetParityAudit(g3_shadow)
    g3_check.verify()
    g3=G3ShadowFenceCoordinator(g3_check)
    fenced=g3.fence_shadow()
    _assert(fenced.status=="FENCED_SHADOW_HOLD"
            and fenced.legacy_writes_fenced
            and fenced.execution_authorized is False
            and fenced.candidate_dispatch_authorized is False
            and fenced.is_production_cutover is False,
            "G3 fence accidentally granted execution")
    _assert(g3.inspect()==fenced,"G3 frozen handoff cannot be inspected")
    try:
        stale_registry.register(OperationRecord(
            idempotency_key="g3-unauthorized",passage_id="g3-unauthorized",
            agent_id="legacy",action_type="audit",state=OperationState.CREATED))
    except RuntimeError as exc:
        _assert("G3 authority fence" in str(exc),"legacy write rejection is not from G3")
    else:
        raise AssertionError("G3 failed to fence pre-existing JSON registry writer")
    _assert(g3_registry.get("g3-unauthorized") is None,
            "legacy writer persisted after G3 fence")
    # A finalized epoch must not automatically reconstruct a missing
    # marker after possible tampering. The persistent initialized sentinel
    # still blocks cooperating legacy JSON writers.
    os.unlink(g3.marker)
    try:
        g3.fence_shadow()
    except ShadowMigrationHold:
        pass
    else:
        raise AssertionError("G3 silently recreated a missing finalized marker")
    try:
        g3_registry.register(OperationRecord(
            idempotency_key="g3-after-marker-loss",
            passage_id="g3-after-marker-loss",agent_id="old",
            action_type="audit",state=OperationState.CREATED))
    except RuntimeError as exc:
        _assert("G3 authority fence" in str(exc),
                "missing marker unexpectedly reopened old writer")
    else:
        raise AssertionError("G3 initialized sentinel did not block stale JSON writer")
    checked["g3_shadow_fencing"]={
        "status":"SCOPED_G3_FENCED_HOLD_PASS",
        "source_authority":"FENCED_LEGACY_JSON",
        "candidate_dispatch_authorized":False,
        "execution_authorized":False,
        "production_cutover":False,
        "legacy_writers_observed_blocked":True,
        "missing_finalized_marker_is_hold":True,
        "tested":["durable_fence_epoch","stale_writer_denial","monotonic_HOLD",
                  "immutable_shadow_snapshot"],
        "missing":["old non-fence-aware binaries","live governor ownership migration",
                   "budget and provider atomic execution transaction",
                   "cross-host fencing","trusted cutover authorization"],
        "normative_conformant":False,
    }
    # G1 candidate-namespace only: source projection + attempt + existing
    # SQLiteConsensusBackend I8 reservation must commit in one transaction.
    # No production JSON OperationState or external provider is involved.
    g1_atomic_dir=base/"g1-atomic-budget"
    g1_atomic_backend=SQLiteConsensusBackend(str(g1_atomic_dir))
    _assert(g1_atomic_backend.register_resource(
        "candidate:reg-budget",Decimal("10"))=="REGISTERED",
        "isolated G1 candidate resource setup failed")
    g1_atomic=CandidateAtomicBudgetAdmission(
        g1_atomic_backend,verifier,experimental_only=True)
    g1_claim=dict(
        operation_key="candidate:reg-op",operation_digest=DIGEST,
        attempt_id="candidate-reg-attempt",lei="candidate:reg-lei",
        nonce="34567890123456789012345678901234",deadline_ms=1400,
        resource_id="candidate:reg-budget",amount=Decimal("7"),
    )
    receipt=g1_atomic.admit(**g1_claim)
    _assert(receipt.status=="CANDIDATE_RESERVED_HOLD"
            and not receipt.execution_authorized
            and not receipt.source_is_production, "G1 budget claim overpromoted")
    _assert(g1_atomic.admit(**g1_claim)==receipt,
            "G1 repeated claim not idempotent")
    observed=g1_atomic_backend.get_state("candidate:reg-budget")
    _assert(observed.reserved==Decimal("7")
            and observed.committed==Decimal("0"),
            "candidate admission corrupted budget I8")
    _assert(g1_atomic.attempts.inspect("candidate-reg-attempt").attempt_state=="UNKNOWN",
            "G1 atomic attempt not persisted")
    try:
        g1_atomic.admit(**{
            **g1_claim,"operation_key":"candidate:reg-op-2",
            "attempt_id":"candidate-reg-attempt-2",
            "lei":"candidate:reg-lei-2","amount":Decimal("7"),
        })
    except CandidateBudgetHold:
        pass
    else:
        raise AssertionError("G1 candidate exceeded I8 capacity")
    _assert(g1_atomic_backend.get_state("candidate:reg-budget").reserved==Decimal("7"),
            "failed G1 candidate admission partially reserved budget")
    # Signed candidate-only effect settlement: attempt + source + existing
    # budget reservation/disposition are updated inside one SQLite TX.
    g1_effect_proof=_signed(
        private,"candidate-reg-attempt","candidate:reg-lei",
        "34567890123456789012345678901234","EFFECT_CONFIRMED",digest=DIGEST)
    effect=g1_atomic.settle_attested_candidate(
        attempt_id="candidate-reg-attempt",signed_evidence=g1_effect_proof,
        observed_ms=1500,
    )
    _assert(effect.status=="CANDIDATE_EVIDENCE_SETTLED_HOLD"
            and effect.attempt_state=="RESOLVED"
            and effect.budget_state=="COMMITTED"
            and effect.execution_authorized is False,
            "signed candidate effect incorrectly settled or authorized")
    _assert(g1_atomic.settle_attested_candidate(
        attempt_id="candidate-reg-attempt",signed_evidence=g1_effect_proof,
        observed_ms=1600)==effect,"signed effect replay diverged")
    g1_now=g1_atomic_backend.get_state("candidate:reg-budget")
    _assert(g1_now.reserved==Decimal("0") and g1_now.committed==Decimal("7"),
            "signed candidate effect did not atomically settle budget")

    # An independent simulated non-execution moves only the experimental
    # reservation to RELEASED, never triggers a real provider retry.
    second=dict(g1_claim,operation_key="candidate:reg-op-3",
                attempt_id="candidate-reg-attempt-3",
                lei="candidate:reg-lei-3",amount=Decimal("2"))
    g1_atomic.admit(**second)
    no_effect=_signed(private,"candidate-reg-attempt-3","candidate:reg-lei-3",
        "34567890123456789012345678901234","NON_EXECUTION_CONFIRMED",digest=DIGEST)
    released=g1_atomic.settle_attested_candidate(
        attempt_id="candidate-reg-attempt-3",signed_evidence=no_effect,
        observed_ms=1500,
    )
    _assert(released.attempt_state=="FAILED"
            and released.budget_state=="RELEASED"
            and released.execution_authorized is False,
            "signed candidate no-effect incorrectly settled or authorized")
    totals=g1_atomic_backend.get_state("candidate:reg-budget")
    _assert(totals.reserved==Decimal("0") and totals.committed==Decimal("7"),
            "signed candidate no-effect altered committed budget")
    checked["g1_atomic_budget_candidate"]={
        "status":"SCOPED_G1_ATOMIC_I8_CANDIDATE_PASS",
        "candidate_namespace_only":True,
        "single_sqlite_transaction":True,
        "source_authority":"CANDIDATE_PROJECTION_NOT_GOVERNOR",
        "execution_authorized":False,
        "production_cutover":False,
        "normative_conformant":False,
        "tested":["source_attempt_reservation_single_transaction",
                  "idempotent_replay","I8_capacity_fail_closed",
                  "budget_and_attempt_atomic_rollback",
                  "signed_effect_atomic_COMMITTED","signed_no_effect_atomic_RELEASED",
                  "exact_signed_settlement_replay"],
        "missing":["authoritative production OperationState integration",
                   "cutover owner fencing across all deployed writers",
                   "external provider dispatch and effect settlement",
                   "T8 retry authorization"],
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

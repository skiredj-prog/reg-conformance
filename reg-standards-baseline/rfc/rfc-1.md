---
rfc: 1
title: The Execution Grant Envelope (EGE) & Wire Protocol
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0]
---

# RFC-1: The Execution Grant Envelope (EGE) & Wire Protocol

**Status:** Proposed Standard (Draft)
**Dependency:** RFC-0 (Constitution)

---

## 1. The Seven Invariants of the Wire Protocol

To ensure the wire protocol does not inadvertently reintroduce implementation-specific topologies or weaken the constitutional guarantees of RFC-0, RFC-1 is governed by seven strict invariants:

1. **EGE is a proof container, not an evaluation pipeline.** The EGE represents the evidentiary state of an execution evaluation, not the internal order in which admissibility dimensions are computed.

2. **Topological independence is preserved.** REG MUST NOT require any particular evaluation order between Standing, Structure, and Commit.

3. **HOLD is a REG disposition; 202 is merely its transport representation.** A 202 Accepted HTTP response MUST NOT constitute execution authorization.

4. **Fail-Closed Execution.** No valid grant + transport uncertainty = MUST NOT EXECUTE.

5. **Transport failure vs. Cryptographic Verdict.** Transport failure (e.g., 503, timeout) produces a fail-closed execution state, but is not necessarily a cryptographic HARD_VETO verdict. Auditors must distinguish between an explicit refusal and an unverified state.

6. **Independent Verifiability.** Each attestation (Standing, Structure, Commit) MUST be independently verifiable by a conforming third party. Verification of one MUST NOT require access to the implementation internals of another.

7. **Implementation Neutrality.** REG wire semantics MUST remain implementation-neutral and vendor-neutral.

---

## 2. Transport & Endpoint Definitions

The 4-phase lifecycle (RFC-0) maps to the following RESTful endpoints:

**Phase 1 (Pre-Execution):** `POST /evaluations`
Action: Submit EvaluationRequest.

**Phase 2 (Conditional Auth):** Response to Phase 1.
Action: Returns EvaluationResponse containing the EGE. If the membrane requires time, returns 202 Accepted with a Location header for polling/webhooks.

**Phase 3 (Supervised Exec):** `POST /evaluations/{evaluation_id}/events`
Action: Submit sequenced ExecutionEvent (e.g., STARTED, TRANSITION).

**Phase 4 (Closure & Proof):** `GET /evaluations/{evaluation_id}/evidence`
Action: Retrieve the final Evidence Manifest.

---

## 3. The Execution Grant Envelope (EGE) Structure

The EGE is the core payload of the EvaluationResponse. It is structured as a container of independent proofs.

```json
{
  "envelope_id": "ege_8f7a9b...",
  "evaluation_id": "eval_123...",
  "action_id": "act_999...",
  "timestamp": "2026-10-27T10:00:00Z",
  "final_disposition": "PASS",
  "valid_until": "2026-10-27T10:05:00Z",
  "invalidation_conditions": ["state_drift", "standing_revoked"],
  "attestations": {
    "standing_attestation": {
      "status": "VALID",
      "proof_reference": "hash_or_uri_to_standing_proof",
      "verifiable_credentials": ["..."]
    },
    "structure_attestation": {
      "status": "ADMISSIBLE",
      "raw_score": 0.85,
      "proof_reference": "hash_or_uri_to_geometry_proof",
      "reason_codes": ["INV-001_MET"]
    },
    "commit_attestation": {
      "status": "BOUND",
      "nonce": "a1b2c3d4",
      "state_hash_at_verdict": "0x9f8e7d...",
      "proof_reference": "hash_or_uri_to_commit_proof"
    }
  },
  "routing": {
    "next_hop": "executor_service",
    "tau_k_seconds": 900,
    "exhaustion_policy": "fail_closed"
  }
}
---
rfc: 1
title: The Execution Grant Envelope (EGE) & Wire Protocol
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0]
---

# RFC-1: The Execution Grant Envelope (EGE) & Wire Protocol

**Status:** Proposed Standard (Frozen Draft)
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

**Phase 1 (Pre-Execution):** POST /evaluations
Action: Submit EvaluationRequest.

**Phase 2 (Conditional Auth):** Response to Phase 1.
Action: Returns EvaluationResponse containing the EGE. If the membrane requires time, returns 202 Accepted with a Location header for polling/webhooks.

**Phase 3 (Supervised Exec):** POST /evaluations/{evaluation_id}/events
Action: Submit sequenced ExecutionEvent (e.g., STARTED, TRANSITION).

**Phase 4 (Closure & Proof):** GET /evaluations/{evaluation_id}/evidence
Action: Retrieve the final Evidence Manifest.

---

## 3. The Execution Grant Envelope (EGE) Structure

The EGE is the core payload of the EvaluationResponse. It is structured as a container of independent proofs.

The reference logical structure is:

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

**Note:** The exact JSON schema will be formalized in the implementation annex. The above illustrates the logical separation of the three independent attestations.

---

## 4. Idempotency, Replay & Sequence Control

**Idempotency-Key:** Mandatory for POST /evaluations and POST /evaluations/{id}/events. It is a security primitive, not just a network convenience.

- Replay with the same key and identical payload = return cached logical result.
- Replay with the same key but different payload = 409 Conflict.

**Sequence Control:** ExecutionEvent payloads must include a strictly monotonically increasing event_sequence. Out-of-order or duplicate sequences are rejected as conflicts.

---

## 5. Error Taxonomy & Fail-Closed Semantics

All errors follow the application/problem+json standard.

| HTTP Code | Situation | Client Action (Fail-Closed) |
|---|---|---|
| 400 | Invalid JSON / headers | Correct message. Do not retry. |
| 401 | Invalid auth / signature | Correct authentication. |
| 409 | Idempotency / sequence conflict | Read state, resolve divergence. |
| 422 | Semantic incompleteness | Correct payload content. |
| 503 | Membrane unavailable / not ready | MUST NOT execute. Treat as fail-closed. Do not retry automatically if it risks double execution. |
| Timeout | Network / transport failure | MUST NOT execute. Treat as fail-closed execution state. |

**Crucial Rule:** A retry MUST NEVER accidentally execute a second consequential action. If the client cannot verify the membrane's state due to transport failure, the default action is to halt the proposed consequential action.

---

## 6. Identity, Trace Correlation & Security Headers

### Correlation Chain

The protocol mandates a strict chain of reference identifiers linking the procedural decision to the cryptographic proof:

- decision_id - procedural origin
- action_id - business-stable identifier
- evaluation_id - specific membrane evaluation
- evidence_id - final cryptographic proof

**Note:** These are reference relations, not necessarily a temporal sequence.

### Technical Tracing

X-Trace-Id (or equivalent W3C Trace Context) is used for distributed technical tracing. It does not replace the business correlation chain.

### Security Headers

- Mutual TLS (mTLS) is mandatory for workload-to-workload transport.
- Payloads must be secured using a Detached-Signature (as defined in RFC-6).
- Implementation-specific headers (e.g., vendor-specific signature headers) MUST NOT be used in the normative REG standard.

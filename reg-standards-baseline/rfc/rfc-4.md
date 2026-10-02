---
rfc: 4
title: Commit & Execution Proof
version: v0.2
status: Frozen
date: 2026-10-02
supersedes: v0.1
dependencies:
  - RFC-0 (Constitution)
  - RFC-1 (Wire Protocol)
  - RFC-2 (Structure)
  - RFC-3 (Standing)
---

# RFC-4: Commit & Execution Proof

## Purpose

Defines the properties that must be satisfied for an Execution Grant to cross the
Execution Boundary and become an external effect. Establishes the mechanisms to
prevent replay and race conditions, mandates Decision Receipts for all
dispositions, and standardizes the Evidence Manifest for post-hoc verification.

## Major Decisions Locked

1. **Commit Binding Property (Not External Atomicity)** — REG ensures that an
   Execution Grant cannot be successfully consumed for an effect outside its
   declared binding, validity window, or commit conditions. Where the external
   effect cannot participate in an atomic transaction with the Commit Gate, the
   implementation MUST provide explicit post-commit evidence and MUST NOT claim
   atomic external-effect semantics.

2. **Commit State Binding (Generic Mechanism)** — To prevent race conditions, the
   membrane binds the evaluation to a specific state. The reference mechanism is a
   `state_hash_at_verdict`, but implementations MAY use equivalent mechanisms
   (version/epoch, optimistic concurrency token, transaction identifier, resource
   version) provided they satisfy the same security property.

3. **Decision Receipt (Symmetric Proof)** — Every disposition generates a signed
   Decision Receipt. PASS yields a Grant/Authorization Receipt; FLAG yields a
   Conditional Decision Receipt; HOLD yields a Suspension Receipt; HARD_VETO yields
   a Refusal Receipt. Silence is not a valid governance outcome.

4. **Independent Reproducibility (Not World-State Replay)** — REG requires that an
   independent verifier can reproduce or verify the decision from recorded inputs,
   policy/version identifiers, transformation rules, and cryptographic
   attestations. It does NOT require reproduction of the external world-state.
   Implementations declare their Reproducibility Class (R0, R1, R2).

5. **Tamper-Evident Evidence (Mechanism-Neutral)** — The Evidence Manifest MUST be
   tamper-evident and independently verifiable. The reference mechanism is a Merkle
   tree or transparency log, but implementations MAY use equivalent append-only
   ledgers provided they satisfy the same integrity property.

6. **RFC-4 Does Not Execute** — RFC-4 defines the conditions under which an
   execution may cross the boundary. The executor remains responsible for the
   external effect. RFC-4 produces evidence of the decision and its binding, not
   evidence of the effect itself.

---

## 1. The Commit Boundary & Binding Property

### 1.1 Commit Binding Property

A conforming implementation MUST ensure that an Execution Grant cannot be
successfully consumed for an effect that is outside its declared binding, validity
window, or commit conditions.

**What REG Controls:**

- The grant is bound to a specific `evaluation_id`, `action_id`, and `nonce`.
- The grant is valid only within the `valid_until` window.
- The grant is valid only if the Standing Credential remains valid (RFC-3).
- The grant is valid only if the structural state has not materially drifted (RFC-2).

**What REG Does Not Control:**

- The atomicity of the external effect.

Where the external system cannot participate in an atomic transaction with the
Commit Gate, the implementation MUST provide explicit post-commit evidence and
MUST NOT claim atomic external-effect semantics. This post-commit evidence is
captured in the Evidence Manifest (§4).

### 1.2 Grant Consumption

An Execution Grant is a single-use authorization for a specific action context.
The commit request from the executor MUST include:

- `envelope_id`
- `nonce`
- `action_id`

The membrane verifies this binding before allowing the effect to proceed.

### 1.3 Topological Independence

Commit validation may occur in parallel with or immediately after Standing and
Structure checks, provided the final EGE contains a valid `commit_attestation`.

The final disposition recorded in the EGE remains the most-restrictive composition
of the Standing, Structure, and Commit results (RFC-0).

---

## 2. Anti-Replay & Race Soundness

### 2.1 Replay Soundness (Nonce Enforcement)

Every EvaluationRequest MUST contain a unique, unpredictable nonce. Replaying a
previous request with the same nonce is rejected. The nonce is cryptographically
bound to the Execution Grant and MUST be presented at commit time.

### 2.2 Race Soundness (Commit State Binding)

The membrane binds the evaluation to a specific state at the moment of verdict.

**Reference Mechanism:** `state_hash_at_verdict`. At commit time the executor MAY
present a `state_hash_at_commit`. If the delta exceeds the pre-declared tolerance,
the membrane triggers HARD_VETO.

The tolerance (or equivalent acceptance criteria for alternative binding
mechanisms) is part of the versioned policy and threshold configuration and is
subject to change control.

**Alternative Mechanisms** (provided they satisfy the same security property):

- Version/Epoch
- Optimistic Concurrency Token
- Transaction Identifier
- Resource Version

If the state changes after the verdict but before commit, the binding mechanism
MUST detect this and trigger HARD_VETO.

---

## 3. Decision Receipts (Symmetric Proof)

### 3.1 Mandatory Generation

Every disposition MUST generate a cryptographically signed Decision Receipt.
Silence is not a valid governance outcome.

### 3.2 Receipt Taxonomy

| Disposition | Receipt Type | Purpose |
|---|---|---|
| PASS | Grant / Authorization Receipt | Proof of authorization under specific bindings |
| FLAG | Conditional Decision Receipt | Proof of conditional authorization with explicit conditions |
| HOLD | Suspension Receipt | Proof of suspension with triggering conditions and tau_K |
| HARD_VETO | Refusal Receipt | Proof of categorical refusal with reason codes |

### 3.3 Receipt Contents

Every Decision Receipt MUST include:

- `evaluation_id`
- `action_id`
- `disposition`
- `reason_codes`
- `timestamp`
- `policy_version`
- `threshold_version`
- `reproducibility_class` (R0/R1/R2)
- `signature`

It is RECOMMENDED that the receipt also carry a composition disposition field (or
equivalent) when a multiagent Composition Admissibility outcome contributed to the
final disposition.

---

## 4. Evidence Manifest & Tamper-Evident Ledger

### 4.1 Manifest Composition

Upon COMPLETED, ABORTED, or ROLLED_BACK the membrane aggregates:

1. Original EvaluationRequest (or its hash)
2. Execution Grant Envelope (EGE)
3. Sequenced ExecutionEvent log
4. Final Decision Receipt(s)
5. Post-commit evidence (mandatory when external effect could not be atomic)

### 4.2 Tamper-Evident Property (Mechanism-Neutral)

The Evidence Manifest MUST be tamper-evident, append-only, and independently
verifiable.

**Reference mechanism:** Merkle tree or transparency log. Equivalent mechanisms are
permitted provided they satisfy the same integrity property.

### 4.3 Independent Reproducibility (Not World-State Replay)

A conforming implementation MUST supply sufficient evidence for an independent
verifier to reproduce or verify the decision from recorded inputs, policy/version
identifiers, transformation rules, and cryptographic attestations.

Reproduction of the external world-state is not required.

### 4.4 Reproducibility Classes

The declared class (R0/R1/R2) MUST appear in the EGE, every Decision Receipt, and
the Evidence Manifest.

| Class | Meaning |
|---|---|
| R0 | Evidence-only |
| R1 | Deterministically reproducible |
| R2 | Cryptographically independently verifiable |

---

## 5. Interoperability, Verifiability & Conformance

### 5.1 Independent Verification

An auditor MUST be able to:

- Verify the Decision Receipt signature
- Verify the tamper-evident property of the Evidence Manifest
- Replay or independently verify the decision (subject to the declared
  Reproducibility Class)

### 5.2 Conformance Test Vectors

RFC-4 defines a minimal set of normative behavioral test vectors. These vectors
are the canonical bridge between the normative properties of this RFC and
independent implementations.

Each vector is specified by the following fields:

| Field | Purpose |
|---|---|
| `vector_id` | Stable identifier |
| `input` | Execution request / EGE / attestations |
| `initial_state` | Relevant state at evaluation |
| `commit_state` | State presented at commit |
| `policy_version` | Exact policy / constraint version |
| `expected_disposition` | PASS / FLAG / HOLD / HARD_VETO |
| `expected_commit_result` | EXECUTE / REJECT |
| `expected_receipt` | Required receipt type |
| `expected_failure_code` | Deterministic reason code (when applicable) |
| `evidence_requirements` | What must be verifiable afterward |

**Normative minimal set:**

1. CT-R4-001 — Valid Grant Binding: valid EGE, matching evaluation_id / action_id / nonce, matching commit state → PASS / EXECUTE
2. CT-R4-002 — Action/Payload Binding Violation: grant issued for action_A, commit attempts action_B → HARD_VETO / REJECT
3. CT-R4-003 — Replay Rejection: reuse of a consumed nonce or grant → REJECT / REPLAY_DETECTED
4. CT-R4-004 — Expired Grant Rejection: `valid_until` window passed before commit → REJECT / EVALUATION_EXPIRED
5. CT-R4-005 — Commit-State Binding / Race Detection: state at commit materially differs from state captured at verdict (state_hash_at_verdict or equivalent) → REJECT / STATE_DRIFT
6. CT-R4-006 — Non-PASS Cannot Cross Commit: HOLD or HARD_VETO disposition → commit attempt → REJECT / INVALID_DISPOSITION
7. CT-R4-007 — Decision Receipt Generation: every disposition (including non-PASS) produces a cryptographically signed Decision Receipt, independently verifiable without accessing internal state
8. CT-R4-008 — Evidence Manifest Integrity: Evidence Manifest altered after closure → integrity verification fails. Requires tamper-evident, append-only ledger.
9. CT-R4-009 — Independent Evidence Verification: third-party verifier can reproduce or verify the decision from the Manifest without accessing mutable internal state
10. CT-R4-010 — External-Effect Claim Boundary: implementation provides post-commit evidence for non-atomic external effects and does NOT claim atomic external-effect semantics

A conforming implementation MUST pass all applicable vectors in this minimal set.

The expanding, machine-readable corpus of additional vectors, edge cases, and
multi-implementation interoperability tests is maintained in RFC-7 (Conformance
Suite & Interoperability) and the associated public conformance repository. RFC-7
is the authoritative source for the full harness; RFC-4 supplies only the
normative minimal behavioral anchors.

---

## 6. Summary: The Four Properties of RFC-4

| Property | Question |
|---|---|
| Grant Binding | Does this decision concern exactly this action, under these exact conditions? |
| Replay Soundness | Can the same grant be fraudulently reused? |
| Race Soundness | Does the decision remain valid in the face of state changes? |
| Evidence Integrity | Can we prove after the fact what was decided, under which bindings, and what execution evidence was recorded? |

RFC-3 protects the continuity of authority. RFC-4 protects the integrity of the
passage from authority to effect.

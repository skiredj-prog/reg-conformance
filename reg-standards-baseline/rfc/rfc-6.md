---
rfc: 6
title: Security, Transport & Cryptography
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0, RFC-1, RFC-3]
---

# RFC-6: Security, Transport & Cryptography

**Status:** Proposed Standard (Draft)
**Dependencies:** RFC-0 (Constitution), RFC-1 (Wire Protocol), RFC-3 (Standing)

**Purpose:** Defines the strict security requirements for the membrane itself. It standardizes workload identity, message integrity, replay protection, key management, and data minimization at the Execution Boundary.

---

## Major Decisions Locked

1. **Workload Identity via mTLS:** Mutual TLS (mTLS) is the mandatory baseline for authenticating the communication channel between the proposing agent and the membrane.

2. **Detached Signatures & Canonicalization:** Payloads MUST be secured using detached signatures over a canonicalized representation (e.g., JCS), ensuring that signature verification is independent of JSON formatting or whitespace.

3. **Idempotency as a Security Primitive:** Idempotency keys and freshness windows are mandatory security controls to prevent replay attacks, not merely network reliability features.

4. **Cryptographic Agility & Revocation:** The standard mandates algorithm agility (SHA-256 minimum) and strict key rotation/revocation protocols, explicitly linking key revocation to the `revocation_bound` defined in RFC-3.

5. **Data Minimization:** Governance payloads MUST NOT contain secrets, credentials, or unnecessary Personally Identifiable Information (PII).

---

## 1. Transport & Channel Security

The transport layer must guarantee the authenticity of the communicating workloads and enforce fail-closed semantics during network degradation.

### 1.1 Mutual Authentication

**Requirement:** Communication between the proposing agent (or executor) and the Constitutional Membrane MUST be secured using Mutual TLS (mTLS) or an equivalent cryptographic channel authentication mechanism.

**Workload Identity:** The membrane MUST verify the workload identity (e.g., SPIFFE ID, service account) of the caller against the Standing Credential presented in the EGE.

### 1.2 Fail-Closed Transport Semantics

**Requirement:** As defined in RFC-1, if the transport channel is degraded, unavailable, or if mTLS handshake fails, the system MUST enter a fail-closed execution state.

**Distinction:** Transport failure prevents execution but does not inherently generate a cryptographic HARD_VETO Decision Receipt, as no evaluation occurred.

---

## 2. Message Integrity & Signatures

To ensure that the Execution Grant Envelope (EGE) and Evaluation Requests cannot be tampered with in transit, the standard mandates strict message integrity controls.

### 2.1 Detached Signatures

**Requirement:** All critical payloads (EvaluationRequest, EGE, ExecutionEvent) MUST be secured using a detached digital signature.

**Transport Neutrality:** The signature MUST be carried in a standardized transport header (e.g., `Detached-Signature`) or an equivalent protocol-specific mechanism. Implementation-specific headers (e.g., vendor-prefixed headers) MUST NOT be used in the normative standard.

### 2.2 Canonicalization

**Requirement:** To ensure deterministic signature verification across different programming languages and JSON parsers, the payload MUST be canonicalized before signing and verification.

**Reference Standard:** Implementations SHOULD use a standardized canonicalization scheme, such as the JSON Canonicalization Scheme (JCS - RFC 8785), to normalize key ordering and whitespace prior to cryptographic hashing.

### 2.3 Cryptographic Agility & Minimum Strength

**Requirement:** The standard MUST support algorithm agility to allow for future cryptographic upgrades without breaking the wire protocol.

**Minimum Baseline:** At the time of publication, hash functions MUST be at least SHA-256. Signature algorithms MUST provide a minimum of 128-bit security strength (e.g., ECDSA P-256, Ed25519, or RSA-3072).

---

## 3. Replay Protection & Freshness

To prevent an attacker from capturing a valid Execution Grant or Evaluation Request and reusing it to execute an unauthorized action, the membrane MUST enforce strict replay protection.

### 3.1 Idempotency as a Security Primitive

**Requirement:** All state-changing requests (e.g., `POST /evaluations`) MUST include a globally unique, cryptographically random `Idempotency-Key`.

**Enforcement:** The membrane MUST reject any request where the `Idempotency-Key` has been previously used with a different payload. This is a security requirement to prevent duplicate consequential actions, not just a network convenience.

### 3.2 Freshness Windows

**Requirement:** Every request MUST include a `submitted_at` timestamp (or equivalent nonce/epoch).

**Enforcement:** The membrane MUST reject requests where the `submitted_at` timestamp falls outside a pre-declared freshness window (e.g., ±5 minutes). This bounds the window of opportunity for replay attacks, even if an `Idempotency-Key` is somehow compromised.

---

## 4. Key Management & Revocation

The security of the membrane relies on the secure lifecycle of the cryptographic keys used to sign Standing Credentials and Decision Receipts.

### 4.1 Key Rotation

**Requirement:** Implementations MUST support seamless key rotation. The wire protocol MUST include the `key_id` or `certificate_fingerprint` in the signature header to allow the verifier to select the correct public key.

**Grace Period:** Old keys MUST be retained for a defined overlap period to verify historical Decision Receipts and Evidence Manifests.

### 4.2 Revocation & The revocation_bound

**Requirement:** When a cryptographic key or certificate is compromised or retired, it MUST be revoked.

**Integration with RFC-3:** Key revocation MUST be treated as a material invalidation event. The membrane MUST enforce the `revocation_bound` (e.g., `revocation_epoch`, watermark, or CRL freshness) defined in RFC-3.

Any Standing Credential signed with a revoked key, or presented after its `revocation_bound`, MUST NOT produce executable authorization.

---

## 5. Data Minimization & Privacy

The Execution Boundary is a high-trust zone. To minimize the blast radius of a potential breach, the standard enforces strict data minimization.

### 5.1 Prohibition of Secrets

**Requirement:** EvaluationRequests and EGEs MUST NOT contain raw secrets, passwords, private keys, or unmasked credentials. If an action requires a secret to execute, the membrane MUST only receive a reference or a cryptographic hash of the secret, not the secret itself.

### 5.2 PII Minimization

**Requirement:** Personally Identifiable Information (PII) SHOULD NOT be included in the governance payload unless strictly necessary for the structural evaluation (e.g., a specific regulatory check). If included, it MUST be minimized and protected according to applicable data privacy regulations.

---

## 6. Interoperability & Conformance

How to prove a system satisfies REG Security requirements.

### 6.1 Mandatory Security Properties

A conforming implementation MUST demonstrably satisfy:

1. **Channel Auth:** Rejecting unauthenticated or improperly authenticated transport connections.
2. **Signature Verification:** Successfully verifying a detached signature over a canonicalized payload, and rejecting a payload where a single byte has been altered.
3. **Replay Prevention:** Rejecting a replayed request with the same `Idempotency-Key` but a different payload, and rejecting a request with an expired `submitted_at` timestamp.
4. **Revocation Enforcement:** Rejecting a Standing Credential signed by a key that has been explicitly revoked past its `revocation_bound`.

### 6.2 Conformance Tests (RFC-7)

The RFC-7 Conformance Harness MUST include specific security test vectors:

1. **VEC-6-01 (Canonicalization):** Submitting a payload with altered JSON whitespace/key ordering to prove the signature verification relies on canonicalization, not raw string matching.
2. **VEC-6-02 (Replay):** Submitting a valid, previously used `Idempotency-Key` with a modified action value to prove the system rejects the replay.
3. **VEC-6-03 (Freshness):** Submitting a valid request with a `submitted_at` timestamp outside the freshness window to prove rejection.
4. **VEC-6-04 (Revocation):** Presenting a valid Standing Credential signed by a key that is past its declared `revocation_bound` to prove the system triggers a HARD_VETO or invalidation.
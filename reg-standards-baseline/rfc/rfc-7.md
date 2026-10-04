---
rfc: 7
title: Conformance Suite & Interoperability
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0, RFC-1, RFC-2, RFC-3, RFC-4, RFC-5, RFC-6]
---

# RFC-7: Conformance Suite & Interoperability

**Status:** Proposed Standard (Frozen Draft)
**Dependencies:** RFC-0 through RFC-6

**Purpose:** Defines how conformance is proven. Establishes the philosophy, the test vector format, the conformance harness architecture, the mandatory test categories, the deployment maturity ladder, and the separation between implementation status and conformance status.

---

## Major Decisions Locked

1. **Behavioral Conformance over Internal Topology:** REG tests what an implementation proves and does, not whether it was built according to any specific reference model.

2. **Three Levels of EGE Independence:** The conformance suite MUST prove that the standing, structure, and commit attestations are independent at the Cryptographic, Structural, and Semantic levels.

3. **Separation of Conformance and Maturity:** Conformance is binary (satisfies normative requirements). Maturity is the breadth of deployment.

4. **Separation of Implementation and Test Status:** An implementation's internal development status is strictly separated from its normative test outcomes.

---

## 1. Conformance Philosophy

REG standardizes the execution boundary and its proof obligations. Conformance testing focuses on input/output behavior, cryptographic proof integrity, and epistemic handling, rather than code path coverage or internal architecture.

---

## 2. Reference Deployment Artifacts

Before runtime conformance testing can occur, the deployment must define its governance scope. REG requires the functions and evidence of the seven governance artifacts (TAU Declaration, Invariant, Admissible Region, tau_K, Decision Policy, Runbook, Record Schema). The specific serialization formats are reference recommendations, not mandatory identifiers, ensuring genuine openness.

---

## 3. Machine-Readable Test Vector Format

A Test Vector isolates a specific normative property and defines the exact inputs and mandatory expected outcomes.

### 3.1 Test Vector Structure

To prevent ambiguity, expected outcomes are strictly typed. The reference structure is:

    vector_id, target_rfc, property_tested,
    inputs (action, standing, measurements),
    expected_outcome (
        allowed_dispositions,
        expected_disposition,
        expected_transition,
        receipt_type_required,
        reason_code_required
    )

**Note:** `allowed_dispositions` defines the set of acceptable outcomes. `expected_disposition` is used when exactly one outcome is required. `expected_transition` is used for sequential behavior.

---

## 4. Conformance Harness Architecture & Section Independence

The REG Conformance Harness is an implementation-neutral execution engine. It tests the three EGE sections at three distinct, mandatory levels of independence:

1. **Cryptographic Independence:** Can the signature and integrity of each attestation be verified using only public cryptographic material, without trusting the other sections?

2. **Structural Independence:** Can the verifier parse and validate the schema and format of each attestation without executing the internal logic of another gate?

3. **Semantic Independence:** Can a failure or change in one dimension (e.g., Structure) be evaluated and understood without requiring the verifier to reproduce the internal calculations of another dimension (e.g., Standing)?

---

## 5. Mandatory Test Categories

The harness MUST include vectors covering five primary categories:

1. **EGE & Section Independence:** Tests that the three attestations can be parsed, verified cryptographically, and evaluated semantically without hidden coupling.

2. **Epistemic Soundness (RFC-2):** Tests UNKNOWN, STALE, CONTRADICTORY, and LOW CONFIDENCE states. The implementation MUST NOT silently treat insufficient evidence as establishing admissibility.

3. **Authority Continuity (RFC-3):** Tests Non-Amplification, invalidation/revocation bounds, and credential/grant separation. An invalidated authority MUST NOT produce executable authorization.

4. **Commit Integrity (RFC-4):** Tests grant/action binding, replay soundness, commit-state binding, and evidence integrity. Reuse of a single-use execution authorization MUST be detected and MUST NOT produce an executable effect.

5. **Liveness & Exhaustion (RFC-5):** Tests that expiration of a declared tau_K window on HOLD produces exactly the pre-declared exhaustion behavior, without ad-hoc policy substitution.

---

## 6. Deployment Maturity Levels

REG Conformance is binary: an implementation either satisfies the applicable normative requirements or it does not.

**Deployment Maturity** measures the operational breadth of the implementation.

REG Conformance: RFC-0 -> RFC-1 -> RFC-2 -> RFC-3 -> RFC-4 -> RFC-5 -> RFC-6

Deployment Maturity: Level 0 (Defined) through Level 5 (Composed), as defined in RFC-5 section 5.

An implementation can be fully REG-Conformant at Deployment Maturity Level 1 (Observable). Maturity levels do not imply "partial compliance."

---

## 7. Interoperability & Implementation Gaps

### 7.1 Separation of Implementation and Conformance Status

To maintain the integrity of the standard, an implementation's internal development status is strictly separated from its normative test outcomes. Implementations MUST report using the following structured, machine-readable matrices:

**Implementation Status:** IMPLEMENTED, PARTIALLY IMPLEMENTED, NOT IMPLEMENTED, NOT_APPLICABLE

**Test/Conformance Status:** PASSED, FAILED, NOT TESTED, NOT APPLICABLE

**Example Conformance Report Entry:**

| Property | Implementation Status | Test Status | Normative Conformance |
|---|---|---|---|
| RFC-3 Non-Amplification | IMPLEMENTED | PASSED | Conformant |
| RFC-4 Decision Receipts | NOT IMPLEMENTED | NOT TESTED | Non-conformant |
| RFC-6 mTLS | PARTIALLY IMPLEMENTED | NOT TESTED | Degraded |

### 7.2 Third-Party Verification

Conformance reports generated by the RFC-7 Harness MAY be independently reviewed or verified by a third party. RFC-7 defines the evidence required for such verification but does not mandate a certification authority, accreditation scheme, or certification business model. This ensures the standard remains neutral, future-proof, and free from institutional capture.

---

## 8. Interface Modes and Evidence Levels

### 8.1 Interface Modes

The conformance suite runs in two modes. **Conformance is declared per mode.**

| Mode | interface_mode | Evidence level | Description |
|---|---|---|---|
| --mode http | "adapter" | 2 - Adapter-Tested | Tests against a REG HTTP endpoint. Behavioral compatibility; not native conformance. |
| --mode native | "native" | 3 - Native-Conformant | Tests in-process kernel directly via NativeKernelAdapter. No HTTP layer. |

### 8.2 Evidence Levels

- **Level 1 - SEMANTIC_MAPPING:** Documented conceptual correspondence only - no execution.
- **Level 2 - ADAPTER_TESTED:** Passes via translation layer - behavioral compatibility, NOT native conformance.
- **Level 3 - NATIVE_CONFORMANT:** Native interface satisfies normative properties directly.

Every result MUST declare its interface_mode. A report mixing native and adapter results without explicit labeling is non-conformant.

### 8.3 Reporting States

| State | Meaning |
|---|---|
| PASS | Normative requirement satisfied |
| FAIL | Normative requirement violated |
| NOT_APPLICABLE | Property does not apply to this topology |
| ADAPTER_REQUIRED | Testable only through a translation layer |
| IMPLEMENTATION_GAP | Requirement understood; not yet engineered |

---

## 9. Conformance Test Tiers

Vectors are organized by testability tier:

| Tier | Meaning | Example vectors |
|---|---|---|
| Tier 1 | Testable against reference shim now | C1-C5, CT-R4-001/002/003/006/010, R7-003, R7-004 |
| Tier 2 | Requires shim enrichment (composition, delegation, evidence) | R1-*, R2-*, R3-001/002/003/005/006, R6-003/004/006 |
| Tier 3 | Requires infrastructure (mTLS, detached signatures, Merkle ledger) | R0-005, R3-004, R6-001/002/005/007 |
| Tier 4 | Meta-conformance; requires secondary harness | R7-001, R7-002, R7-005, R7-006 |

Implementations MUST declare which tiers they claim to conform to. A Tier 1 conformance claim is not equivalent to a Tier 3 claim.

---

## 10. Reference Implementation

RFC-0 section 7 designates the TENIR-Gov middleware as the long-term reference. The reg-conformance repository currently tests the standalone kernel under reg-conformance/kernel/. The middleware will be added under reference/ when its kernel tier is extractable.

The current published conformance results are maintained under reg-conformance/results/ with the following conventions:

- Results are versioned with the suite (v0.3.0 or later).
- Each result declares its interface_mode and evidence_level.
- Gaps are reported per tier and per vector, never aggregated into a single "compliance score."

The conformance suite does not assume any specific implementation. Any conforming implementation may publish results under its own identifier.

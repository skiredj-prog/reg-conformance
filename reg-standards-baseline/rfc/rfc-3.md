---
rfc: 3
title: Standing & Authority Continuity
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0, RFC-1]
---

# RFC-3: Standing & Authority Continuity

**Status:** Proposed Standard (Frozen Draft)
**Dependencies:** RFC-0 (Constitution), RFC-1 (Wire Protocol)

**Purpose:** Defines how the Standing dimension ($St_t$) evaluates whether an actor currently possesses the authority to request an action, how that authority is cryptographically bound and preserved, and how multiple authorities compose under collective constraints. It closes the critical gaps of delegation amplification, revocation propagation, and context mutation.

---

## Scope Boundary

RFC-3 defines the continuity and composition of authority. RFC-5 defines how the system remains live when authority or admissibility is suspended. RFC-4 defines how a valid decision becomes an executable, provable commitment.

This RFC does not prescribe IAM implementations, workflow orchestration, or operational recovery mechanics. It defines the properties that such systems must satisfy at the Execution Boundary.

---

## Major Decisions Locked

1. **Identity ≠ Authority Scope ≠ Standing:** authentication (who you are) is distinct from Authority Scope (what you are permitted to request) and from Standing (whether that permission is currently valid, unrevoked, and contextually sound).

2. **Strict Non-Amplification (Algebraic Delegation):** Scope(Child) ⊆ Scope(Parent). Delegation is a strictly monotonic reduction of scope, never an expansion.

3. **Bounded Revocation Guarantee:** a revoked authority MUST NOT remain executable beyond the declared revocation bound. REG standardizes the observable security property, not the internal propagation mechanism.

4. **Four Distinct Invocation Events:** Credential Revocation, Policy Invocation, Context Drift, and Execution Invocation are distinct events with distinct semantics. They MUST NOT be conflated.

5. **Credential vs. Grant vs. Commit Separation:** a Standing Credential may be durable or reusable. An Execution Grant is bound to a specific evaluation. Commit authorization is governed by RFC-4. These are distinct artifacts.

6. **Composition Does Not Rewrite Local Standing:** multi-IAU composition evaluates whether individually valid authorities can coexist under a Composition Invariant. It MUST NOT rewrite, fabricate, or negate local Standing attestations.

7. **Mutation Soundness (Bounded):** material changes that invalidate the basis on which Standing was attested MUST trigger re-valuation. The standard provides examples but does not prescribe a fixed list of mutations.

8. **Authority Recovery Semantics Only:** a suspended authority MAY be re-established only through a new, valid Standing attestation (potentially with reduced scope). Operational recovery mechanics are deferred to RFC-5.

---

## 1. Normative Definitions

**Identity:** the cryptographic binding of the requesting agent (e.g., workload identity, SPIFFE ID, X.509 subject).

**Authority Scope:** the explicit, versioned boundaries of what the agent is permitted to request (action classes, targets, value limits, temporal constraints).

**Standing:** the active, unrevoked, and contextually valid state of possessing a given Authority Scope at time t. Standing is a predicate, not an artifact.

**Standing Credential:** a durable cryptographic artifact (e.g., signed JWT, Verifiable Credential, Zero-Knowledge Proof, signed delegation chain) that attests to Standing. It MAY be reusable across multiple evaluations within its validity window.

**Execution Grant:** a single-use, cryptographically bound authorization linked to a specific `evaluation_id`, `action_id`, `nonce`, and `valid_until` window. The Execution Grant is the artifact consumed at the Commit Point (RFC-4).

**Composition Invariant:** a higher-order rule that governs a group of TAUs. Local Standing is evaluated independently; Composition Admissibility evaluates whether the set of locally valid actions can coexist under the Composition Invariant.

---

## 2. The Standing Attestation & Artifact Model

### 2.1 Credential vs. Grant vs. Commit Separation

| Artifact | Lifespan | Binding | Consumability |
|---|---|---|---|
| Standing Credential | Durable (hours to months) | Agent identity + scope | Reusable within validity |
| Execution Grant | Ephemeral (seconds to minutes) | evaluation_id + action_id + nonce | Single evaluation |
| Commit Authorization | Instantaneous | State hash + nonce | Governed by RFC-4 |

### 2.2 Credential Structure

A conforming Standing Credential MUST contain:

- `issuer`
- `subject` (TAU / agent identifier)
- `scope` (explicit, versioned Authority Scope)
- `not_before` / `expires_at`
- `parent_reference` (if delegated)
- `version` (schema and policy version under which the credential was issued)

### 2.3 Verification Mechanics

The membrane MUST verify the credential's signature and validity using public cryptographic material or local, frequently updated revocation data (e.g., CRLs, Merkle proofs, status lists, epoch watermarks).

The membrane MUST NOT rely on synchronous, real-time IAM database lookups that introduce latency or single points of failure at the Execution Boundary.

### 2.4 Independent Verifiability

A third-party auditor MUST be able to verify a Standing attestation using only the cryptographic artifact and public trust material, without access to the issuer's private IAM logs or internal state.

---

## 3. Delegation Algebra & Non-Amplification

**Monotonic Reduction:** formally Scope(Child) ⊆ Scope(Parent). A child MUST NOT be granted permission to execute an action class, target, or value limit that the parent does not itself possess.

**Chain of Delegation:** the membrane MUST deterministically verify multi-hop delegation chains. If any link is invalid, expired, or revoked, the entire descendant chain is invalidated.

**Conformance Requirement:** any implementation of delegation MUST provide a deterministic, auditable algorithm to prove non-amplification. This property MUST be testable via the conformance suite (RFC-7).

---

## 4. Invalidation Semantics

REG defines four distinct invalidation events. They MUST NOT be conflated.

### 4.1 Event Taxonomy

| Event | Definition | Origin | Consequence |
|---|---|---|---|
| Credential Revocation | The authority itself is withdrawn. The Standing Credential is no longer valid. | Issuer / IAM | All Execution Grants derived from it are invalidated. |
| Policy Invocation | The authority may still exist, but its scope is no longer admissible under current policy. | Policy engine / Risk Owner | Standing is re-evaluated against the new policy. |
| Context Drift | The identity/authority may remain valid, but the conditions under which Standing was attested have materially changed. | Environment / Runtime | Standing attestation is voided; re-evaluation required. |
| Execution Invocation | A previously issued Execution Grant can no longer be used. | Membrane / Structure / Commit | The specific grant is voided. Standing itself may remain valid. |

### 4.2 Bounded Revocation Guarantee

REG does not mandate a specific propagation mechanism. It standardizes the following observable security property:

> **A revoked authority MUST NOT remain executable beyond the declared revocation bound.**

The revocation bound (e.g., `revocation_epoch`, watermark, freshness window) MUST be explicitly declared, versioned, and signed by the Risk Owner.

Acceptable mechanisms include push-based invalidation, short-lived credentials, epoch watermarking, Merkle status proofs, or any other technique that demonstrably satisfies the bound.

**In-flight actions:** if a revocation occurs after an Execution Grant is issued but before or during the Commit Point / Supervised Execution, the membrane MUST trigger a HARD_VETO and instruct the executor to transition to a safe state.

### 4.3 Cascade Mechanics

Revoking a parent credential MUST invalidate all descendant Standing Credentials within the declared revocation bound. The membrane MUST enforce this closure at the Execution Boundary.

---

## 5. Context & Mutation Soundness

### 5.1 Normative Rule

Material identity, execution-context, authority-policy, or declared-agent-state changes that invalidate the basis on which Standing was attested MUST invalidate or trigger re-evaluation of that attestation.

### 5.2 Examples of Material Drift (Non-Exhaustive)

- Switch of execution environment (e.g., sandbox → production).
- Change in the underlying model weights or prompt version if and only if the Standing Credential was explicitly bound to that specific version.
- Change in the declared risk profile or deployment scope of the TAU.

### 5.3 Separation from Structure

Context Drift (Standing) is distinct from State/Environment Drift (Structure / P, V, K). Both can independently trigger re-evaluation or HOLD, but they are evaluated by different dimensions and produce attestations in different sections of the EGE.

---

## 6. Multi-TAU Composition & Authority Continuity

### 6.1 Core Principle — Two Independent Questions

**Local Standing:** "Does this TAU possess the authority required for this action?"

**Composition Admissibility:** "Can the set of individually standing-valid actions coexist under the Composition Invariant?"

**Crucial Rule:** composition evaluates the coexistence of valid authorities. It MUST NOT rewrite, upgrade, or downgrade a local Standing attestation.

**Correct example:**
- TAU A: Standing = PASS
- TAU B: Standing = PASS
- Composition Invariant violated → Composition disposition = HOLD (or HARD_VETO)
- Local Standing attestations remain PASS

### 6.2 Conflict Taxonomy (C1–C4)

- **C1 (Vertical):** local Standing valid, but Composition Invariant violated.
- **C2 (Horizontal):** peer TAUs with valid local Standing conflict over a shared resource.
- **C3 (Temporal):** sequence of individually valid actions collectively violates an invariant.
- **C4 (Priority Absent):** tension with no declared rule of precedence.

### 6.3 Resolution Strategies

The Composition Manifest MUST declare a priority convention and resolution strategy. Permitted strategies include (non-exhaustive):

- Serialize
- Pareto-Restore
- Escalate
- Fail-Closed Collectif

These strategies govern execution ordering and resource allocation, not the truth value of local Standing attestations.

### 6.4 Composition Liveness Window ($\tau_K^{comp}$)

The composition MUST declare a bounded collective liveness window ($\tau_K^{comp}$) and the method by which it is derived.

$$\tau_K^{comp} = \max(\tau_K \text{ of children}) + \text{arbitration margin}$$

This construction MAY be used as a reference method where its safety and liveness properties are established. It is not a normative universal formula. The declared value and its derivation method MUST be signed by the Composition Risk Owner (or equivalent).

If $\tau_K^{comp}$ expires on an unresolved conflict, the membrane applies Fail-Closed Collectif to the Execution Grants of the involved TAUs while preserving their underlying Standing Credentials.

### 6.5 Priority Convention

Manifests MUST declare a priority convention (e.g., lower integer = higher priority). Priority informs resolution strategies but does not override or rewrite local Standing evaluations.

### 6.6 Reference Implementation

A readable, local reference implementation of the strategy-dispatch and conflict-resolution logic is published at [`reg-conformance/composition/simulator.py`](../../composition/simulator.py). Its scope and limitations are documented in [`composition/README.md`](../../composition/README.md). It is not a conformance suite and does not constitute an empirical validation of RFC-3.

---

## 7. Authority Recovery Semantics

### 7.1 Normative Rule

An authority that has been suspended (HOLD) or invalidated (HARD_VETO) MAY be re-established only through a new, valid Standing attestation. The new attestation MAY carry a strictly reduced Authority Scope (progressive degradation), provided this reduction was pre-declared in the Decision Policy and proven to preserve the core Invariant.

### 7.2 Scope of RFC-3 vs. RFC-5

RFC-3 defines what constitutes a valid re-establishment of Standing. RFC-5 defines how the system operationally manages recovery (queuing, cooldowns, escalation, backlog management).

---

## 8. Interoperability, Verifiability & Conformance

### 8.1 Independent Verifiability

A third-party auditor MUST be able to verify the Standing Credential and the non-amplification chain using only the artifact and public cryptographic material.

### 8.2 Required Conformance Tests (RFC-7)

1. **Non-Amplification:** attempt to delegate broader scope than parent → HARD_VETO.
2. **Revocation Bound:** revoke parent and attempt to use descendant beyond the bound → HARD_VETO.
3. **Mutation Soundness:** alter bound context mid-flight → re-evaluation or HOLD.
4. **Composition Independence:** composition-level HOLD/HARD_VETO does not rewrite local Standing attestations.
5. **Credential / Grant Separation:** replay of an Execution Grant is rejected; the underlying Standing Credential remains usable for new evaluations.

### 8.3 Implementation Gap Tracking

Implementations MUST explicitly document which proof obligations are fully engineered and which remain IMPLEMENTATION GAP.

---

## 9. The Four Independent Questions of REG (Summary)

| Question | Dimension | RFC |
|---|---|---|
| "Does this unit still have the right to act?" | Local Standing | RFC-3 |
| "Can these units act together without violating the collective invariant?" | Composition Admissibility | RFC-3 (§6) |
| "Does the current state of the system permit this action?" | Structure | RFC-2 |
| "Can this specific action now cross the boundary and be proven as such?" | Commit | RFC-4 |

These four questions are evaluated independently. Their dispositions are composed via the deterministic rule defined in RFC-0: the most restrictive applicable disposition governs.
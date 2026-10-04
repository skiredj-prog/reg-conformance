---
rfc: 0
title: Runtime Execution Governance (REG) Standard — Constitution
version: v0.2
status: Frozen
date: 2026-10-03
dependencies: []
---

# RFC-0: Runtime Execution Governance (REG) Standard

**Status:** Proposed Standard (Frozen Draft)
**Domain:** AI Safety, Autonomous Systems, Execution Boundaries
**Origin:** Open standard derived from the convergence of TENIR-Gov, CCEAF, and CommitGate architectures.

---

## 1. Introduction and Scope

As autonomous agents transition from generating text to executing consequential actions in the real world, a critical vulnerability emerges at the threshold where a system's proposal becomes an irreversible effect. Traditional governance (policy engines, identity management, post-hoc monitoring) terminates at authorization. It does not survive to the millisecond the external consequence becomes effective.

Runtime Execution Governance (REG) is the discipline and architectural standard that intercepts, evaluates, and controls this boundary. Its core mantra is:

> **The agent proposes. The membrane decides. Authorised / Admissible.**

### Editorial Principle

REG standardizes the execution boundary and its proof obligations, not the internal architecture used to implement them.

This RFC defines the canonical vocabulary, the independent admissibility dimensions, the verdict dispositions, and the action lifecycle. It deliberately separates the semantics of the boundary from the topology of the implementation.

---

## 2. Canonical Vocabulary

To prevent category fragmentation, the following terms are defined as the standard lexicon for REG:

**Execution Boundary:** The fundamental object of REG. The boundary at which a proposed consequential action may become an external effect.

**Consequential Action:** Any action that modifies external state, moves value, or produces non-trivially reversible effects. Rule of prudence: in doubt, it is consequential.

**Constitutional Membrane:** The logical and technical surface that intercepts all consequential actions before they cross the Execution Boundary.

**Structural Admissibility:** The property of an action being compatible with the real-time structural state of the system (capacity, pressure, volatility). Distinct from static policy compliance.

**Fail-Closed:** The default behavior of the membrane. In case of uncertainty, timeout, or component failure, the action is blocked.

---

## 3. The Three Admissibility Dimensions (The "WHAT")

REG evaluates three independent admissibility dimensions at the execution boundary. These are independent state evaluations (predicates) over the same execution attempt:

$$\mathbf{A} = f(\mathbf{St}_t, \mathbf{S}_t, \mathbf{C}_t)$$

Where:

- **$St_t$ (Standing):** Does this actor currently possess the authority to request this action? Evaluates identity, delegation, non-amplification, revocation closure.
- **$S_t$ (Structure):** Is the action admissible under the current system state and constraints? Evaluates dynamic capacity, pressure, volatility, invariant compliance.
- **$C_t$ (Commit):** Can the evaluated action become the exact external effect without losing the integrity of the decision? Evaluates atomicity, non-replayability, cryptographic binding.

### Topological Independence

While an implementation may evaluate these dimensions sequentially for computational efficiency, this standard does not prescribe a sequential pipeline topology. Implementations may evaluate them in parallel, via distributed consensus, or through a unified mathematical model. The standard only requires that the final state A is deterministically composed from $St_t$, $S_t$, and $C_t$.

---

## 4. Verdict Semantics & Dispositions (The "OUTCOME")

The membrane evaluates the execution attempt and returns exactly one of four final execution dispositions. These are not numerical states on a scalar hierarchy; they are distinct adjudication outcomes.

| Disposition | Definition | Execution Instruction |
|---|---|---|
| **PASS** | Execution may proceed within the validity boundary. | ALLOW (bounded by `valid_until` and state drift). |
| **FLAG** | Execution may proceed only under an explicitly defined additional condition or supervision. | ALLOW_WITH_MONITORING (never a bare ALLOW). |
| **HOLD** | Execution is suspended pending resolution or human adjudication. | SUSPEND (triggers the τ_K exhaustion timer). |
| **HARD_VETO** | Execution is categorically refused for this evaluation. | BLOCK (generates a signed refusal receipt). |

### Deterministic Conflict Resolution

Because the three dimensions are evaluated independently, they may theoretically produce conflicting dispositions. The standard resolves this via strict set-based restriction, not a numerical hierarchy:

> **When multiple applicable controls produce incompatible dispositions, the most restrictive applicable disposition governs.**

Example: If Standing yields PASS, Structure yields FLAG, and Commit yields HOLD, the final disposition is HOLD. If any dimension yields HARD_VETO, the final disposition is HARD_VETO.

---

## 5. The Action Lifecycle (The "WHEN")

The lifecycle describes the temporal progression of a consequential action, separate from the adjudication model. It consists of four phases:

1. **Pre-Execution:** The proposing agent submits an EvaluationRequest containing the action intent, target, expected effects, and a snapshot of the runtime state.

2. **Conditional Authorization:** The membrane returns the verdict and the Execution Grant Envelope (EGE). A PASS is never permanent; it is strictly bounded by a `valid_until` timestamp and is invalidated by material state changes.

3. **Supervised Execution:** The executor sends sequenced ExecutionEvent signals. If a HARD_VETO is triggered during this phase (e.g., via state drift detection), execution must halt or transition to a safe state.

4. **Closure & Proof:** Upon completion, abortion, or rollback, the membrane generates an EvidenceManifest, anchoring the cryptographic proof of the entire lifecycle to an immutable ledger.

---

## 6. Liveness, τ_K, and the Exhaustion Policy

A HOLD verdict cannot last indefinitely without causing operational paralysis (Liveness Failure).

**τ_K (Organizational Veto Window):** The maximum time allowed for human resolution. τ_K is never invented; it is derived empirically from existing organizational SLAs (e.g., on-call response + human review time + documented margin).

**Exhaustion Policy:** If τ_K expires on a HOLD, the system executes a pre-declared policy. The default is Fail-Closed (reject the action). A Fail-Degraded policy (e.g., queueing, capping) is permitted only if it was pre-declared by the Risk Owner at design time and mathematically proven to preserve the core invariant.

---

## 7. Proof Obligations vs. Implementation Status

A critical distinction of the REG standard is the separation of normative requirements from implementation status.

**Normative Requirements (The Standard):** RFC-0 through RFC-6 define what MUST be true. For example: "Delegated authority SHALL NOT exceed the authority of its parent" (Non-Amplification).

**Implementation Status (The Reference):** The reference implementation (TENIR-Gov) is subject to conformance testing. If the current implementation has not yet fully engineered a specific proof obligation, it is flagged as **NON-CONFORMANT / IMPLEMENTATION GAP** until resolved.

This separation ensures that REG remains a rigorous, objective standard, rather than a marketing document for a specific software product. RFC-7 defines the conformance suite used to prove whether an implementation actually satisfies the standard's claims.

---

## 8. The REG RFC Dependency Map

RFC-0 establishes the semantic and normative baseline. The technical and operational specifications are deferred to subsequent RFCs:

- **RFC-0:** Constitution (this document)
- **RFC-1:** The Execution Grant Envelope (EGE) & Wire Protocol
- **RFC-2:** Structural Admissibility (Constraint Geometry & Invariants)
- **RFC-3:** Standing & Authority Continuity (Delegation & Revocation)
- **RFC-4:** Commit & Execution Proof (Atomicity & Ledger Anchoring)
- **RFC-5:** Liveness & Operationalization (τ_K & Exhaustion)
- **RFC-6:** Security, Transport & Cryptography
- **RFC-7:** Conformance Suite & Interoperability
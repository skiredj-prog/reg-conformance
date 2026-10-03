---
rfc: 5
title: Liveness & Operationalization
version: v0.1
status: Frozen
date: 2026-10-03
dependencies: [RFC-0, RFC-1, RFC-3]
---

# RFC-5: Liveness & Operationalization

**Status:** Proposed Standard (Draft)
**Dependencies:** RFC-0 (Constitution), RFC-1 (Wire Protocol), RFC-3 (Standing)

**Purpose:** Translates the architecture into operational reality. Defines how τ_K is derived, how the exhaustion policy is declared, how Shadow Mode is bounded, how recovery establishes a new authorization context, and how adoption maturity is measured.

---

## Major Decisions Locked

1. **τ_K is Derived, Never Invented:** The Organizational Veto Window (τ_K) must be empirically derived from existing, documented organizational SLAs.

2. **Pre-Declared Exhaustion Policy:** The behavior when τ_K expires on a HOLD must be declared and signed by the Risk Owner at design time. The default is Fail-Closed. Fail-Degraded is permitted only if supported by a documented, independently reviewable argument that the core invariant remains satisfied. Degradation is never chosen ad-hoc during a crisis.

3. **Shadow Mode Entry Criterion:** Shadow Mode MUST NOT be activated without explicitly allocated, bounded, and latency-proven human review capacity.

4. **Recovery as New Authorization:** Reinsertion of a blocked TAU establishes a new valid Standing/Structure/Commit context; it is never an automatic continuation of a suspended authorization.

5. **Progressive Deployment Maturity:** Conformance (satisfying normative requirements) is distinct from Maturity (the breadth and capability of the deployment).

---

## 1. The τ_K Derivation Method

The Organizational Veto Window (τ_K) represents the maximum time the organization has to understand a situation and exercise its veto before the system must act autonomously to preserve liveness or safety.

### 1.1 Derivation Principle

> **τ_K is derived from organizational reality; it is not invented.**

The derivation of τ_K for a specific TAU and action class MUST identify the applicable organizational response constraints and MUST document the binding constraint used to establish τ_K.

**Reference Method:** Where multiple constraints apply, selecting the most restrictive (shortest) applicable time is the recommended reference method.

**Justification & Reproducibility:** The selected constraint MUST be justified based on the specific risk profile of the action class, and the derivation process MUST be reproducible by an independent auditor.

Sources to consider (non-exhaustive):
- on-call response SLA for incidents of comparable criticality,
- contractual or regulatory notification/escalation time,
- observed crisis cell assembly time,
- human review SLA already applied to actions of the same class,
- reaction windows imposed by regulation.

### 1.2 Multi-TAU Composition τ_K

For composed TAUs, the collective τ_K ($\tau_K^{comp}$) MUST be explicitly declared in the Composition Manifest. The derivation MUST account for arbitration latency and collective decision-making overhead.

---

## 2. Exhaustion Policies (Fail-Closed vs. Fail-Degraded)

When a HOLD verdict reaches the end of its τ_K window without human resolution, the system must execute a pre-declared Exhaustion Policy.

### 2.1 Fail-Closed (The Default)

**Definition:** The suspended action is categorically rejected (HARD_VETO).

**Requirement:** This is the mandatory default behavior for all action classes unless an explicit, signed exception is made.

### 2.2 Fail-Degraded (The Exception)

**Definition:** The action is permitted to proceed in a restricted, lower-risk form (e.g., amount capped, queued for the next business window).

**Strict Requirements:** A Fail-Degraded policy is ONLY permissible if:

1. It is explicitly pre-declared in the Decision Policy manifest for that specific action class.
2. It is signed by the designated Risk Owner.
3. It is supported by a documented and independently reviewable argument demonstrating that the declared invariant remains satisfied. Where the invariant admits formal verification, formal proof SHOULD be used.

**Prohibition:** Degradation parameters MUST NOT be chosen or adjusted ad-hoc during an incident.

---

## 3. Shadow Mode & Review Capacity Bounds

Shadow Mode (evaluating actions and generating verdicts without blocking execution) is a critical phase for calibration.

### 3.1 The Entry Criterion

> **No Shadow Mode without allocated, bounded, and latency-proven review capacity.**

Before activating Shadow Mode, the organization MUST declare and provision:

- `nominal_reviewers` and `available_reviewers`: Human resources assigned to review HOLDs.
- `max_hold_backlog`: The absolute maximum number of unreviewed HOLDs tolerated.
- `daily_review_budget_min`: Minimum time allocated per day.
- `max_review_latency`: The maximum acceptable time between HOLD generation and human review.

### 3.2 Boundedness Proof

The deployment MUST demonstrate that the HOLD generation rate will not exceed the review capacity within the permitted `max_review_latency`. If the `max_hold_backlog` is exceeded, the system MUST tighten the Admissible Region, reduce the TAU's operational scope, or explicitly increase allocated capacity.

---

## 4. Progressive Recovery & Reinsertion Semantics

A HOLD or localized Fail-Closed state must not lead to permanent operational paralysis.

### 4.1 Recovery as New Authorization

Reinsertion of a suspended TAU MUST establish a new valid Standing, Structure, and Commit context. It MUST NOT be treated as an automatic continuation or resumption of the previously suspended authorization.

### 4.2 Authority Degradation

Reinsertion MAY be granted with a strictly reduced Authority Scope (e.g., lower velocity, reduced limits). This degraded scope MUST be defined as a valid sub-region within the original Admissible Region.

---

## 5. Progressive Deployment Maturity

To prevent overwhelming adopters, REG separates binary normative conformance from the breadth of deployment. REG defines a 6-level Deployment Maturity Ladder.

| Level | Name | Requirements |
|---|---|---|
| 0 | Defined | 1 TAU, 1 Invariant, and Consequential Actions explicitly declared. |
| 1 | Observable | Shadow Mode active. Allocated review capacity proven. Structured Decision Records logged. |
| 2 | Controlled | At least one Consequential Action class is actively Enforced (HARD_VETO applied). |
| 3 | Evidenced | Decision Records are cryptographically anchored and independently replayable. |
| 4 | Calibrated | τ_K and Constraint Geometry thresholds are empirically tuned against real operational data. |
| 5 | Composed | Multi-TAU arbitration is active, with declared conflict resolution strategies and collective τ_K enforcement. |

---

## 6. Reference Deployment Artifacts

To claim Level 1+ Deployment Maturity, a deployment MUST provide sufficient equivalent evidence for the following seven governance functions. The exact file names and serialization formats are RECOMMENDED reference formats, not mandatory identifiers. Alternative formats (JSON, database records, signed policy bundles) are permitted provided they fulfill the functional requirements:

1. **TAU Declaration**
2. **Invariant Definition**
3. **Admissible Region**
4. **τ_K Derivation**
5. **Decision Policy** (including Exhaustion rules)
6. **Operator Runbook**
7. **Decision Record Schema**
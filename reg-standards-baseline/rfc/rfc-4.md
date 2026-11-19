---
rfc: 4
title: Commit & Execution Proof
version: v0.3
status: Draft (awaiting ratification by the author; v0.2 stays the frozen text until then)
date: 2026-11-19
supersedes: v0.2
incorporates:
  - RN-001 (FLAG admission, elapsed time, and state drift at commit), ratified 2026-11-18
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

7. **Elapsed Time: Fail-Safe Bound vs. Epistemic Input (v0.3)** — A bound the
   policy declares fail-safe refuses alone; any other elapsed time is an
   epistemic input to readjudication. The age of a verdict already rendered
   (`PASS` or `FLAG`) is not, by itself, a gate: past the policy's freshness
   threshold it requires a fresh adjudication in which that age is one input
   among the others, and it can only make the disposition more restrictive.
   τ_K, the bound on waiting for a human resolution of a `HOLD` (RFC-0 §6,
   RFC-5 §1), is a fail-safe bound (§2.3, §7).

8. **Outcome, Not Label, on State Drift (v0.3)** — On a change of governance
   state between verdict and commit, REG requires no effect under the changed
   state and a reported state class: a terminal refusal, or a suspension with a
   declared resumption condition. `HARD_VETO` is one terminal refusal; REG does
   not impose it (§2.2).

---

## 1. The Commit Boundary & Binding Property

### 1.1 Commit Binding Property

A conforming implementation MUST ensure that an Execution Grant cannot be
successfully consumed for an effect that is outside its declared binding, validity
window, or commit conditions.

**What REG Controls:**

- The grant is bound to a specific `evaluation_id`, `action_id`, and `nonce`.
- The grant can be consumed as is only within the `valid_until` window. In v0.3,
  `valid_until` is the policy's freshness threshold for that verdict (§2.3):
  past it, no effect follows from the grant without a fresh adjudication that
  includes the verdict's age.
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
the commit MUST NOT produce an effect (required outcome below).

The tolerance (or equivalent acceptance criteria for alternative binding
mechanisms) is part of the versioned policy and threshold configuration and is
subject to change control.

**Alternative Mechanisms** (provided they satisfy the same security property):

- Version/Epoch
- Optimistic Concurrency Token
- Transaction Identifier
- Resource Version

If the state changes after the verdict but before commit, the binding mechanism
MUST detect this. The required outcome is (RN-001 §4):

> No effect under a changed governance state, and the reported state class:
> either a terminal refusal, or a suspension with a declared resumption
> condition.

`HARD_VETO` is the reference terminal refusal. An implementation that suspends
instead MUST declare the resumption condition in the Suspension Receipt
(§3.2). A suspension without a declared resumption condition does not satisfy
this clause.

*Changed from v0.2, which read "MUST detect this and trigger HARD_VETO". REG
describes the outcome; it does not prescribe the mechanism.*

### 2.3 Elapsed Time at Commit (v0.3)

This section separates two objects that v0.2 did not distinguish (RN-001 §2).

**2.3.1 Fail-safe bound.** A bound that the versioned policy declares
fail-safe refuses alone when it is exhausted. It is never invented by the
implementation (RFC-0 §6, RFC-5 §1). Its exhaustion applies the pre-declared
exhaustion policy (RFC-5 §2) wherever the bounded operation could advance, and
this MUST NOT depend on a timer firing. τ_K on a `HOLD` is such a bound when the
policy supplies it.

**2.3.2 Verdict age.** Any other elapsed time, in particular the age of a
verdict already rendered (`PASS` or `FLAG`), is an epistemic input. It does not
refuse alone. Where it reaches the policy's freshness threshold (for the grant,
`valid_until`):

1. **No dispatch on a stale verdict.** No effect follows from that verdict
   without a fresh adjudication that includes the verdict's age as an input.
   Refusing the commit (`REJECT` / `EVALUATION_EXPIRED`) is the reference
   outcome when no fresh adjudication takes place.
2. **One direction.** All else equal, the fresh adjudication is never less
   restrictive because the verdict is older. Age acts as a modulator that
   contracts the admissible region (RFC-2 §3.4, one-way hardening); it is not a
   term that a strong score elsewhere can buy back.
3. **Recorded.** A fresh adjudication is a disposition: it produces its own
   Decision Receipt (§3), which records the verdict age that entered it. A
   readjudication that leaves no receipt is indistinguishable from a dispatch
   on a stale verdict and is treated as one.

**2.3.3 When age is fail-safe.** Verdict age refuses alone only where the
policy declares the freshness threshold fail-safe for that action class. The
policy SHOULD do so where proceeding on a verdict of that age could threaten a
declared invariant or a fail-safe property; the declaration follows the same
change control as the other thresholds (§2.2).

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
| HOLD | Suspension Receipt | Proof of suspension with triggering conditions, τ_K when the policy supplies it, and the resumption condition when the suspension follows a state change (§2.2) |
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
4. CT-R4-004 — Stale Grant, Refusal Branch (rewritten in v0.3): `valid_until` passed before commit and no fresh adjudication presented → no effect; REJECT / EVALUATION_EXPIRED is the reference outcome. An effect without a recorded fresh adjudication fails the vector (§2.3.2). As a normative anchor, CT-R4-004 is superseded by CT-R4-014 to CT-R4-016 (RN-001 §3); it stays registered with its results.
5. CT-R4-005 — Commit-State Binding / Race Detection: state at commit materially differs from state captured at verdict (state_hash_at_verdict or equivalent) → no effect under the changed state; terminal refusal, or suspension with a declared resumption condition (§2.2, RN-001 §4)
6. CT-R4-006 — Non-PASS Cannot Cross Commit: HOLD or HARD_VETO disposition → commit attempt → REJECT / INVALID_DISPOSITION
7. CT-R4-007 — Decision Receipt Generation: every disposition (including non-PASS) produces a cryptographically signed Decision Receipt, independently verifiable without accessing internal state
8. CT-R4-008 — Evidence Manifest Integrity: Evidence Manifest altered after closure → integrity verification fails. Requires tamper-evident, append-only ledger.
9. CT-R4-009 — Independent Evidence Verification: third-party verifier can reproduce or verify the decision from the Manifest without accessing mutable internal state
10. CT-R4-010 — External-Effect Claim Boundary: implementation provides post-commit evidence for non-atomic external effects and does NOT claim atomic external-effect semantics
11. CT-R4-014 — No Dispatch on a Stale Verdict: verdict older than the policy's freshness threshold → no effect without a fresh adjudication that includes the verdict's age (§2.3.2 item 1)
12. CT-R4-015 — Age Never Improves a Disposition: same inputs readjudicated at a greater verdict age → equal or more restrictive disposition (§2.3.2 item 2)
13. CT-R4-016 — Fail-Safe Bound Refuses Alone: a bound the policy declares fail-safe (e.g. τ_K on a HOLD) is exhausted, all other inputs favourable → no effect; the pre-declared exhaustion policy applies wherever the operation could advance, without a timer (§2.3.1)

Identifiers are stable labels: CT-R4-011 to CT-R4-013 are lifecycle vectors
filed under this prefix but resting on the manuscript, not on this RFC (see
`VECTORS.md`). Items 11 to 13 above are new normative anchors in v0.3.

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
| Race Soundness | Does the decision remain valid in the face of state changes and elapsed time? |
| Evidence Integrity | Can we prove after the fact what was decided, under which bindings, and what execution evidence was recorded? |

RFC-3 protects the continuity of authority. RFC-4 protects the integrity of the
passage from authority to effect.

---

## 7. Reconciliation: τ_K and Verdict Age (informative)

Both objects measure time, which is why they were confused. They bound
different things:

| | τ_K (§2.3.1) | Verdict age (§2.3.2) |
|---|---|---|
| What it bounds | The **absence** of a decision: how long a `HOLD` may wait for a human resolution | The **age** of a decision already rendered (`PASS`, `FLAG`) |
| Source | Policy, derived from organizational SLAs (RFC-5 §1); never invented | Policy freshness threshold (`valid_until`) |
| On exhaustion | Refuses alone: pre-declared exhaustion policy, default Fail-Closed (RFC-5 §2) | Does not refuse alone: requires a fresh adjudication in which age is one input, and only hardens |
| Exception | Fail-Degraded only if pre-declared and signed (RFC-5 §2.2) | Refuses alone only if the policy declares it fail-safe (§2.3.3) |
| Vector | CT-R4-016; RFC-7 Liveness & Exhaustion | CT-R4-004 (refusal branch), CT-R4-014, CT-R4-015 |

Consequences:

- A human approval or resolution that arrives after τ_K is exhausted does not
  revive the `HOLD`. The held operation has no admission whose age could be
  weighed; the bound that governs it is fail-safe. An implementation that fails
  closed on a late resolve, a late exit approval, or a dispatch of an operation
  whose τ_K is exhausted conforms to §2.3.1 and does not contradict §2.3.2.
- The converse does not hold: an implementation MUST NOT apply a fail-safe
  refusal to the age of a `PASS` or `FLAG` unless the policy declares that
  threshold fail-safe (§2.3.3).
- When the policy supplies no τ_K, the implementation MUST NOT invent one
  (RFC-0 §6). CT-R4-016 is then not applicable to that `HOLD`, and the report
  says so.

Application to one runtime (informative, not a conformance statement):
TENIR-Gov issue #140 reports that in 5.7.0 an exhausted τ_K does not stop a
`HOLD` from advancing through `resolve_hold`, `authorize_exit(approve=True)` or
`dispatch`. A correction that fails closed at those advance points when a
policy-supplied τ_K is exhausted, and that leaves τ_K unset when the policy
supplies none, is consistent with §2.3.1. It is not an application of
CT-R4-004: the vector that covers it is CT-R4-016.

Terminology: this RFC uses τ_K only in the sense of RFC-0 §6 and RFC-5 §1, with
τ_K^comp (RFC-3 §6.4) as its composition variant. The bound that manuscript
v7.2 writes τ_K for waiting on a qualifying receipt (`AWAITING` → `UNKNOWN`) is
a different object, named τ_R in the REG glossary; RFC-4 does not define it.

---

## Changes from v0.2

- Major Decisions 7 and 8 added; §2.3 and §7 added.
- §1.1: `valid_until` read as the policy's freshness threshold.
- §2.2: required outcome on state drift replaces the `HARD_VETO` label (RN-001 §4).
- §3.2: Suspension Receipt carries τ_K when supplied and the resumption condition after a state change.
- §5.2: CT-R4-004 rewritten as the refusal branch and marked superseded as an anchor; CT-R4-005 expected outcome aligned on RN-001 §4; CT-R4-014 to CT-R4-016 added.
- No recorded result changes. RN-001 stays in force as the record of the decision.

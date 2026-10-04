# REG Vector Index

This index points to normative properties in the RFCs; it does not replace them. Status reflects the current repository source, not a historical result or a claim of conformance.

**Inventory note:** the current `runner.py` registry contains 15 IDs (C1–C5 and CT-R4-001–010). CT-R4-009 and CT-R4-010 are registered but return an implementation-gap result without exercising the property. The other 38 extended IDs below occur in the saved v0.3.1 reports but are absent from the current runner. They are indexed under the `CT-RX` namespace with their historical IDs retained in `location`.

| vector_id | family | rfc | normative_property | status | location |
|---|---|---|---|---|---|
| C1 | CORE | RFC-3 | Invalid standing must yield HARD_VETO regardless of structural state. | IMPLEMENTED | `runner.py` VECTORS / `_v_c1`; RFC-3 §2–4 |
| C2 | CORE | RFC-2 | Extreme structural pressure must not yield PASS. | IMPLEMENTED | `runner.py` VECTORS / `_v_c2`; RFC-2 §3 |
| C3 | CORE | RFC-4 §2.2; RFC-3 §4.2 | Revocation after verdict and before commit must yield HARD_VETO and block commit. | IMPLEMENTED | `runner.py` VECTORS / `_v_c3`; `shim.py` `commit_event`; RFC-4 §2.2; RFC-3 §4.2 |
| C4 | CORE | RFC-1 §1, §5; RFC-6 §1.2 | Transport uncertainty must fail closed and must not authorize execution. | IMPLEMENTED | `runner.py` VECTORS / `_v_c4`; HTTP is adapter-required and native is not applicable |
| C5 | CORE | RFC-1 §4; RFC-6 §3.1 | Reuse of an idempotency key/nonce with a different request must be rejected. | IMPLEMENTED | `runner.py` VECTORS / `_v_c5`; RFC-1 §4; RFC-6 §3.1 |
| CT-R4-001 | COMMIT | RFC-4 §1, §1.2 | A valid grant binds evaluation, action, nonce, and commit within its validity window. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_001`; RFC-4 §1 |
| CT-R4-002 | COMMIT | RFC-4 §1.1, §1.3 | Commit for an action different from the granted action must be rejected. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_002`; RFC-4 §1.1–1.3 |
| CT-R4-003 | COMMIT | RFC-4 §2.1 | A consumed nonce or grant must not be replayable. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_003`; RFC-4 §2.1 |
| CT-R4-004 | COMMIT | RFC-4 §2 | An expired grant must not authorize commit. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_004`; RFC-4 §2 |
| CT-R4-005 | COMMIT | RFC-4 §2.2 | Relevant state drift between verdict and commit must be detected and trigger HARD_VETO. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_005`; `shim.py` `commit_event`; RFC-4 §2.2 |
| CT-R4-006 | COMMIT | RFC-4 §1 | HOLD or HARD_VETO must not cross the commit boundary. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_006`; RFC-4 §1 |
| CT-R4-007 | COMMIT | RFC-4 §3 | Every disposition must produce a signed, independently verifiable Decision Receipt. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_007`; RFC-4 §3 |
| CT-R4-008 | COMMIT | RFC-4 §4 | Evidence manifest integrity must be verifiable and tampering detectable. | IMPLEMENTED | `runner.py` VECTORS / `_v_ct_r4_008`; RFC-4 §4 |
| CT-R4-009 | COMMIT | RFC-4 §4.3–4.4 | An independent verifier must be able to verify/reproduce the decision using the declared evidence class. | DECLARED | `runner.py` `_v_ct_r4_009` is a gap stub; RFC-4 §4.3–4.4 |
| CT-R4-010 | COMMIT | RFC-4 §1.1 | Non-atomic external effects require post-commit evidence; implementation must not claim atomicity. | DECLARED | `runner.py` `_v_ct_r4_010` is a gap stub; RFC-4 §1.1 |
| CT-RX-0-001 | INTEGRATION | RFC-0 §7 | The conformance record must identify the normative basis for the claimed property. | RESERVED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R0-001`); no RFC-0 policy-anchor-hash endpoint requirement found |
| CT-RX-0-002 | INTEGRATION | RFC-0 §7; RFC-7 §7 | The implementation/conformance report should identify applicable standard versions. | RESERVED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R0-002`); no mandatory version endpoint specified |
| CT-RX-0-003 | INTEGRATION | RFC-5 §6 | A Level 1+ deployment must provide evidence for the seven governance functions. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R0-003`); RFC-5 §6 |
| CT-RX-0-004 | INTEGRATION | RFC-0 §7 | The implementation status must be distinguished from normative requirements and conformance results. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R0-004`); RFC-0 §7 |
| CT-RX-0-005 | INTEGRATION | RFC-0 §4; RFC-2 §3.3 | The most restrictive applicable disposition governs; invariant violations bypass scoring and veto. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R0-005`); RFC-0 §4; RFC-2 §3.3 |
| CT-RX-1-001 | INTEGRATION | RFC-1 §3 | The EGE must carry the required independent attestations and validity/invalidation context. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-001`); RFC-1 §3 |
| CT-RX-1-002 | INTEGRATION | RFC-1 §5 | Error responses must use application/problem+json semantics. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-002`); RFC-1 §5 |
| CT-RX-1-003 | INTEGRATION | RFC-1 §5 | The client must fail closed on protocol errors and transport uncertainty; retries must not duplicate execution. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-003`); RFC-1 §5 |
| CT-RX-1-004 | INTEGRATION | RFC-1 §5 | A transport timeout must not lead to execution without a verifiable grant. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-004`); RFC-1 §5 |
| CT-RX-1-005 | INTEGRATION | RFC-1 §6; RFC-6 §1.1 | Workload-to-workload transport must use mTLS or equivalent channel authentication. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-005`); RFC-1 §6; RFC-6 §1.1 |
| CT-RX-1-006 | INTEGRATION | RFC-1 §3 | EGE fields and attestations must follow the defined logical structure. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-006`); RFC-1 §3 |
| CT-RX-1-007 | INTEGRATION | RFC-1 §1, §3 | Independent Standing, Structure, and Commit attestations must not depend on implementation internals of another dimension. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R1-007`); RFC-1 §1, §3 |
| CT-RX-2-001 | INTEGRATION | RFC-2 §3 | The applicable thresholds and admissibility rules must be declared and applied consistently. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-001`); RFC-2 §3 |
| CT-RX-2-002 | INTEGRATION | RFC-2 §4.1 | Structural evaluation must be deterministic and reproducible for the same versioned inputs. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-002`); RFC-2 §4.1 |
| CT-RX-2-003 | INTEGRATION | RFC-2 §3.1 | The scoring formula must handle its zero-denominator case deterministically. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-003`); RFC-2 §3.1 |
| CT-RX-2-004 | INTEGRATION | RFC-2 §3 | Exact threshold-boundary behavior must be specified before a conformance test can be defined. | RESERVED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-004`); historical note says boundary behavior is unspecified |
| CT-RX-2-005 | INTEGRATION | RFC-2 §2.2, §3 | Measurements must carry valid ranges and structural evaluation must use provenanced measurements. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-005`); RFC-2 §2.2, §3 |
| CT-RX-2-006 | INTEGRATION | RFC-2 §3; RFC-7 §7 | Any applicable threshold override must preserve normative disposition rules and be auditable. | RESERVED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R2-006`); no threshold-override audit requirement located |
| CT-RX-3-001 | INTEGRATION | RFC-3 §2.2–2.3 | Standing credentials must have the required structure and be checked for signature and validity. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-001`); RFC-3 §2.2–2.3 |
| CT-RX-3-002 | INTEGRATION | RFC-3 §4.2 | Revocation must be enforced within the explicitly declared, versioned, signed revocation bound. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-002`); RFC-3 §4.2 |
| CT-RX-3-003 | INTEGRATION | RFC-3 §2–4 | Standing and invalidation decisions must be evaluated for the correct principal and credential. | RESERVED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-003`); principal-isolation case not specified as a distinct normative vector |
| CT-RX-3-004 | INTEGRATION | RFC-3 §4; RFC-4 §4 | Invalidation and execution events must be represented in the evidence needed for independent audit. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-004`); RFC-3 §4; RFC-4 §4 |
| CT-RX-3-005 | INTEGRATION | RFC-3 §3 | Delegation chains must be checked deterministically; any invalid, expired, or revoked link invalidates descendants. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-005`); RFC-3 §3 |
| CT-RX-3-006 | INTEGRATION | RFC-3 §2.2 | Standing credentials must enforce their `not_before` and `expires_at` validity interval. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-006`); RFC-3 §2.2 |
| CT-RX-3-007 | INTEGRATION | RFC-3 §2.2; RFC-3 §3 | Credential scope must be explicit and delegated scope must not exceed parent scope. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-007`); RFC-3 §2.2–3 |
| CT-RX-3-008 | INTEGRATION | RFC-3 §2.2; RFC-6 §4 | Credential/key rotation and revocation must not leave authorization valid beyond the declared bound. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R3-008`); RFC-3 §2.2; RFC-6 §4 |
| CT-RX-5-001 | INTEGRATION | RFC-1 §2; RFC-4 §4 | The evidence manifest must be retrievable for closure and audit. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R5-001`); RFC-1 §2; RFC-4 §4 |
| CT-RX-5-002 | INTEGRATION | RFC-4 §4.3, §5.1 | A third party must be able to verify exported evidence without mutable internal state. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R5-002`); RFC-4 §4.3, §5.1 |
| CT-RX-5-003 | INTEGRATION | RFC-4 §4 | Evidence must remain tamper-evident and append-only. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R5-003`); RFC-4 §4 |
| CT-RX-5-004 | INTEGRATION | RFC-6 §5 | Governance payloads must exclude raw secrets and minimize PII. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R5-004`); RFC-6 §5 |
| CT-RX-5-005 | INTEGRATION | RFC-4 §4 | Manifest continuity must preserve tamper evidence across appended records. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R5-005`); RFC-4 §4 |
| CT-RX-6-001 | INTEGRATION | RFC-6 §1.1 | Unauthenticated or improperly authenticated workload channels must be rejected. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R6-001`); RFC-6 §1.1 |
| CT-RX-6-002 | INTEGRATION | RFC-6 §2.1–2.2 | Critical payload signatures must bind canonicalized payload bytes and reject tampering. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R6-002`); RFC-6 §2.1–2.2 |
| CT-RX-6-003 | INTEGRATION | RFC-6 §4 | Revoked or rotated keys must not authorize credentials beyond the declared revocation bound. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R6-003`); RFC-6 §4 |
| CT-RX-6-004 | INTEGRATION | RFC-6 §3 | State-changing requests must enforce idempotency and freshness rules. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R6-004`); RFC-6 §3 |
| CT-RX-7-001 | INTEGRATION | RFC-7 §8 | Adapter and native reports must identify separate interface modes and evidence levels. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R7-001`); RFC-7 §8 |
| CT-RX-7-002 | INTEGRATION | RFC-7 §7–8 | Conformance status and evidence level must not be conflated or promoted across interface modes. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R7-002`); RFC-7 §7–8 |
| CT-RX-7-003 | INTEGRATION | RFC-7 §7.2 | A third party may independently review or verify conformance evidence. | DECLARED | `results/tenirlabs-v0.3.1-adapter.json` (legacy `CT-R7-003`); RFC-7 §7.2 |
| VEC-6-01 | SECURITY | RFC-6 §2.2, §6.2 | Signature verification must be based on canonicalized payloads, not JSON formatting. | DECLARED | `reg-standards-baseline/rfc/rfc-6.md` §2.2, §6.2 |
| VEC-6-02 | SECURITY | RFC-6 §3.1, §6.2 | Reuse of an idempotency key with a modified action must be rejected. | DECLARED | `reg-standards-baseline/rfc/rfc-6.md` §3.1, §6.2 |
| VEC-6-03 | SECURITY | RFC-6 §3.2, §6.2 | Requests outside the declared freshness window must be rejected. | DECLARED | `reg-standards-baseline/rfc/rfc-6.md` §3.2, §6.2 |
| VEC-6-04 | SECURITY | RFC-3 §4.2; RFC-6 §4.2, §6.2 | A credential signed by a revoked key past its revocation bound must not authorize execution. | DECLARED | `reg-standards-baseline/rfc/rfc-6.md` §4.2, §6.2 |
| REG-STATE-001 | STATE | RFC-2 §2.5 | UNKNOWN evidence must not be treated as satisfying an invariant; default to HOLD or HARD_VETO. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.5 |
| REG-STATE-002 | STATE | RFC-2 §2.5 | STALE measurements must be excluded; a critical stale measurement yields HOLD or HARD_VETO. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.5 |
| REG-STATE-003 | STATE | RFC-2 §2.5 | MISSING evidence must remain distinguishable from other epistemic states. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.5 |
| REG-STATE-004 | STATE | RFC-2 §2.5 | CONTRADICTORY evidence yields HOLD unless a deterministic, pre-declared resolution applies. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.5 |
| REG-STATE-005 | STATE | RFC-2 §2.5, §2.8 | LOW CONFIDENCE must invoke Conservative Admissibility. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.5, §2.8 |
| REG-STATE-006 | STATE | RFC-2 §2.1 | The membrane must not invent observations; observations without provenance are invalid for structural evaluation. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.1 |
| REG-STATE-007 | STATE | RFC-2 §2.2 | Measurements must carry provenance and required contextual bindings. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.2 |
| REG-STATE-008 | STATE | RFC-2 §2.3 | Interpretations must be produced by deterministic, versioned mappings. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.3 |
| REG-STATE-009 | STATE | RFC-2 §2.4 | Decisions must derive only from Interpretation and applicable Invariants. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.4 |
| REG-STATE-010 | STATE | RFC-2 §2.6 | Prohibited inferences must not be used to establish admissibility. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.6 |
| REG-STATE-011 | STATE | RFC-2 §2.7 | A reason chain must link the decision to interpretations and exact measurements for deterministic reproduction. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.7 |
| REG-STATE-012 | STATE | RFC-2 §2.8 | Uncertainty must be evaluated against worst-case plausible bounds. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.8 |
| REG-STATE-013 | STATE | RFC-2 §2.8 | Increasing uncertainty must never expand the Admissible Region. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §2.8 |
| REG-STATE-014 | STATE | RFC-2 §3.3 | A hard invariant violation must bypass scoring and produce HARD_VETO. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §3.3 |
| REG-STATE-015 | STATE | RFC-2 §3.4 | Confidence modulation may only degrade, never upgrade, the disposition. | DECLARED | `reg-standards-baseline/rfc/rfc-2.md` §3.4 |
| REG-STATE-016 | STATE | RFC-3 §2.3 | Credentials must be checked using public cryptographic material or sufficiently fresh local revocation data. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §2.3 |
| REG-STATE-017 | STATE | RFC-3 §2.3 | Verification must not depend on synchronous real-time IAM lookups at the Execution Boundary. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §2.3 |
| REG-STATE-018 | STATE | RFC-3 §3 | Child authority scope must not exceed parent scope; invalid chain links invalidate descendants. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §3 |
| REG-STATE-019 | STATE | RFC-3 §4.1 | Credential revocation, policy invocation, context drift, and execution invocation must remain distinct events. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §4.1 |
| REG-STATE-020 | STATE | RFC-3 §4.2 | Revocation bounds must be explicit, versioned, and signed. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §4.2 |
| REG-STATE-021 | STATE | RFC-3 §4.2 | Revocation after grant but before/during commit must trigger HARD_VETO and a safe-state transition. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §4.2 |
| REG-STATE-022 | STATE | RFC-3 §4.3, §5.1 | Parent revocation and material authority/context changes must invalidate or trigger re-evaluation of affected standing. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §4.3, §5.1 |
| REG-STATE-023 | STATE | RFC-3 §6, §7; RFC-5 §4 | Composition must preserve local Standing; recovery must establish a new authorization context. | DECLARED | `reg-standards-baseline/rfc/rfc-3.md` §6–7; `reg-standards-baseline/rfc/rfc-5.md` §4 |
| REG-STATE-024 | STATE | RFC-5 §1–3 | τ_K and exhaustion behavior must be pre-declared; HOLD expiry defaults to fail-closed, and Shadow Mode requires bounded review capacity. | DECLARED | `reg-standards-baseline/rfc/rfc-5.md` §1–3 |

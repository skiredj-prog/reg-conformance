# REG Vector Index

This index points to normative properties in the RFCs; it does not replace them. `IMPLEMENTED` means a behavioral test exists in the current runner. `DECLARED` means the RFC specifies the property but the runner does not test it. `RESERVED` means the check is identified but the RFC does not specify it.

The runner registers 53 vector IDs (15 core/commit and 38 extended). Registration alone does not make a vector `IMPLEMENTED`: 36 extended entries currently return an implementation-gap result without exercising the property. The archived v0.3.1 reports also contain false PASS assessments for C3, CT-R4-005, CT-R4-009, and CT-R4-010; use corrected implementation and current report before making conformance claims.

| vector_id | family | rfc | normative_property | status | location |
|---|---|---|---|---|---|
|C1|CORE|RFC-3|Invalid credential → HARD_VETO regardless of structural state.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|C2|CORE|RFC-2|P≥0.9, V≥0.9, K≤0.15 → FLAG or HARD_VETO, never PASS.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|C3|CORE|RFC-4 §2.2|Revocation after verdict but before or during commit must trigger HARD_VETO and block the action. (RFC-4 §2.2; RFC-3 §4.2)|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|C4|CORE|RFC-1|Transport fault → no execution. NOT_APPLICABLE for in-process kernels.|DECLARED|runner.py CORE_VECTORS and adapter dispatch|
|C5|CORE|RFC-1/4|Duplicate nonce → REJECT/NONCE_REPLAY.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-001|COMMIT|RFC-4 §1|Matching evaluation_id/action/nonce within window → GRANT/COMMITTED.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-002|COMMIT|RFC-4 §1.3|Grant for action_A; commit attempts action_B → REJECT/BINDING_VIOLATION.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-003|COMMIT|RFC-4 §2.1|Consumed nonce reused → REJECT/REPLAY_DETECTED.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-004|COMMIT|RFC-4 §2|valid_until passed before commit → REJECT/EVALUATION_EXPIRED.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-005|COMMIT|RFC-4 §2.2|Relevant state drift after verdict and before commit must be detected and trigger HARD_VETO. (RFC-4 §2.2)|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-006|COMMIT|RFC-4 §1|HOLD or HARD_VETO → commit attempt → REJECT/INVALID_DISPOSITION.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-007|COMMIT|RFC-4 §3|Every disposition → cryptographically signed Receipt, independently verifiable.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-008|COMMIT|RFC-4 §4|Append-only hash-chain manifest; integrity verifiable at any time.|IMPLEMENTED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-009|COMMIT|RFC-4 §4|Independent verification must reproduce or verify the decision from recorded inputs, policies, transformations, and attestations. (RFC-4 §4.3, §5.1)|DECLARED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R4-010|COMMIT|RFC-4 §1.1|Non-atomic external effects require post-commit evidence; declaring the effect non-atomic alone is insufficient. (RFC-4 §1.1, §4.1)|DECLARED|runner.py CORE_VECTORS and adapter dispatch|
|CT-R0-001|INTEGRATION|RFC-0|Unspecified proposal: Policy file hash verifiable independently.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R0-002|INTEGRATION|RFC-0|Unspecified proposal: Implementation declares conformant RFC versions.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R0-003|INTEGRATION|RFC-0|Declared scope matches tested behavior.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R0-004|INTEGRATION|RFC-0|Unspecified proposal: All referenced RFCs pinned with SHA/date.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R0-005|INTEGRATION|RFC-0 §4|The most restrictive applicable disposition governs conflicting controls.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-001|INTEGRATION|RFC-1|Unspecified proposal: Response fields match declared schema exactly.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-002|INTEGRATION|RFC-1|Unspecified proposal: Responses declare Content-Type: application/json.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-003|INTEGRATION|RFC-1|2xx/4xx/5xx used per RFC semantics.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-004|INTEGRATION|RFC-1 §5 (timeout window itself unspecified)|Unspecified proposal: server-side request timeout bound; RFC-1 requires fail-closed handling of transport timeout.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-005|INTEGRATION|RFC-1|Non-TLS connections rejected in production mode.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-006|INTEGRATION|RFC-1|Unspecified proposal: Oversized payloads rejected with 413.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R1-007|INTEGRATION|RFC-1|Unspecified proposal: Parallel evaluations do not interfere.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-001|INTEGRATION|RFC-2|Thresholds declared and pinned in policy file.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-002|INTEGRATION|RFC-2|Identical P/V/K → identical S and disposition across independent calls.|IMPLEMENTED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-003|INTEGRATION|RFC-2|Zero-denominator (P=0, V=0) handled without error; epsilon prevents divide-by-zero.|IMPLEMENTED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-004|INTEGRATION|RFC-2|Unspecified proposal: Values at threshold boundaries produce consistent, declared dispositions.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-005|INTEGRATION|RFC-2|Unspecified proposal: P/V/K outside [0,1] rejected with 422.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R2-006|INTEGRATION|RFC-2|Unspecified proposal: Threshold overrides logged with policy_epoch.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-001|INTEGRATION|RFC-3|Malformed credentials rejected before evaluation.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-002|INTEGRATION|RFC-3|Revocation effective within declared latency window.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-003|INTEGRATION|RFC-3|Unspecified proposal: Revocation of A does not affect principal B.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-004|INTEGRATION|RFC-3|Unspecified proposal: All revocation events appended to manifest.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-005|INTEGRATION|RFC-3 §3 (maximum depth itself unspecified)|Unspecified proposal: a fixed maximum delegation-chain depth.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-006|INTEGRATION|RFC-3|Time-limited credentials expire as declared.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-007|INTEGRATION|RFC-3|Standing valid only within declared organizational scope.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R3-008|INTEGRATION|RFC-3|Rotated credentials invalidate prior grants.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R5-001|INTEGRATION|RFC-1 §2; RFC-4 §4.1|The final Evidence Manifest is retrievable for closure and audit.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R5-002|INTEGRATION|RFC-4 §4.3; RFC-4 §5.1|Independent verifier can verify/reproduce the decision from recorded evidence.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R5-003|INTEGRATION|RFC-4 (retention period unspecified)|Unspecified proposal: minimum evidence-retention period.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R5-004|INTEGRATION|RFC-4 §4.2|Evidence manifests are tamper-evident and append-only; closed entries are not silently removed.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R5-005|INTEGRATION|RFC-4 §4.2 (cross-epoch continuity unspecified)|Unspecified proposal: manifest-chain continuity across policy epochs.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R6-001|INTEGRATION|RFC-6 (no override requirement specified)|Unspecified proposal: emergency override audit requirement.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R6-002|INTEGRATION|RFC-6 (no override requirement specified)|Unspecified proposal: override authority validation requirement.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R6-003|INTEGRATION|RFC-6 (no override requirement specified)|Unspecified proposal: override time-window requirement.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R6-004|INTEGRATION|RFC-6 (no override requirement specified)|Unspecified proposal: override receipt requirement.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R7-001|INTEGRATION|RFC-7 §8.1 (mode-specific conformance; exact output equivalence unspecified)|Unspecified proposal: adapter and native outputs must be exactly equivalent.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R7-002|INTEGRATION|RFC-7 §8.2|Adapter evidence must not be promoted to native-conformance evidence.|DECLARED|runner.py EXTENDED_VECTORS and adapter dispatch|
|CT-R7-003|INTEGRATION|RFC-7 §7.2 (cross-implementation agreement not mandated)|Unspecified proposal: independent implementations must agree on outcomes.|RESERVED|runner.py EXTENDED_VECTORS and adapter dispatch|
|VEC-6-01|SECURITY|RFC-6 §2.2, §6.2|Signature verification must be based on canonicalized payloads, not JSON formatting.|DECLARED|`reg-standards-baseline/rfc/rfc-6.md` §2.2, §6.2|
|VEC-6-02|SECURITY|RFC-6 §3.1, §6.2|Reuse of an idempotency key with a modified action must be rejected.|DECLARED|`reg-standards-baseline/rfc/rfc-6.md` §3.1, §6.2|
|VEC-6-03|SECURITY|RFC-6 §3.2, §6.2|Requests outside the declared freshness window must be rejected.|DECLARED|`reg-standards-baseline/rfc/rfc-6.md` §3.2, §6.2|
|VEC-6-04|SECURITY|RFC-3 §4.2; RFC-6 §4.2, §6.2|A credential signed by a revoked key past its revocation bound must not authorize execution.|DECLARED|`reg-standards-baseline/rfc/rfc-6.md` §4.2, §6.2|
|REG-STATE-001|STATE|RFC-2 §2.5|UNKNOWN evidence must not be treated as satisfying an invariant; default to HOLD or HARD_VETO.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.5|
|REG-STATE-002|STATE|RFC-2 §2.5|STALE measurements must be excluded; a critical stale measurement yields HOLD or HARD_VETO.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.5|
|REG-STATE-003|STATE|RFC-2 §2.5|MISSING evidence must remain distinguishable from other epistemic states.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.5|
|REG-STATE-004|STATE|RFC-2 §2.5|CONTRADICTORY evidence yields HOLD unless a deterministic, pre-declared resolution applies.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.5|
|REG-STATE-005|STATE|RFC-2 §2.5, §2.8|LOW CONFIDENCE must invoke Conservative Admissibility.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.5, §2.8|
|REG-STATE-006|STATE|RFC-2 §2.1|The membrane must not invent observations; observations without provenance are invalid for structural evaluation.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.1|
|REG-STATE-007|STATE|RFC-2 §2.2|Measurements must carry provenance and required contextual bindings.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.2|
|REG-STATE-008|STATE|RFC-2 §2.3|Interpretations must be produced by deterministic, versioned mappings.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.3|
|REG-STATE-009|STATE|RFC-2 §2.4|Decisions must derive only from Interpretation and applicable Invariants.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.4|
|REG-STATE-010|STATE|RFC-2 §2.6|Prohibited inferences must not be used to establish admissibility.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.6|
|REG-STATE-011|STATE|RFC-2 §2.7|A reason chain must link the decision to interpretations and exact measurements for deterministic reproduction.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.7|
|REG-STATE-012|STATE|RFC-2 §2.8|Uncertainty must be evaluated against worst-case plausible bounds.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.8|
|REG-STATE-013|STATE|RFC-2 §2.8|Increasing uncertainty must never expand the Admissible Region.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §2.8|
|REG-STATE-014|STATE|RFC-2 §3.3|A hard invariant violation must bypass scoring and produce HARD_VETO.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §3.3|
|REG-STATE-015|STATE|RFC-2 §3.4|Confidence modulation may only degrade, never upgrade, the disposition.|DECLARED|`reg-standards-baseline/rfc/rfc-2.md` §3.4|
|REG-STATE-016|STATE|RFC-3 §2.3|Credentials must be checked using public cryptographic material or sufficiently fresh local revocation data.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §2.3|
|REG-STATE-017|STATE|RFC-3 §2.3|Verification must not depend on synchronous real-time IAM lookups at the Execution Boundary.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §2.3|
|REG-STATE-018|STATE|RFC-3 §3|Child authority scope must not exceed parent scope; invalid chain links invalidate descendants.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §3|
|REG-STATE-019|STATE|RFC-3 §4.1|Credential revocation, policy invocation, context drift, and execution invocation must remain distinct events.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §4.1|
|REG-STATE-020|STATE|RFC-3 §4.2|Revocation bounds must be explicit, versioned, and signed.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §4.2|
|REG-STATE-021|STATE|RFC-3 §4.2|Revocation after grant but before/during commit must trigger HARD_VETO and a safe-state transition.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §4.2|
|REG-STATE-022|STATE|RFC-3 §4.3, §5.1|Parent revocation and material authority/context changes must invalidate or trigger re-evaluation of affected standing.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §4.3, §5.1|
|REG-STATE-023|STATE|RFC-3 §6, §7; RFC-5 §4|Composition must preserve local Standing; recovery must establish a new authorization context.|DECLARED|`reg-standards-baseline/rfc/rfc-3.md` §6–7; `reg-standards-baseline/rfc/rfc-5.md` §4|
|REG-STATE-024|STATE|RFC-5 §1–3|τ_K and exhaustion behavior must be pre-declared; HOLD expiry defaults to fail-closed, and Shadow Mode requires bounded review capacity.|DECLARED|`reg-standards-baseline/rfc/rfc-5.md` §1–3|

# Native lifecycle T6–T8 — integration acceptance contract (design, non-normative)

Status: engineering design for review. **Not an amendment to RFC-4 or a claim of native conformance.**

## Evidence and authority

- RFC-4 frozen specification: `reg-standards-baseline/rfc/rfc-4.md`.
- Conformance vector definitions: `vectors/core.yaml`, CT-R4-011..013.
- State vocabulary: `lifecycle/attempt_state.py`.
- Executable reference *laboratory* membrane: `skiredj-prog/tenir-conformance-s1-g1/src/tenir_conformance/membrane/membrane.py`.
- REG `runner.py` native adapter currently exposes `PolicyEngine` verdict/grant methods, **not a lifecycle backend contract**. Its T6/T8 handlers report `IMPLEMENTATION_GAP`. T7's lab probe is not a native subject test.

## Required integration boundary

Before adding PASS handlers to NativeKernelAdapter, bind it to a **real subject-owned durable lifecycle interface**, not an in-memory test double living inside the runner. The interface shall expose equivalent capabilities to:

- `create_attempt(lei, attempt_id, payload_binding)` — return durable attempt state and bound identity.
- `mark_unknown(lei, attempt_id, cause)` — make absence of confirmation explicit without asserting non-execution.
- `qualify_resolution(lei, attempt_id, evidence_ref)` — T6: accept only qualified evidence, persist terminal state and its provenance.
- `declare_failed(lei, attempt_id, evidence_ref, retry_eligible)` — T7: reject missing/unqualified non-effect evidence; timeout alone must preserve UNKNOWN.
- `retry(lei, previous_attempt_id, new_attempt_id, payload_binding)` — T8: only if qualified state and retry eligibility allow it; new attempt identity, retained old attempt, no duplicate external effect under declared assumptions.
- `get_attempt(lei, attempt_id)` and `get_events(lei)` — independent state/evidence retrieval; never infer external effects from grants alone.

Names are illustrative adapter contract sketches, **not existing production APIs**.

## Required preconditions and non-claims

1. Subject identity/version, deployment topology, persistence scope and trust anchor must be recorded in test evidence.
2. T6/T7/T8 MUST be tested against **the selected backend instance** with injected faults and durable state inspection.
3. Lab implementation may be used as oracle/test vector, but its PASS cannot be emitted with `evidence_level=NATIVE_CONFORMANT` for a different subject.
4. Timeout, network silence, and missing receipt MUST NOT be treated as proof of non-effect.
5. A retry eligibility flag does not itself prove an effect did not occur. Preserve prior attempt and effect-lock semantics.
6. Concurrent workers, crash/restart and external provider semantics are independently scoped; absent those tests, refrain from cross-process or exactly-once-effect claims.

## Test matrix for native acceptance

| ID | Initial state | Stimulus | Required assertion |
|---|---|---|---|
| T6-A | UNKNOWN | qualified effect/receipt evidence | RESOLVED, reason and provenance durable |
| T6-B | UNKNOWN | absent/invalid qualification | unchanged UNKNOWN, explicit refusal |
| T7-A | UNKNOWN | timeout only | unchanged UNKNOWN |
| T7-B | UNKNOWN | unqualified FAILED request | unchanged UNKNOWN, rejection event |
| T7-C | UNKNOWN | qualified non-effect evidence | FAILED with evidence binding |
| T8-A | UNKNOWN | retry request | denied; no additional effect |
| T8-B | FAILED | retry_eligible=false | denied |
| T8-C | FAILED | retry_eligible=true with valid qualification | new distinct attempt; old retained |
| T8-D | RESOLVED with confirmed effect | replay/retry | denied according to LEI binding |
| RACE | shared LEI, 2 workers | simultaneous retry | no double issue within proved deployment scope |
| RESTART | UNKNOWN/FAILED persisted | process restart | no silent loss of lock, evidence or state |

## Definition of done

- Native subject implementation and adapter calls reviewed on a PR against concrete code (not conceptual tests).
- Per-vector raw run output for CT-R4-011/012/013 with backend identity and revision.
- Repeatability on CI using a deterministic failure-injection harness.
- `IMPLEMENTATION_GAP` replaced by PASS **only when** the selected native backend was exercised and evidence supports that specific property.
- Cross-process/distributed guarantees remain separate and conditional on their deployment and trust assumptions.

Until then, the correct status for native T6/T8 is `IMPLEMENTATION_GAP`. T7 laboratory evidence is kept distinct from native conformance.

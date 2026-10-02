# REG Conformance Spec — v0.2.4
**TENIR Labs** | 2026-09-29 | RFC-4 (frozen) · RFC-7 (updated)

---

## Architecture (RFC-7 §8)

The conformance suite tests **normative semantic properties**, not interface topology.
The same canonical vector runs against any adapter:

```
AbstractTestVector  (topology-neutral, defined here)
        │
   BaseAdapter
        │
  ┌─────┴──────┐
  │            │
HTTPAdapter   NativeKernelAdapter      ← or any other adapter
(mode:          (mode: "native")
 "adapter")
```

---

## Evidence levels (RFC-7 §8.2)

| Level | Label | Meaning |
|---|---|---|
| 1 | `SEMANTIC_MAPPING` | Documented conceptual correspondence only — no execution |
| 2 | `ADAPTER_TESTED` | Passes via translation layer — behavioral compatibility, **NOT** native conformance |
| 3 | `NATIVE_CONFORMANT` | Native interface satisfies normative properties directly |

Every result **must** declare its `interface_mode` (`native` \| `adapter` \| `mapped`).
A report mixing native and adapter results without explicit labeling is non-conformant (RFC-7 §8.4).

---

## Reporting states (RFC-7 §8.3)

| State | Symbol | Meaning |
|---|---|---|
| `PASS` | ✓ | Normative requirement satisfied |
| `FAIL` | ✗ | Normative requirement violated |
| `NOT_APPLICABLE` | ○ | Property does not apply to this topology |
| `ADAPTER_REQUIRED` | ~ | Testable only through a translation layer |
| `IMPLEMENTATION_GAP` | △ | Requirement understood; not yet engineered |

---

## Core invariants (C-series)

| ID | RFC | Normative property | Abstract input | Expected outcome |
|---|---|---|---|---|
| C1 | RFC-3 | Standing Gate | Actor with invalid credential | `HARD_VETO` — no structural computation |
| C2 | RFC-2 | Structure Gate | P≥0.9, V≥0.9, K≤0.15 | `FLAG` or `HARD_VETO` — never `PASS` |
| C3 | RFC-4 §2.2 | Commit-State Binding — Standing Drift | Standing revoked between verdict and commit | Commit blocked (strict). Permissive behavior is non-conformant to RFC-4 §2.2 MUST and is declared as IMPLEMENTATION_GAP. |
| C4 | RFC-1 | Fail-Closed Transport Safety | Transport fault or 5xx | No execution proceeds — `NOT_APPLICABLE` for in-process kernels |
| C5 | RFC-1/4 §2.1 | Replay Soundness — Idempotency | Duplicate nonce or request | `REJECT` / `NONCE_REPLAY` |

---

## CT-R4 vectors (RFC-4 §5 — frozen)

Abstract inputs and expected semantic outcomes.
No HTTP paths. No interface shape. Adapters translate.

| ID | Normative property | Abstract input | Expected semantic outcome |
|---|---|---|---|
| CT-R4-001 | Valid Grant Binding | Valid evaluation_id + matching action + nonce, within window | `GRANT` / `COMMITTED` |
| CT-R4-002 | Action/Payload Binding Violation | Grant for action_A; commit attempts action_B | `REJECT` / `PAYLOAD_BINDING_VIOLATION` |
| CT-R4-003 | Replay Rejection | Consumed nonce reused | `REJECT` / `REPLAY_DETECTED` |
| CT-R4-004 | Expired Grant Rejection | `valid_until` passed before commit | `REJECT` / `EVALUATION_EXPIRED` |
| CT-R4-005 | Commit-State Binding / Race Detection | State at commit differs from state at verdict (beyond declared tolerance) | `REJECT` / `STATE_DRIFT` |
| CT-R4-006 | Non-PASS Cannot Cross Commit | `HOLD` or `HARD_VETO` disposition → commit attempt | `REJECT` / `INVALID_DISPOSITION` |
| CT-R4-007 | Decision Receipt Generation | Any disposition (including non-PASS) | Signed Decision Receipt independently verifiable |
| CT-R4-008 | Evidence Manifest Integrity | Manifest altered after closure | Integrity verification fails |
| CT-R4-009 | Independent Evidence Verification | Third-party verifier, no mutable internal state | Decision reproducible from Manifest |
| CT-R4-010 | External-Effect Claim Boundary | Non-atomic external effect | `external_effect_atomic=false`; post-commit evidence provided |

---

## Known gaps in reference implementation (shim v0.2.4 / kernel v0.1)

| Vector | Gap | Gap type |
|---|---|---|
| CT-R4-004 | Expiry not triggerable via HTTP without wait — use `NativeKernelAdapter` | `ADAPTER_REQUIRED` (HTTP) |
| CT-R4-005 | `state_hash_at_verdict` not implemented — drift detection limited to standing | `IMPLEMENTATION_GAP` |
| CT-R4-007 | Structural receipt present; cryptographic signing absent | `IMPLEMENTATION_GAP` |
| CT-R4-008 | Tamper-evident manifest absent; commit hash only | `IMPLEMENTATION_GAP` |
| CT-R4-009 | Depends on CT-R4-007 and CT-R4-008 | `IMPLEMENTATION_GAP` |

---

## Previous vector mapping (v0.1 → v0.2)

For traceability — explains what changed and why.

| v0.1 vector | v0.1 description | v0.2 mapping | Reason |
|---|---|---|---|
| CT-R4-001 | Commit records to ledger | CT-R4-001 Valid Grant Binding | Aligned to RFC-4 §5 property |
| CT-R4-002 | HARD_VETO unclearable | CT-R4-006 Non-PASS Cannot Cross Commit | Correctly named |
| CT-R4-003 | Orphan commit (404) | CT-R4-001 (commit path) | Was testing HTTP 404, not replay |
| CT-R4-004 | Duplicate commit | CT-R4-003 Replay Rejection | Now tests nonce/grant reuse correctly |
| CT-R4-005 | Expiry window | CT-R4-004 Expired Grant Rejection | Same property, cleaner name |
| CT-R4-006 | Nonce too short | C5 / RFC-1 validation | Input validation, not commit-integrity |
| CT-R4-007 | Nonce replay | CT-R4-003 Replay Rejection | Merged; now canonical |
| CT-R4-008 | Standing revocation | C3 / RFC-4 §2.2 | Was RFC-3 — reclassified |
| CT-R4-009 | Emergency override | C1 / RFC-3 | Was RFC-3 standing — reclassified |
| CT-R4-010 | Audit proof | CT-R4-010 External-Effect Claim Boundary | Aligned to RFC-4 §1.1 property |

---

## Thresholds (kernel-r5-1.0.0)

| Parameter | Value |
|---|---|
| Formula | `S = K / (P × V + ε)` |
| `hard_veto_below` | 0.75 |
| `flag_below` | 0.90 |
| `ε` | 1e-6 |
| Commit window | 30 s |

Runner is threshold-agnostic: it tests structural properties, not S-score values.

---

## Interface modes

The suite runs in two modes. **Conformance is declared per mode.** Native does not imply HTTP, and vice versa.

| Mode | `interface_mode` | Evidence level | Description |
|---|---|---|---|
| `--mode http` | `"adapter"` | 2 — Adapter-Tested | Tests against a REG HTTP endpoint (`POST /evaluations`). Behavioral compatibility; not native conformance. |
| `--mode native` | `"native"` | 3 — Native-Conformant | Tests in-process kernel directly via `NativeKernelAdapter`. No HTTP layer. |

### Same vectors, same criteria — different interface only

Both modes run the identical 15 vectors from the same `VECTORS` dict. Pass/fail criteria are identical. The only legitimate differences between modes:

- **C4** (`Fail-Closed Transport Safety`) — `NOT_APPLICABLE` for native: no transport layer exists. This is architectural, not a permissiveness concession.
- **CT-R4-004** (`Expired Grant Rejection`) — native uses `_inject_stale_grant()` to set `valid_until = now - 1 s`, rather than waiting 30 s. The normative property tested is identical: commit on an expired grant must be rejected with `EVALUATION_EXPIRED`. The precondition mechanism differs; the criterion does not.

Any result difference beyond these two cases would indicate miscalibration and must be investigated.

# REG Conformance Spec — v0.3.1
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
| `INCONCLUSIVE` | ? | Evidence cannot establish PASS or FAIL; never treated as PASS |
| `NOT_APPLICABLE` | ○ | Property does not apply to this topology |
| `ADAPTER_REQUIRED` | ~ | Testable only through a translation layer |
| `IMPLEMENTATION_GAP` | △ | Requirement understood; not yet engineered |

---

## Core invariants (C-series)

| ID | RFC | Normative property | Abstract input | Expected outcome |
|---|---|---|---|---|
| C1 | RFC-3 | Standing Gate | Actor with invalid credential | `HARD_VETO` — no structural computation |
| C2 | RFC-2 | Structure Gate | P≥0.9, V≥0.9, K≤0.15 | `FLAG` or `HARD_VETO` — never `PASS` |
| C3 | RFC-3 §4.2; RFC-4 §2.2 | Standing Continuity at Commit | Standing revoked between verdict and commit | `HARD_VETO`; commit blocked. |
| C4 | RFC-1 | Fail-Closed Transport Safety | Transport fault or 5xx | No execution proceeds — `NOT_APPLICABLE` for in-process kernels |
| C5 | RFC-1/4 §2.1 | Replay Soundness — Idempotency | Duplicate nonce or request | `REJECT` / `NONCE_REPLAY` |

C3 has three evidence outcomes. **C3-A:** revocation is established and commit is blocked with `HARD_VETO` → `PASS`. **C3-B:** commit is accepted after revocation → `FAIL`. **C3-C:** timing, veto, or commit outcome cannot be established → `INCONCLUSIVE`; uncertainty never becomes `PASS` or `FAIL` without evidence. The runner's single C3 probe applies this oracle to each execution.

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
| CT-R4-005 | Commit-State Binding / Race Detection | Relevant state at commit differs from state at verdict | `HARD_VETO` / `STATE_DRIFT`; commit blocked |
| CT-R4-006 | Non-PASS Cannot Cross Commit | `HOLD` or `HARD_VETO` disposition → commit attempt | `REJECT` / `INVALID_DISPOSITION` |
| CT-R4-007 | Decision Receipt Generation | Any disposition (including non-PASS) | Signed Decision Receipt independently verifiable |
| CT-R4-008 | Evidence Manifest Integrity | Copy of manifest altered after closure | Integrity verification fails without changing the original |
| CT-R4-009 | Independent Evidence Verification | Third-party verifier, no mutable internal state | Decision reproducible from Manifest |
| CT-R4-010 | External-Effect Claim Boundary | Non-atomic external effect | `external_effect_atomic=false`; post-commit evidence provided |

---

## Current execution scope and known gaps (shim v0.3.1 / kernel-r5-1.0.0)

The runner registers and dispatches 53 vectors: five C-series vectors, ten CT-R4 vectors, and 38 extended RFC-0/1/2/3/5/6/7 vectors. The two RFC-2 math vectors have active probes; the other 36 extended vectors report `IMPLEMENTATION_GAP` because their adapter tests are not implemented. HTTP C4 is `ADAPTER_REQUIRED` because the generic adapter cannot establish that a transport failure prevented execution. Native C4 is `NOT_APPLICABLE`. CT-R4-009 remains a gap because the manifest lacks enough inputs and policy state for independent decision reproduction. CT-R4-010 remains a gap because the implementation does not provide external-effect evidence. Protected administrative test helpers require `REG_ADMIN_TOKEN` on the shim and `--admin-token` on the runner. Reports record harness/specification hashes and disclose missing target/environment bindings; they are not externally certifiable without a clean pinned subject and reproducible environment. The per-vector inventory is maintained in [`VECTORS.md`](VECTORS.md).

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

Both modes run the same 53 registered IDs from `VECTORS`. Pass/fail criteria are identical where an executable probe exists. The only legitimate differences between modes:

- **C4** (`Fail-Closed Transport Safety`) — `NOT_APPLICABLE` for native: no transport layer exists. This is architectural, not a permissiveness concession.
- **CT-R4-004** (`Expired Grant Rejection`) — native uses `_inject_stale_grant()` to set `valid_until = now - 1 s`, rather than waiting 30 s. The normative property tested is identical: commit on an expired grant must be rejected with `EVALUATION_EXPIRED`. The precondition mechanism differs; the criterion does not.

Any result difference beyond these two cases would indicate miscalibration and must be investigated.

# REG Conformance Suite v0.3.0

Implementation-agnostic conformance runner for the Runtime Execution Governance (REG) Standard.
RFC-0 through RFC-7 (frozen).

53 vectors: 5 core invariants + 10 commit-integrity vectors (CT-R4-001–010) + 38 RFC-specific vectors.

## Requirements

    pip install requests fastapi uvicorn pyyaml

The reference kernel (PolicyEngine + policy YAML) ships inside kernel/.
No external repository required.

Kernel policy version (kernel-r5-1.0.0) and code version (v0.3.0) are tracked
independently. Policy versions evolve without code changes.

## Standard Reference

The normative specification for REG is pinned under `reg-standards-baseline/rfc/`:

| RFC | Title |
|---|---|
| RFC-0 | Constitution |
| RFC-1 | Execution Grant Envelope & Wire Protocol |
| RFC-2 | Structural Admissibility |
| RFC-3 | Standing & Authority Continuity |
| RFC-4 | Commit & Execution Proof |
| RFC-5 | Liveness & Operationalization |
| RFC-6 | Security, Transport & Cryptography |
| RFC-7 | Conformance Suite & Interoperability |

All eight RFCs are frozen. Latest tag: `rfc-v0.3`.

## Usage

### HTTP adapter mode (interface_mode: "adapter" — evidence level 2)

Start the reference shim:

    uvicorn shim:app --host 127.0.0.1 --port 8099

Run suite against it:

    python runner.py --mode http --endpoint http://127.0.0.1:8099

Or against any REG-compatible HTTP endpoint:

    python runner.py --mode http --endpoint https://your-server.example.com --api-key TOKEN

### Native kernel mode (interface_mode: "native" — evidence level 3)

Run directly against the in-process PolicyEngine — no HTTP required.
This is the mode for authorize(record, payload_bytes, …) style interfaces.

    python runner.py --mode native --kernel kernel/tenir_policies.yaml

### Both modes in one run

    python runner.py --mode both \
      --endpoint http://127.0.0.1:8099 \
      --kernel kernel/tenir_policies.yaml \
      --output results/my-impl.json

## Output

Console table + JSON result file.
Every result declares `interface_mode`, `evidence_level`, and `tier`.
Adapter results are never promoted to native-conformance claims.

## Reporting states

| Symbol | State | Meaning |
|---|---|---|
| ✓ | PASS | Normative requirement satisfied |
| ✗ | FAIL | Normative requirement violated |
| ○ | NOT_APPLICABLE | Property irrelevant to this topology |
| ~ | ADAPTER_REQUIRED | Testable only via translation layer |
| △ | IMPLEMENTATION_GAP | Requirement understood; not yet engineered |

## Test tiers

| Tier | Meaning |
|---|---|
| 1 | Testable against reference shim now |
| 2 | Requires shim enrichment (composition, delegation, evidence) |
| 3 | Requires infrastructure (mTLS, detached signatures, Merkle ledger) |
| 4 | Meta-conformance; requires secondary harness |

## Interface modes

Conformance is declared per mode. Native does not imply HTTP, and vice versa.

| Mode | interface_mode | Evidence level | Description |
|---|---|---|---|
| `--mode http` | `"adapter"` | 2 — Adapter-Tested | Tests against a REG HTTP endpoint. Behavioral compatibility; not native conformance. |
| `--mode native` | `"native"` | 3 — Native-Conformant | Tests in-process kernel directly via NativeKernelAdapter. No HTTP layer. |

## Reference results (standalone kernel v0.1 / shim v0.3.0)

| Mode | PASS | NOT_APPLICABLE / ADAPTER_REQUIRED | IMPLEMENTATION_GAP | FAIL |
|---|---|---|---|---|
| HTTP adapter | 11 | 1 | 38 | 0 |
| Native kernel | 11 | 1 | 38 | 0 |

Reference JSON: `results/reg-conformance-v0.3-*.json` (regenerated on each release).

Known gaps:
- C3 — permissive revocation after standing change is non-conformant to RFC-4 §2.2 MUST (reported as IMPLEMENTATION_GAP, not PASS)
- CT-R4-005 — `state_hash_at_verdict` not implemented
- CT-R4-007 — structural receipt present; cryptographic signing absent
- CT-R4-008 / CT-R4-009 — no tamper-evident Evidence Manifest / independent verifier path
- RFC-2 epistemic taxonomy, RFC-3 delegation algebra, RFC-6 mTLS and detached signatures — see `gap_by_tier` in results JSON

## Repository layout

    reg-conformance/
      kernel/                     Reference PolicyEngine + policy YAML
        policy_engine.py
        tenir_policies.yaml
      reg-standards-baseline/
        rfc/                      RFC-0 through RFC-7 (frozen)
      results/                    Committed conformance run artefacts
      LICENSE
      README.md
      runner.py                   Conformance runner (adapter + native modes)
      shim.py                     HTTP shim wrapping the kernel
      spec.md                     Conformance specification

## License

Apache 2.0 — TENIR Labs / Abdelaziz Skiredj

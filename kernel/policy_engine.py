# REG Conformance Suite v0.2.2

Implementation-agnostic conformance runner for the Runtime Execution Governance (REG) Standard.
RFC-4 (frozen) · RFC-7 (updated).

15 vectors: 5 core invariants (C1–C5) + 10 commit-integrity vectors (CT-R4-001–010).

## Requirements

pip install requests fastapi uvicorn pyyaml

The reference kernel (PolicyEngine + policy YAML) ships inside kernel/.
No external repository required.

Kernel policy version (kernel-r5-1.0.0) and code version (v0.2.2) are tracked
independently. Policy versions evolve without code changes.

## Usage

### HTTP adapter mode (interface_mode: "adapter" — evidence level 2)

Start the reference shim (TENIR-Gov kernel behind /evaluations):

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

python runner.py --mode both --endpoint http://127.0.0.1:8099 --kernel kernel/tenir_policies.yaml --output results/my-impl.json

## Output

Console table + JSON result file.
Every result declares interface_mode and evidence_level.
Adapter results are never promoted to native-conformance claims.

## Reporting states

| Symbol | State | Meaning |
|---|---|---|
| ✓ | PASS | Normative requirement satisfied |
| ✗ | FAIL | Normative requirement violated |
| ○ | NOT_APPLICABLE | Property irrelevant to this topology |
| ~ | ADAPTER_REQUIRED | Testable only via translation layer |
| △ | IMPLEMENTATION_GAP | Requirement understood; not yet engineered |

## Interface modes

Conformance is declared per mode. Native does not imply HTTP, and vice versa.

| Mode | interface_mode | Evidence level | Description |
|---|---|---|---|
| --mode http | "adapter" | 2 — Adapter-Tested | Tests against a REG HTTP endpoint. Behavioral compatibility; not native conformance. |
| --mode native | "native" | 3 — Native-Conformant | Tests in-process kernel directly via NativeKernelAdapter. No HTTP layer. |

## Reference results (TENIR-Gov kernel v0.1 / shim v0.2.2)

| Mode | PASS | NOT_APPLICABLE / ADAPTER_REQUIRED | IMPLEMENTATION_GAP | FAIL |
|---|---|---|---|---|
| HTTP adapter | 10 | 1 | 4 | 0 |
| Native kernel | 10 | 1 | 4 | 0 |

Known gaps: CT-R4-005 (state_hash_at_verdict), CT-R4-007 (signing key), CT-R4-008/009 (tamper-evident manifest).

## Repository layout

reg-conformance/
  kernel/                     Reference PolicyEngine + policy YAML
    policy_engine.py
    tenir_policies.yaml
  reg-standards-baseline/     RFC references and baseline documents
  results/                    Committed conformance run artefacts
  LICENSE
  README.md
  runner.py                   Conformance runner (adapter + native modes)
  shim.py                     HTTP shim wrapping the kernel
  spec.md                     Conformance specification

## License

Apache 2.0 — TENIR Labs / Abdelaziz Skiredj

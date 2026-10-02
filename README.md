# REG Conformance Suite v0.2.4

Implementation-agnostic conformance runner for the Runtime Execution Governance (REG) Standard.
RFC-4 (frozen) · RFC-7 (updated).

15 vectors: 5 core invariants (C1–C5) + 10 commit-integrity vectors (CT-R4-001–010).

## Requirements

```bash
pip install requests fastapi uvicorn pyyaml
```

## Usage

### HTTP adapter mode (interface_mode: "adapter" — evidence level 2)

```bash
# Start the reference shim (TENIR-Gov kernel behind /evaluations)
uvicorn shim:app --host 127.0.0.1 --port 8099

# Run suite against it
python runner.py --mode http --endpoint http://127.0.0.1:8099

# Or against any REG-compatible HTTP endpoint
python runner.py --mode http --endpoint https://your-server.example.com --api-key TOKEN
```
## Reference implementations

This repo ships one **standalone kernel** (`kernel/policy_engine.py`) — a
minimal, self-contained demonstration of the admissibility formula. It is
deliberately 200 lines: no external dependencies, no infrastructure.

The REG reference implementation named in RFC-0 §7 is the TENIR-Gov
middleware (`tenir-governance`), which implements a superset of this kernel:
Ed25519 signing, Merkle ledger, state-hash commit binding. The middleware
will be added under `reference/` when its kernel tier is extractable.

The conformance suite tests any implementation. It does not assume
TENIR-Gov. Results for the standalone kernel are labelled `kernel-standalone`
in `results/`.

### Native kernel mode (interface_mode: "native" — evidence level 3)

```bash
# Run directly against the in-process PolicyEngine — no HTTP required
# This is the mode for authorize(record, payload_bytes, …) style interfaces
python runner.py --mode native --kernel tenir_policies.yaml
```

### Both modes in one run

```bash
python runner.py --mode both \
  --endpoint http://127.0.0.1:8099 \
  --kernel tenir_policies.yaml \
  --output results/my-impl.json
```

## Output

Console table + JSON result file.  
Every result declares `interface_mode` and `evidence_level`.  
Adapter results are never promoted to native-conformance claims.

## Reporting states

| Symbol | State | Meaning |
|---|---|---|
| ✓ | PASS | Normative requirement satisfied |
| ✗ | FAIL | Normative requirement violated |
| ○ | NOT_APPLICABLE | Property irrelevant to this topology |
| ~ | ADAPTER_REQUIRED | Testable only via translation layer |
| △ | IMPLEMENTATION_GAP | Requirement understood; not yet engineered |

## Reference results (TENIR-Gov kernel v0.1 / shim v0.2)

| Mode | PASS | NOT_APPLICABLE / ADAPTER_REQUIRED | IMPLEMENTATION_GAP | FAIL |
|---|---|---|---|---|
| HTTP adapter | 10 | 1 | 4 | 0 |
| Native kernel | 10 | 1 | 4 | 0 |

Known gaps: CT-R4-005 (`state_hash_at_verdict`), CT-R4-007 (signing key),
CT-R4-008/009 (tamper-evident manifest).

## License

Apache 2.0 — TENIR Labs / Abdelaziz Skiredj

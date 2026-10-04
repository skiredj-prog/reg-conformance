# REG Conformance Suite v0.3.1

Implementation-agnostic conformance runner for the Runtime Execution Governance (REG) Standard.
RFC-0 through RFC-7 (frozen).

The runner registers 53 vector IDs across the core/commit and extended integration sets. Registration is distinct from a behavioral test and from conformance: vectors without an executable probe report `IMPLEMENTATION_GAP`. [`VECTORS.md`](VECTORS.md) is the single vector inventory, including each RFC mapping and test-coverage status.

## Requirements

    pip install requests fastapi uvicorn pyyaml cryptography

The reference kernel (PolicyEngine + policy YAML) ships inside kernel/.
No external repository required.

Kernel policy version (kernel-r5-1.0.0) and suite code version (v0.3.1) are tracked
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

Start the reference shim (from the repository root):

    $env:REG_ADMIN_TOKEN = "replace-with-a-long-random-secret"
    $env:REG_CREDENTIAL_TOKEN = "valid-token"
    uvicorn shim:app --host 127.0.0.1 --port 8099

The shim accepts only the credential configured as `REG_CREDENTIAL_TOKEN`; an unset
variable rejects all principals. Pass the same value via `--principal-credential`.
Admin-only test helpers require `X-REG-Admin-Token`. If `REG_ADMIN_TOKEN` is unset,
they return `503 ADMIN_ENDPOINTS_DISABLED`. Supply the same token to the runner with
`--admin-token`; never expose the reference shim to an untrusted network.

Run suite against it:

    python runner.py --mode http --endpoint http://127.0.0.1:8099 --admin-token "$env:REG_ADMIN_TOKEN"

For third-party endpoints, omit `--admin-token` when authenticated test helpers are not available; affected vectors are reported as `ADAPTER_REQUIRED`.

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
Every result declares `interface_mode` and `evidence_level`.
Adapter results are never promoted to native-conformance claims.

## Reporting states

| Symbol | State | Meaning |
|---|---|---|
| ✓ | PASS | Normative requirement satisfied |
| ✗ | FAIL | Normative requirement violated |
| ? | INCONCLUSIVE | Evidence cannot establish PASS or FAIL; never counted as PASS |
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

## Reference results (shim v0.3.1 / kernel-r5-1.0.0)

The committed JSON files under `results/` are historical runs that have been re-scored against the frozen normative requirements. Each corrected result preserves the original status and observed details. They are not fresh executions of the corrected source. A runtime with the listed dependencies is required to generate a new report.

| Historical report | PASS | FAIL | INCONCLUSIVE | NOT_APPLICABLE | ADAPTER_REQUIRED | IMPLEMENTATION_GAP | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| HTTP adapter | 12 | 2 | 0 | 0 | 1 | 38 | `FAILED` |
| Native kernel | 12 | 2 | 0 | 1 | 0 | 38 | `FAILED` |

These corrected assessments replace the earlier 15 PASS / 0 GAP / 0 FAIL headline. In particular, C3 and CT-R4-005 are scored `FAIL`; CT-R4-009 and CT-R4-010 remain `IMPLEMENTATION_GAP` because the historical evidence does not establish the required behavior.

The historical files are **not certifiable evidence**: they have no pinned source/subject revision, source-tree hash, OCI environment digest, or dependency lock. `requirements.txt` is currently unpinned. Fresh reports include `evidence_binding` with the local harness revision and source-tree hash, RFC-3/RFC-4 content hashes, runtime/dependency versions, and any supplied subject/environment bindings. Supply `--subject-repository`, `--subject-revision` (full commit SHA), `--subject-worktree-state clean`, and `--environment-digest sha256:<64 hex>` to bind an HTTP run. `--conformance-profile` selects the declared profile. A `CONFORMANT` behavior summary does not imply `EVIDENCE_BOUND` or release certification; the runner does not create CI provenance or sign reports.

`VECTORS.md` says whether a normative property has an executable probe (`IMPLEMENTED`) or remains declared/reserved. A run report says what that probe observed. An ID being registered or marked implemented does not by itself prove scenario coverage or conformance.

CT-R4-009 remains a gap: signed receipts are verified, but the manifest does not retain enough inputs and policy state to reproduce the decision. CT-R4-010 remains a gap: the implementation declares the need for post-commit evidence but does not provide evidence of an external effect.

The runner reports `conformance_status` separately from evidence binding. Any FAIL exits with code 1; any `INCONCLUSIVE` exits with code 3; otherwise any `IMPLEMENTATION_GAP` or `ADAPTER_REQUIRED` exits with code 2. Exit 0 means all applicable probes passed, but does not by itself certify the report's revision/environment bindings.


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

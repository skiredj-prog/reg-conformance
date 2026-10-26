# REG E8 — CI execution evidence (bounded experiment)

**Evidence ID:** REG-E8-CI-20261026-01  
**Execution date:** 2026-10-26 (GitHub Actions)  
**Repository:** `skiredj-prog/reg-conformance`  
**SUT commit:** `f8db75c4921c2cb3c8afc93852be5af4cf26ef56`  
**CI run:** [40278876478](https://github.com/skiredj-prog/reg-conformance/actions/runs/40278876478)  
**Workflow:** `.github/workflows/e8-isolation.yml`  
**Verdict:** **EXPERIMENTAL CI GREEN — 11 Python PASS + 7 container PASS + unsigned advance denial**  
**Assurance claim:** `CONTAINER_BOUNDARY_CI_PASS` and `IN_PROCESS_PROTOCOL_MODEL_PASS` only. **R-01/Q6 P0 OPEN. PRODUCTION HOLD.**

## Provenance

This report records results independently retrievable from the CI workflow logs for the **specified commit**, not from the earlier operator narrative alone. The original seven results remain archived separately as `REPORTED_PASS`; the new CI directly executed the committed code on a GitHub-hosted Ubuntu runner. GitHub automation execution is **not** equivalent to a security review by an independent administrative authority.

## Evidence and observations

| Job | GitHub job log observation | Interpretation |
| --- | --- | --- |
| `E8 signed witness and Q6 model — lab only` | **11 passed, 1 warning, 0 failures** | In-process FastAPI/TestClient protocol tests: Ed25519, signed nonce freshness, monotone CAS, replay/conflict, database rewind relative to externally retained *test* floor, Q1/Q6 local-quarantine model |
| `Docker FS/NET/KEY — seven bounded probes` | **7 PASS / 7 total, 0 failed** in JSONL output | Non-root runtime container namespace, witness-volume absence, internal health reachability and Ed25519 PEM mount/parse tests |
| Unsigned witness state advance | Job step `Reject an unsigned witness state advance from runtime` completed successfully | Unauthenticated `POST /advance` is not accepted by the test witness when invoked from the runtime container |
| Evidence export | `actions/upload-artifact@v4` step in Docker job | Machine-readable container probe JSONL, Compose render and source SHA retained temporarily with CI run (retention configured 14 days) |

### Seven probe-level observations in the CI log

| ID | Result | Specific observed value |
| --- | --- | --- |
| FS-POS-1 | PASS | effective UID=1000, GID=1000, runtime volume writable |
| FS-NEG-1 | PASS | witness path absent: **ENOENT** |
| FS-NEG-2 | PASS | no witness target mount and no named-volume mention in runtime mountinfo |
| FS-NEG-3 | PASS | attempted direct path write fails with **errno=2 / ENOENT** — **not** a demonstrated `EACCES` permission denial |
| NET-POS-1 | PASS | HTTP `/health` returned 200 via internal bridge; **no TLS/mTLS inferred** |
| KEY-POS-1 | PASS | public key file mounted read-only and present |
| KEY-POS-1b | PASS | valid Ed25519 PEM structure; key generated ephemerally within the same CI run, **not independently trusted/pinned** |

This distinction matters: `FS-NEG-3` reports a failure to write because the path is absent. It does **not** show that a privileged writer who can mount the witness filesystem would be denied.

## Reproducibility and scope

The relevant files at the fixed SHA are:
- `experiments/e8/compose.yaml`
- `experiments/e8/witness/{service.py,protocol.py,client.py,checkpoint.py,schema.sql}`
- `experiments/e8/runtime/{probe_isolation.py,quarantine_gate.py}`
- `experiments/e8/tests/{test_witness_protocol.py,test_e8_q6.py}`
- `.github/workflows/e8-isolation.yml`

Private keys were newly generated during the job; `.gitignore` and `.dockerignore` exclude the key directory. The engine private key is not placed into the runtime or witness container. Both containers run on the **same Docker host**; no independently controlled second host, external pin authority or production cryptographic trust provisioning is demonstrated. The Q6 model uses local temporary files and an in-process witness; it is **not** an execution of the G4-A production admission path.

## Residual gating requirements

**R-01 remains P0 OPEN:** demonstrate actual OS separation between worker and G1 storage engine UIDs, protect all SQLite DB/WAL/SHM/sidecar and parent-directory mutation paths, reproduce privileged writer counterexamples under the final threat model.

**Q6/Q1 remain P0 OPEN:** restore/delete the real TENIR quarantine marks with live G1/G4-A paths under an independently anchored CB-05 head, and observe `HARD_HOLD` before any new durable settlement or provider effect. A same-process gate model and a writable local file are not sufficient.

**C1/C2 remain P0 OPEN:** externally pin trusted witness and receipt roots, distinguish actor and verifier authorities, exercise complete-key-store replacement and coherent authority rollback.

**Additional:** advance is authorized by a lab controller signing key and a monotonic SQLite witness, but there is no production G1 one-time grant, coherent multi-system commit, host-independent monotonic guarantee, mTLS, full G4-A state digest or supplier-effect evidence.

**Governance:** No real execution authorization, merge or release promotion follows from these CI results. `PRODUCTION HOLD`.

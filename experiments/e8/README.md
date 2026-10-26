# E8 — Witness / Runtime Container Isolation Experiment

**Reference:** REG-ARCH-022 · TENIR-Gov / REG E8 · 26 October 2026  
**Evidence classification:** 7/7 `REPORTED_PASS` (operator-reported, not independently reproduced)  
**Assurance status:** Container deployment controls under evaluation — **R-01 and Q6 remain open**  
**Release gate:** **PRODUCTION HOLD**

> This directory documents the reported container-isolation experiment for an E8
> external witness and its runtime peer. It does **not** constitute a production
> certification, independently verified security assessment, or proof of the
> normative E8/CB-05 protocol. Do not use these findings to authorize real
> provider effects or privileged production deployment.

## 1. Purpose and scope

The E8 experiment explores the **Witness vs. Runtime** separation in a
containerized TENIR-Gov / REG deployment. Its immediate objective is to
demonstrate, for a specified unprivileged runtime-container threat model, that:

- the runtime can write to **its own** dedicated working volume;
- the runtime cannot directly see or write the witness's dedicated data volume
  through the tested container mount namespace;
- the intended runtime-to-witness health endpoint is reachable over a private
  Docker network;
- a witness Ed25519 public-key file can be injected into the runtime as a
  read-only mount and parsed as a public key.

These are **deployment-isolation properties**. They do not by themselves
demonstrate monotonic checkpointing, authenticated pre-authorization, resistance
to rollback of the local G4-A store or quarantine, one-time cryptographic
grants, or integrity of third-party provider effects.

Normative references:

- [E8 external monotone witness contract](../../specs/exteriority-e8-witness.md)
- [E8 container and adversarial test plan](../../specs/e8-container-boundary-test-plan-v0.1.md)
- [Container boundary evidence intake, 26 October 2026](../../evidence/e8/CONTAINER_BOUNDARY_INTAKE_2026-10-26.md)
- [TENIR CB-05 / PR #77](https://github.com/skiredj-prog/tenir_governance/pull/77)
- [G1 experimental IPC / PR #79](https://github.com/skiredj-prog/tenir_governance/pull/79)

## 2. Reported deployment architecture

The experiment report describes the following deployment profile.
The statements in this section are **operator-provided configuration
descriptions**, not independently verified contents of a committed Compose file.

| Control | Runtime container | Witness container |
| --- | --- | --- |
| Linux UID:GID | `1000:1000` (reported) | `2000:2000` (reported) |
| Linux capabilities | `cap_drop: [ALL]` (reported) | `cap_drop: [ALL]` (reported) |
| Privilege escalation via `execve` | `no-new-privileges:true` (reported) | Same (reported) |
| Container root filesystem | `read_only: true` (reported) | `read_only: true` (reported) |
| Writable named volume | `tenir_runtime_strict_volume` | `tenir_witness_strict_volume` |
| Shared network | Internal Docker bridge, `internal: true` | Same network |
| Witness health endpoint | Client of `http://witness:8443/health` | Provider of health endpoint |
| Witness verification key | Public Ed25519 PEM at `/etc/tenir-witness/witness_pub.pem`, mounted `:ro` | Corresponding witness identity, not independently verified here |

**Security qualifications:**

1. `cap_drop: [ALL]` removes Linux capabilities from the container process;
   `no-new-privileges` prevents obtaining additional privileges through
   `execve`. Neither configuration alone blocks every sensitive syscall,
   proves a seccomp policy, or resists compromise of the Docker daemon or host.
2. A read-only container root filesystem still permits writes to explicitly
   mounted writable volumes; these must be verified individually.
3. `internal: true` restricts network routing; it is **not** transport
   encryption or mutual authentication. `http://witness:8443/health` is HTTP,
   not HTTPS, irrespective of the port number.
4. A well-formed Ed25519 public key is not yet a trusted identity. Its
   fingerprint and provenance must be verified against a pin supplied by an
   authority outside the compromised runtime's control.
5. Separate containers on a single Docker host are not automatically
   independent administrative trust domains. A hostile host administrator or
   Docker socket holder is outside the bounded T0 runtime-container test.
6. The witness volume stores are described as isolated. Append-only semantics
   and monotonicity are **not covered** by the seven FS/NET/KEY probes.

## 3. Isolation probes — reported campaign

All seven results below were reported as PASS by the experiment operator. Raw
commands, stdout/stderr, exit codes, exact Compose config, image digests,
manifest, host topology and independently signed evidence have not been supplied
to this repository for this campaign.

| Probe ID | Claimed check | Reported | Conformance interpretation |
| --- | --- | --- | --- |
| `FS-POS-1` | UID 1000 can write to the runtime's dedicated storage volume | REPORTED_PASS | Bounded positive container-filesystem function |
| `FS-NEG-1` | `/var/lib/tenir/witness` is absent from runtime namespace | REPORTED_PASS | Tested path invisible; other access paths not excluded |
| `FS-NEG-2` | Runtime `/proc/self/mountinfo` does not list `tenir_witness_strict_volume` | REPORTED_PASS | No detected cross-mount under observed configuration |
| `FS-NEG-3` | Runtime direct write to witness path does not succeed | REPORTED_PASS | No write observed; distinguish `ENOENT`, `EACCES`, `EPERM` in raw evidence |
| `NET-POS-1` | Runtime can reach witness `/health` on internal bridge | REPORTED_PASS | Network reachability only, **not** channel authentication or bidirectional proof |
| `KEY-POS-1` | Witness public PEM is present via a read-only mount | REPORTED_PASS | Read-only mount observed per report, independent pin source not proven |
| `KEY-POS-1b` | Mounted public key is non-empty and structurally valid | REPORTED_PASS | Format/parse claim only, **not** identity or signature verification |

**Reported score: 7/7 PASS; independently verified score: not established.**
The original report is preserved without upgrading these observations into
production-qualified claims.

## 4. Executable laboratory and reproduction

The following **experimental** artifacts are now committed in this directory:

- `compose.yaml` — non-root runtime and witness with distinct named volumes,
  read-only container root filesystems, `cap_drop: [ALL]`, internal bridge
  network and **no published host port**. This is **one Docker host**, not a
  separate administration domain.
- `witness/service.py` and `witness/schema.sql` — SQLite monotone append-only
  head with signed Ed25519 records and an **engine-signed CAS advance**. Unsigned
  advances from the runtime are rejected. The database's SQL triggers alone
  cannot resist a compromised witness UID or Docker host administrator.
- `witness/protocol.py`, `witness/client.py`, `witness/checkpoint.py` —
  canonical signatures, nonce-bound fresh reads, a caller-supplied public
  key pin, historical verification, and a **local cache only**, respectively.
  An ordinary local checkpoint file is not an independent trust root.
- `runtime/probe_isolation.py` — precisely **seven** FS/NET/KEY probes with
  JSON-lines output and a nonzero exit on failure.
- `runtime/quarantine_gate.py` — **experimental** fresh-head comparison for
  local quarantine snapshots; returns only
  `ELIGIBLE_FOR_FURTHER_CHECKS` or `HOLD_GLOBAL`, never permission to
  dispatch.
- `tests/test_witness_protocol.py` and `tests/test_e8_q6.py` — signed
  protocol, nonce/replay/identity/append-only checks, and an authentic
  **LOCAL quarantine rollback** test. These tests use a same-process witness,
  not a physically independent authority.
- `.github/workflows/e8-isolation.yml` — unit/model tests and Docker
  boundary checks on a disposable GitHub-hosted runner.

**The supplied initial bundle was deliberately corrected:** its nominal
Q6 test rolled back the *witness's* database, not the local quarantine;
its original `/advance` endpoint lacked caller authentication; its Docker
test used `down -v`, destroying witness volumes. The committed experiment
models Q6 correctly at the local-quarantine boundary, signs authorized
advances and preserves volumes during normal teardown.

### Running the Python protocol and Q6 model tests

From the repository root:

```bash
python -m pip install pytest cryptography fastapi httpx
python -m pytest -q experiments/e8/tests/
```

### Running the Docker isolation probes

Prepare **ephemeral** Ed25519 test keys at
`experiments/e8/witness/keys/` (the directory is excluded by both
`.gitignore` and `.dockerignore`). The CI workflow generates
`witness_signing.key` (private witness PEM),
`witness_pub.pem` (public Ed25519 PEM), and
`engine_pub.pem` (separately provisioned controller public key).
The engine private key is deliberately not mounted into the runtime
or witness containers.

On Linux, the witness signing key must be readable by container UID `2000`;
the CI workflow uses `sudo chown 2000:2000` and `sudo chmod 400` on
that ephemeral key. Reproduce only on a dedicated laboratory host and do not
commit or publish private signing material.

```bash
cd experiments/e8
docker compose config
docker compose up -d --build --wait
docker compose exec -T runtime python /app/runtime/probe_isolation.py
docker compose down
```

**Never use `docker compose down -v` as the default cleanup.** It removes
named volumes, including historical witness state and potential evidence.
Provisioning and reset require separately documented, authorized ceremonies.

The `exit_code=0` from `probe_isolation.py` means **the seven bounded
container probes passed on that environment**. It **does not** close R-01,
Q6, C1/C2, prove preauthorization, or authorize real effects.

### CI protocol and trust limits

The experiment intentionally does **not** provide HTTPS/mTLS or a second
independent host. `http://witness:8443` relies on Ed25519 protocol-level
authentication and nonce-signed head reads; it remains susceptible to network
denial, and a Docker host compromise may control both services and their keys.
A correctly signed new head binds to digest values **asserted by an authorized
engine**, not independently reconstructed G4-A truth. Thus the signing
mechanism does not itself establish non-bypassable G1 or E8 conformance.

## 5. Evidence and CI requirements

For a reproducible result, archive a signed or SHA-256-manifested evidence pack
containing:

- Exact TENIR-Gov, REG conformance and witness source commit SHAs;
- Docker Compose render (secrets redacted), runtime/witness OCI image digests,
  engine/host version, network and volume configuration;
- Effective UIDs/GIDs, capabilities, `no-new-privileges` and mount tables
  for both processes;
- Each probe's complete command, stdout/stderr, return code, observed
  `errno`, time and before/after witness state;
- Key PEM fingerprint **and independently provisioned expected fingerprint**;
- Runtime-to-witness authenticated pre-authorization transcript, only once
  the E8 protocol is implemented;
- Independent reviewer identity or an explicit statement that the run is
  solely operator-authored.

A GitHub Actions workflow that runs only these seven probes should publish
`CONTAINER_ISOLATION_PASS`, not `E8_SECURITY_CONFORMANT`. Mocked tests,
same-host tests, and multi-host adversarial tests must remain distinct evidence
classes.

## 6. Threat-to-evidence mapping and open P0s

| Requirement | Seven-probe result | Required closure evidence | Current decision |
| --- | --- | --- | --- |
| **R-01** — Privileged/local G1 or G4-A storage mutation | Does not attempt privileged mutations of **local engine database**, WAL, SHM or sidecars | Real worker↔engine UID isolation plus negative writes/replaces to protected engine state; adversarial testing | **OPEN** |
| **Q6** — Restore coherent old quarantine and re-admit | Does not restore quarantine or run actual admission | Restore prior quarantine state; obtain fresh independent head; synchronous E8 refusal before commit/dispatch | **OPEN** |
| **Q1** — Erase quarantine/sentinel | Not exercised | Erase marks, attempt fresh admission, verify fail-closed and no effect | **OPEN** |
| **C1/C2** — Restore authority or substitute roots | Key presence only | Coherent store/root rollback and substitute-key negative tests against external pin/trust floor | **OPEN** |
| **E8 independent trust** | Container-level separation reported | Separate administrative domain, monotone signed head, attested CAS, revocation/crash tests, independently pinned keys | **NOT DEMONSTRATED** |

Relevant follow-up test IDs: `FS-NEG-4`, `KEY-NEG-1`, `E8-NEG-Q6`,
`E8-NEG-Q1`, `E8-NEG-C1`, `E8-NEG-C2`, `E8-NEG-CAS` and
`E8-NEG-ACK`; see the [test plan](../../specs/e8-container-boundary-test-plan-v0.1.md).

## 7. Verdict

**Container isolation:** seven controls reported PASS in a described Docker
configuration, subject to raw-evidence reproduction.

**Independent monotone witness:** not demonstrated by the container-isolation
probes. **R-01, Q1, Q6, C1 and C2 remain open** for the full stated adversary
model. **PRODUCTION HOLD** remains in effect.

This README is a technical reference and a bounded evidence index, not a
release authorization.

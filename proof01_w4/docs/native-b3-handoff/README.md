# PROOF-01 / W4.3 — Native B3 Adapter + Independent Differential Oracle

**27 October 2026 · Experimental laboratory package · NO CERTIFICATION**

This package is a **candidate contribution** intended for `skiredj-prog/reg-conformance`, PR #55. It has **not been committed to GitHub** by this package's build process. W4.2's synthetic signed-events verifier remains separate and unmodified.

## What is inside

- `proof01_w4/native_b3.py`: independent native proof verifier for the B3–RC-01–I8 lab format (`proof-provider-bundle/candidate-v0.1`).
- `proof01_w4/native_oracle.py`: a **second** independently coded oracle for the intersection of verifiable claims on one synthetic operation.
- `proof01_w4/adapt_native.py`: bounded assessment CLI; never signs or reclassifies unsigned source observations as signed runtime events.
- `proof01_w4/tests/`: 37 native adversarial/structural tests, 12 differential tests, 2 adapter contract tests.
- `proof01_w4/testdata/native_b3/bundle/`: frozen real output from the standalone **laboratory** (provider receipt, checkpoint, local state, witness events and evidence manifest).
- `proof01_w4/testdata/native_b3/external_trust/operator-pins.json`: **operator-generated** demonstration trust pins. NOT an independent authority, and kept outside the evidence bundle.
- `docs/W43_CONTRACT.md` and `docs/RFC7_W43_VECTORS_CANDIDATE.json`: unratified specification and vector list.
- `evidence/`: local test logs and sample verdict, plus SHA-256 file inventory.

## Reproduce

Python >=3.11, package `cryptography>=43,<47`.

```bash
python -m unittest discover -s proof01_w4/tests -v
python -m proof01_w4.adapt_native proof01_w4/testdata/native_b3/bundle \
  --pins proof01_w4/testdata/native_b3/external_trust/operator-pins.json
```

Expected: `51 tests OK`, then bounded `VERIFIED` **only** for `lab-repair-consistency` relative to operator pins. In the stronger sense, system E2E assurance is **HOLD**. `real-banking-effect` and `no-unobserved-effects` are not VERIFIED.

## Product claim boundary

Reconstruction of the integrity and internal consistency of a **recorded, single-operation, simulated** B3/RC-01/I8 run. No assertion that the runtime genuinely created the unsigned state, no complete proof of all possible provider effects, no independent institutional custody of pins, no true G4-A grant/dispatch, no B1/B2/Q1/Q6/R-01 closure. Green tests validate the **test harness expectations**, not production-level security guarantees.

## Integration instruction

Review the code against the pinned SUT version and import only after checking that W4.3 native fields do not silently replace W4.2 synthetic signed-event semantics. Freeze an integration commit, rerun both suites, and keep PR #55 draft until evidence gates pass.

## Source provenance and GitHub status

Original ZIP: `PROOF01_W43_native_B3_differential_verified_2026-10-27.zip`, SHA-256 `6da2426980c4f7b2f44f2bbc013f16fd873e235773637d75876524db3f201252`.

This documentation branch publishes a **handoff specification**, not the ZIP binary or Python source. GitHub W4.3 PR #57 is a separate *synthetic* oracle project, not a verified mirror of these native sources. W4.4 PR #58/#59 remain Draft with CI and TOCTOU obligations.

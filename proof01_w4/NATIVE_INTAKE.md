# Sprint 1 — native evidence intake and receipt-byte checks

Candidate implementation on `feat/proof01-native-evidence-intake`, based on the frozen W4 correction `107c3d8e1affec99843ad4eb3f78ffb36fc0efa9` (Draft PR #59). This contribution prepares the next verification boundary while treating archive availability as a planning assumption. Original archive hashes, original native suites and producer integration are **not reported as verified**.

## Implemented boundary

`native_intake.py` captures a manifest and its declared artifacts once through the POSIX W4 snapshot reader. It checks documentary integrity and requires the three files described in REG #60: `provider-bundle.json`, `local-state.json`, `witness-events.json`. Original file bytes remain unchanged. Files merely present beside the manifest cannot supply undeclared evidence. No synthetic runtime events or new signatures are manufactured.

External pins must be supplied outside the bundle. Their presence and digest are recorded; their native schema, authority and independent custody are not inferred. Native object/array JSON is parsed only to reject malformed or ambiguous input. The exact legacy envelope and codec are deliberately not guessed.

Optional `--expected-subject` supplies a reviewer-held reference with `integration_sha` (40 lowercase hex), `deployment_manifest_sha256` (64 lowercase hex) and `topology_id`. When used, `convergence.json` and `deployment-manifest.json` must be inventoried. Rebound configuration or changed source/topology makes the evidence **STALE** relative to that reference. A match means `MATCHES_CALLER_REFERENCE_ONLY`; filling three strings never establishes an Integration Lock. This is an intake policy, not a new normative CEB-01 schema.

The configuration-drift test changes the deployment, updates convergence and rehashes the manifest. The old external reference is still refused as STALE. No transitive guarantee graph, exhaustive assumption inventory or complete PREPARE/PREVENT proof is claimed; affected guarantees are explicitly `NOT_COMPUTED`.

```sh
python -m pip install -r proof01_w4/requirements-verifier.txt
python -B -m proof01_w4.native_intake /path/to/native/bundle \
  --pins /external/operator-pins.json \
  --expected-subject /external/reviewer-subject.json
```

An otherwise complete intake returns `INDETERMINATE / NATIVE_READERS_REQUIRED`, process exit **2**. A refuted inventory/input returns exit **1**; an out-of-scope claim returns exit 2. No success exit for full native assurance is exposed by this intake command.

## Receipt verification primitive

`receipt_bytes.verify_receipt_bytes(message, signature, public_key, expected)` verifies Ed25519 against the **exact supplied signed message bytes**. The caller provides raw signature/key bytes and an independently held expected binding for provider, key ID, operation, idempotency key, request hash, scope and action type. Production code contains no signing path.

The signed JSON body is checked structurally against the unchanged candidate schema from TENIR #84, commit `e6dc138be9d1cc445f7fe55d7fa77d69c013d891`, Git blob `fcc8c8089722467b405f90034436e40eb9bf0591`. The schema copy is under `contracts/`. Integer fields additionally reject booleans and floating-point representations. JSON Schema `format` remains annotation-only; `issued_at` format/freshness/revocation checks remain explicit outstanding work.

This primitive performs **no canonicalization or re-signing**. Passing the right bytes is essential: a signature over pretty JSON does not validate a different compact serialization. It does not invent a key-ID derivation from a public-key hash; the schema specifies a hex pattern and the caller must supply the actual pinned key-ID mapping.

A valid signature and matching request produce `INDETERMINATE / RECEIPT_SIGNATURE_AND_BINDINGS_VALID`, with the authenticated signer assertion and remaining checks listed. It authenticates a statement relative to a supplied key, not the truth of an external effect. Missing expected bindings stay indeterminate; wrong signatures or changed bindings are refuted. This API is a byte-level building block, not a claim of interoperability with the unavailable original bundle codec.

## Remaining wiring and source assumptions

- The original `native_b3.py`, `native_oracle.py`, `adapt_native.py` and export fixtures are still distinct inputs; none is impersonated or overwritten by these files.
- The native codec must yield the exact signed message from the real envelope before the receipt primitive is wired into it. Merkle inclusion, signed checkpoint, witness pin/chain and differential replay remain separate checks.
- The local RC-01/I8 observations remain unsigned. No positive documentary check is transformed into a valid runtime grant, G4-A effect, independently anchored witness or complete observation guarantee.
- The 29 new tests use expressly labelled intake/receipt fixtures and ephemeral in-memory keys. They are not the original 51 native W4.3 tests or 58/4 REPAIR results.
- TENIR-Gov, its budget ledger and provider dispatch are not modified. No mock G4-A or second budget authority is introduced.

## Validation and disposition

Local Linux run: **79 tests passed**, comprising the existing 50 W4 tests, 15 receipt-byte checks and 14 intake checks. Cases include concurrent W4 regressions, forged bytes, wrong keys, changed scope, duplicate keys, unavailable pins, unlisted files, changed deployment, and no promotion of self-consistent input into native assurance. Run the full suite with `python -B -m unittest discover -s proof01_w4/tests -v`.

The workflow pins cryptography 46.0.7 and jsonschema 4.23.0, verifies the actual checkout SHA and retains environment/dependency/test records. Remote CI is assessed for this branch separately from #59. **Native semantic verification, independent review, Integration Lock, E2E and production remain open/HOLD.**

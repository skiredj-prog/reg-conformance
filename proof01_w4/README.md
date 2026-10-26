# PROOF-01 / W4 — Independent Verifier, tranche 0

Autonomous **offline** verifier, independent from TENIR-Gov and G4-A.
Run from repository root: `python -m unittest discover -s proof01_w4/tests -v`.
Check a bundle: `python -m proof01_w4.verifier /path/to/bundle --claim declared-id`.

Manifest file: `proof-manifest-v1.json` with `schema_version`, explicit
`scope` (system, deployment, time_window, fault_model), `claims`, and
`artifacts` entries (relative path, sha256). All referenced files must
be regular local files contained in the bundle. The initial contract is
intentionally minimal, NOT the final RFC-7 conformance schema.

Outcomes: REFUTED for contradictory inventory/digest, OUT_OF_SCOPE for
undeclared claim, INDETERMINATE for missing evidence or valid hashes with
no semantic attestation. VERIFIED is reserved for future supported,
independently checked *specific* claims; the current verifier never
emits it. A matching SHA-256 is not a proof of external effect, no
second effect, trusted signer, independent witness, or I8 correctness.

Next: signed trust-store and anchor verification; canonical bundle
manifest; completeness/sequence and receipt validation; differential
state replay for RC-01 + I8; RFC-7 adversarial corpus. Integrate W2/W3
by importing their **evidence bundles only**, never their adjudicator.
No external banking integration, certification or C3 claim.

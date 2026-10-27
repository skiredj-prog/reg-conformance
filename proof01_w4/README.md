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


## W4.2 experimental signed-event fixture (not production/B3 wire compatibility)

Requires Python 3.11+ and `cryptography>=43,<47`. Independently supplied trust store:
`{"trust_version":"w4/1","keys":{"runtime":{"role":"runtime","public_key_b64":"..."},"provider":{"role":"provider","public_key_b64":"..."},"witness":{"role":"witness","public_key_b64":"..."}}}`
The trust store MUST reside outside the bundle, and real key custody/independence cannot be concluded from differently named keys.

Manifest must declare claim `signed-trace-integrity`, `wire_contract: proof01-signed-events/1`, and inventory SHA-256 for `events.json` and `checkpoint.json`. Each event has `seq`, `previous_hash`, `kind`, `attempt_id`, `resource_id`, `amount`, `capacity` and detached-in-object Ed25519 signature over canonical JSON without `signature`. The provider must sign `PROVIDER_EXECUTED`; the witness signs checkpoint binding event count, final hash and declared scope hash. Supported synthetic states: RESERVED -> DISPATCHING -> PROVIDER_EXECUTED -> REPAIR -> COMMITTED, or provider-executed direct to committed.

`python -m proof01_w4.semantic /path/to/bundle --trust-store /other/path/trust.json --claim signed-trace-integrity`

`VERIFIED` refers **exclusively** to integrity of the supplied signed synthetic sequence, witnessed endpoint and budget arithmetic *in that sequence*; it does not demonstrate completeness of external provider events, an independently controlled witness, uniqueness of real-world effects, compliance, or correctness of a production integration. A declared `no-unobserved-effects` claim remains `INDETERMINATE` even with perfect signatures and local accounting. This wire format is a draft fixture. Actual W2 G4-A/B3 adapters, independent anchors, independent oracle/reconciliation and real deployment binding remain outstanding.

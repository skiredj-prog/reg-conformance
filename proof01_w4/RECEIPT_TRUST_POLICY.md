# Receipt trust policy — candidate verification profile v0.1

This is an implementation-level reviewer policy, not a ratified REG-ARCH or B3 wire extension. It builds on `receipt_bytes` without changing producer bytes, signatures or the original receipt schema. Base is PR #61 at `333c29400bb68b7e6d2717806adf5d0a854d3f98`.

## Purpose

`verify_with_policy(message, signature, expected, policy, verification_time)` checks receipt time and current key-policy admissibility after exact-byte Ed25519 verification. Both the evaluation time and policy must be explicit caller references. No host clock, implicit "not revoked" default, grant authority or provider execution is created.

A successful policy evaluation still returns `INDETERMINATE / RECEIPT_POLICY_CHECKS_VALID`. It establishes consistency with supplied references, not their authenticity, the completeness of a revocation source, independent clock trust, Merkle inclusion, witness history or RC-01/I8 replay.

## Policy fields

Every field is required; extra fields and unknown versions/rules are refused.

| Field | Meaning |
|---|---|
| `schema` | `proof01-receipt-trust-policy/0.1` |
| `policy_id` | Caller-held policy identifier; an identifier is not an attestation |
| `provider_id`, `key_id` | Must match the independently supplied expected receipt bindings |
| `public_key_b64` | Strict base64 of the selected 32-byte Ed25519 verification key |
| `valid_from`, `valid_until` | Key acceptance window, inclusive lower / exclusive upper bound |
| `revoked_at` | Explicit effective revocation timestamp or explicit null; absence is not interpreted as clear status |
| `status_as_of` | Time represented by the supplied key-status observation |
| `max_status_age_seconds` | Maximum allowed age of that observation |
| `max_receipt_age_seconds` | Maximum allowed age of signed receipt `issued_at` |
| `clock_skew_seconds` | Declared allowance for future receipt/status timestamps |
| `revocation_rule` | Only `reject_at_or_after` is implemented |

Durations are nonnegative integers up to `2**31-1`; bools and floating-point representations are rejected. These bounds and semantics are local profile choices requiring reviewer approval for a deployment, not requirements retroactively imposed on REG-RC-01.

Key validity is checked at **both** issuance and evaluation. Under this current-acceptance profile, a signature issued before expiry is refused once the key acceptance window has ended. This is not an archival-signature validation profile. Revocation rejects issuance or evaluation at/after the effective cutoff, including future-dated issuance that crosses a scheduled revocation within clock-skew allowance.

Old or impossible-future key-status knowledge yields INDETERMINATE. A stale status is marked STALE. A receipt outside the declared freshness/issuance window is refused even if cryptographically signed correctly. Boundary comparisons use integer microsecond precision without floating-point rounding.

## Time encoding

The parser uses a defined subset of [RFC 3339 §§4.3, 5.6–5.7](https://www.rfc-editor.org/rfc/rfc3339): explicit offsets and seconds, with up to six fractional digits. It handles numeric offsets and case variants of T/Z. It does not silently interpret an unqualified local time as UTC.

RFC 3339 includes an unknown-offset notation, leap-second representations and fractional precision beyond this implementation's microseconds. Those cases return an unsupported/indeterminate result for signed receipts, rather than being rounded or presented as invalid cryptographic evidence. Python's representable year/calendar range applies. No claim of complete RFC 3339 or RFC 9557 support is made.

The source signed bytes remain unchanged. Time normalization is used only for comparison and result reporting.

## CLI

```sh
python -B -m proof01_w4.receipt_policy /evidence/receipt/message.json \
  --signature /evidence/receipt/signature.bin \
  --expected /external/request-reference.json \
  --policy /external/receipt-policy.json \
  --at 2026-10-28T16:01:00Z
```

The signature file contains 64 raw bytes. The message is exactly the provider-signed message, not a reserialized bundle object. Codec/envelope extraction remains a separate integration obligation. Policy/request reference files must be outside the message directory; the CLI records hashes of the actual bytes consumed. Files are size-bounded, special files are rejected and no evidence is executed. A separate path alone does not establish independent custody.

Exit **1** denotes refusal; exit **2** denotes indeterminate or a successful intermediate policy check. No full-native VERIFIED exit is exposed. Raw receipt signature checks without temporal policy remain available through the earlier primitive; this wrapper does not silently alter that API.

## Reproducible negative coverage

Tests exercise age/skew boundaries to the microsecond; expired and not-yet-valid keys; effective and scheduled revocation; old/future status observations; timezone equivalence; ambiguous, malformed and unsupported timestamps; missing explicit revocation state; wrong provider/key bindings; malformed policies; forged signatures; external-reference path checks and nonblocking refusal of special files. Valid intermediate results retain policy-provenance and remaining-native-check limitations.

No original archive suite or producer integration is implied. **INDEPENDENT REVIEW OPEN / NATIVE BUNDLE SEMANTICS OPEN / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.**

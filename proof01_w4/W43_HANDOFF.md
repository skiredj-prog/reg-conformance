# PROOF-01 — W4.3 Assurance Lead handoff

**Status:** candidate RFC-7 adversarial vectors; NOT a claim of RFC-7 conformance.
**Ownership:** W4 only. Do not change W2 runtime exporter, W3 witness/security authority or PMO promotion gates.

## Boundaries

- W4.2 `semantic.check` authenticates declared fixture signatures, checks hash chain,
  witness checkpoint and applies *its own* state/I8 interpreter.
- W4.3 `oracle.reconstruct` is a second, standalone interpreter for the already
  authenticated event payloads; `compare_report` flags contradictions.
- Agreement is a *synthetic supplied-trace consistency* observation, not proof of
  provider-effect completeness, exclusive writer authority, witness custody, real
  state convergence, or actual deployment.
- These tests do not yet consume real G4-A or B3 artifacts.

## Interface requested from W2 (do not assume this exists)

A versioned export contract, immutable after run:

1. `run_id`, repo and exact commit SHA, binary/configuration digests.
2. `deployment_id`, host scope, fault model, backend authority and epoch.
3. Ordered attempt events with stable ID, type, resource, amount, recorded state,
   monotonic sequence, source identity, payload digest and predecessor.
4. Provider receipts distinguish OBSERVED/EXECUTED/UNKNOWN; absent receipt
   MUST NOT imply NOT_EXECUTED.
5. `REPAIR` and budget-settlement events with the accountable owner.
6. Evidence type, signature, timestamp, key ID, and coverage/completeness boundary.

W4 will define a versioned *adapter* for this export, not modify W2's runtime.

## Interface requested from W3

- Signed trust-anchor provenance from an authority outside the governed actor.
- Independent observer domain, witness checkpoint and monotonic epoch/anti-rollback
  evidence. A second key on the same writable host does **not** establish independence.
- Negative artifacts for B1/B2, Q1/Q6 and R-01; explicit known bypasses.
- Claimed observation completeness, or declaration of INDETERMINATE.

## Current RFC-7 candidate vectors

| Vector | Expected interpretation |
| --- | --- |
| Intact synthetic signed trace | VERIFIED **trace internal only** |
| Tampered verifier balance | REFUTED differential mismatch |
| Replaced older witness checkpoint | Not VERIFIED |
| No exhaustive external effect feed | INDETERMINATE on no-unobserved-effects |
| Two parallel reservations exceed capacity | OracleReject I8 |
| Duplicate external receipt ID | OracleReject duplicate receipt |
| Unspecified RELEASED transition | OracleReject fields / unsupported |
| Fabricated positive report | REFUTED differential mismatch |

`python -m unittest discover -s proof01_w4/tests -v`

## Promotion gates

- Freeze cross-team schema only after W2/W3 review and PMO pin of exact SHAs.
- Independent key custody/identification and witness attestation must be verified.
- Reproduce the same result from identical immutable artifacts on two verifier hosts.
- Never infer no second provider effect from a local ledger or from a partial provider feed.
- No system PROOF-01 PASS until W2, W3, W4 share one commit/perimeter and evidence set.

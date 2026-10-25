# Native lifecycle mapping — TENIR-Gov 5.7.0 (P0)

Target source: `skiredj-prog/tenir_governance@0ec4870ee5bd73d90b9c6304f5cf774defadfb83`.

**Verdict: API_NOT_EQUIVALENT.** The REG Conformance lab's T6–T8 attempt lifecycle cannot be marked as native-conformant merely because TENIR-Gov has similarly named operation outcomes.

| REG vector | Lab contract | TENIR-Gov 5.7.0 observed interface | Native coverage classification |
|---|---|---|---|
| CT-R4-011 / T6 | attempt UNKNOWN → RESOLVED with qualified evidence | `ProviderOutcome` and `ReconciliationResult`; `OperationState.UNKNOWN` → provider reconciliation semantics | PARTIAL_SEMANTIC_MAPPING; native contract equivalence not established |
| CT-R4-012 / T7 | attempt UNKNOWN → FAILED only with qualified evidence; timeout alone cannot cause FAILED | `DispatchProvider.reconcile`, `ProviderOutcome.FAILED` and durable governor recovery tests; no native `declare_failed(evidence_qualified=...)` API identified | PARTIAL_SEMANTIC_MAPPING; evidence guard is not equivalent to lab Boolean flag |
| CT-R4-013 / T8 | FAILED + retry_eligible → new attempt ID; LEI lock conditions | No native `retry_eligible` attempt contract identified; operation idempotency keys govern retries/reconciliation | IMPLEMENTATION_GAP |

## Evidence sources and tests

- `tenir_governance/operations/provider.py`: `ProviderOutcome`, `DispatchResult`, `ReconciliationResult`, `DispatchProvider`; timeout is UNKNOWN, not proof of FAILED.
- `tests/test_sqlite_governor_crash_recovery.py`: crash boundaries, recovered outcomes and budget invariant I8 in single-host SQLite context.
- `tests/test_ep02_governor_commit_gate.py`: distinct authority and commit recovery concerns, not equivalent to T6–T8.
- `tests/test_deployment_manifest.py`: release boundaries only (23/23 observed in CI), not T6–T8.

## Evidence policy

The CI native targeted test may demonstrate *specific existing release behavior* only. Never assign `EvidenceLevel.NATIVE_CONFORMANT` for CT-R4-011/012/013 until there is a native adapter with identical preconditions, observable state transitions, recovery behavior and negative/adversarial cases. A reference adapter report (14 PASS / 41 GAP) is not an implementation certification.

Follow-up: run pinned tests for the SQLite governor crash/reconciliation cases under CI and attach output; then design a minimal native contract adapter, with an explicit gap for T8 if no production API exists.

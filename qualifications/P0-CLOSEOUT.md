# P0 closeout — TENIR-Gov 5.7.0 / REG Conformance

Status: **IMPLEMENTED_BUT_NOT_FULLY_VERIFIED**. No merge or claim promotion.

## Implemented on PR #47

1. Exact TENIR-Gov source pin and version guard. The 5.7.0 distribution and kernel versions are checked.
2. Deployment-safety (23 tests), SQLite crash/recovery (12 tests), native provider uncertainty/regression (9 exact tests).
3. Machine-readable, fail-closed JUnit gate in `qualifications/verify_native_t6_t7.py`. Rejects absent/extra/duplicate/skipped/failed tests and emits a *partial semantic* mapping, **never native normative conformance**.
4. Six adversarial verifier tests in `qualifications/test_verify_native_t6_t7.py`.
5. Test logs, structured mapping, Python dependencies and SHA256 artifacts retained by CI.
6. REG reference adapter remains **INCOMPLETE** (14 PASS / 41 IMPLEMENTATION_GAP) and is distinct from the installed subject.

## Acceptance matrix

| Requirement | Evidence | P0 interpretation |
|---|---|---|
| Version pin | exact Git SHA and identity check | implemented; previously CI passed |
| 23 deployment tests | GitHub run 40149398519 | PASS |
| 12 SQLite recovery tests | GitHub run 40149398519 | PASS |
| 9 provider semantic tests | GitHub run 40149398519 | PASS on prior `-k` selection; new **exact-node gate pending CI** |
| T6 unknown → provider determination | native guarded subset | PARTIAL_SEMANTIC_EVIDENCE, **not T6 normative PASS** |
| T7 failed requires evidence | provider determination, contradictory-signal guards | PARTIAL_SEMANTIC_EVIDENCE, **not T7 normative PASS** |
| T8 retry eligibility and LEI lock | no production equivalent established | IMPLEMENTATION_GAP |
| Native lifecycle conformance | exact lab `AttemptState` and `tau_K` semantics | NOT_DEMONSTRATED |
| Certification and REG+ promotion | end-to-end immutable evidence chain and norm equivalence | HOLD |

## Strict stop gate

A CI green run on this branch shall certify **only** the tests and scope executed. It shall not flip CT-R4-011 or CT-R4-012 to `NATIVE_CONFORMANT` or CT-R4-013 to PASS. Normative closure requires a reviewed product contract and independent native adapter that explicitly tests the missing attempt-level qualification predicates and retry eligibility. P0 implementation is complete at the scoped evidence-tooling layer; **normative P0 closure remains blocked**, not silently redefined.

## Next independent change

Create a separate TENIR-Gov product design/implementation proposal for a qualifying attempt lifecycle with traceability to RFC-4, once the contract and non-contamination boundary are agreed. Do not retrofit lab state into production governor merely to produce green tests.

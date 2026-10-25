# Lifecycle integration (T6–T8) — verified scope

This note records the state of the `main` runner and the separate S1/G1 laboratory membrane. It does not certify production REG or a TENIR-Gov deployment.

## Present in reg-conformance

| Artifact | Path | Current state |
|---|---|---|
| AttemptState vocabulary | `lifecycle/attempt_state.py` | Present: PENDING, AWAITING_QUALIFICATION, UNKNOWN, FAILED, RESOLVED |
| Lifecycle vectors | `vectors/core.yaml` | CT-R4-011 (T6), CT-R4-012 (T7), CT-R4-013 (T8) present |
| Vector registration | `runner.py` `CORE_VECTORS` | All three registered (18 core/commit vectors according to runner header) |
| Native T6 handler | `runner.py` `_v_ct_r4_011` | Reports `IMPLEMENTATION_GAP` |
| Native T7 handler | `runner.py` `_v_ct_r4_012` | Delegates to `_run_t7_membrane_vector` laboratory probe when importable; may return PASS, FAIL or GAP, not proof of a native adapter implementation |
| Native T8 handler | `runner.py` `_v_ct_r4_013` | Reports `IMPLEMENTATION_GAP` |
| T7 probe | `lifecycle/t7_membrane_probe.py` | Present; executes against laboratory membrane if available |

**Important distinction:** vector registration is not native backend implementation; a lab PASS does not constitute native conformance. Inspect actual results per backend and revision before reporting a PASS.

## Laboratory implementation

Repository: [tenir-conformance-s1-g1](https://github.com/skiredj-prog/tenir-conformance-s1-g1).

- Executable state machine: `src/tenir_conformance/membrane/membrane.py`
- Focused tests: `tests/test_t7_t8_failed_retry.py`
- Covered cases include timeout not implying FAILED, evidence qualification before declaration of failure, UNKNOWN blocking premature retry, retry eligibility and distinct attempts.
- GitHub Actions [Membrane CI run 39188882778](https://github.com/skiredj-prog/tenir-conformance-s1-g1/actions/runs/39188882778), attempt 2, was re-run on 23 October 2026 at commit `d29400100b00f7e7a87d229af660f62e51d61f12` and completed successfully, including the T7/T8 focused test step. This supports that test scope only.

## Remaining gaps / acceptance conditions

1. Run CT-R4-011/012/013 against each REG native/HTTP adapter and preserve the exact verdict, backend, commit and raw logs.
2. Implement an explicit native adapter only after contract review; do not turn `IMPLEMENTATION_GAP` into PASS by reusing a laboratory result.
3. Preserve the RFC-4 safety rules: timeout alone is not failure; FAILED requires qualified evidence; retry eligibility is a property of the prior attempt and not proof of an external non-effect.
4. Validate independent execution / external effect assertions separately, with deployment and trust assumptions captured.

The earlier statement that these vectors were **not registered** in `runner.py` is obsolete. Their registration is complete; native execution coverage is not.

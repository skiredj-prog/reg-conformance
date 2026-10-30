# T6–T8 lifecycle integration — scoped status

## Current implementation

- `reg-conformance` declares the T6–T8 vocabulary and 18 core / 38 extended vectors.
- The standalone, importable laboratory membrane lives in
  [tenir-conformance-s1-g1](https://github.com/skiredj-prog/tenir-conformance-s1-g1).
- `lifecycle/t7_membrane_probe.py` exposes `run_t6_probe`, `run_t7_probe`,
  and `run_t8_probe`.
- CI runs `tests/test_lifecycle_probes.py` on pinned source commits, including
  the full real TENIR-Gov PolicyEngine dependency.
- The runner deliberately records a successful laboratory probe as
  `IMPLEMENTATION_GAP` for **native TENIR-Gov conformance**. No lab-to-native
  promotion is permitted.

## Contract synchronized with RFC-4

| Transition | Safety contract |
| --- | --- |
| T6 `UNKNOWN/AWAITING -> RESOLVED` | Qualified, correctly bound evidence; no late auto-commit |
| T7 `UNKNOWN -> FAILED` | Exactly bound, verified Ed25519 non-execution attestation; timeout/boolean alone insufficient |
| T8 `FAILED -> new attempt` | `non_execution_confirmed && !effect_observed && retry_eligible` |
| T8 `retry_eligible=False` | Same LEI remains blocked even if non-execution is verified |
| `RESOLVED` | Same LEI permanently locked (no duplicate external effect) |

The default Ed25519 lab trust root and RFC 8032 seed are **public test
material**. They do not prove provider-origin non-execution or independent
custody. The laboratory does not assert multi-process or production safety.

## Cross-repository synchronization

- Membrane candidate: [PR #49](https://github.com/skiredj-prog/tenir-conformance-s1-g1/pull/49).
- The lifecycle CI temporarily pins that PR's exact unmerged SHA; replace the
  pin with the final reviewed commit when the candidate is merged.
- The native TENIR-Gov adapter must independently implement and qualify the
  lifecycle vectors before `CT-R4-011..013` can be reported as native PASS.

## Gates still open

- Independent source authority for negative attestations;
- W2/connector/provider custody and high-water restoration;
- Native runtime integration, independent W4 verification and production conformance.

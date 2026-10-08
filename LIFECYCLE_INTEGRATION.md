# Lifecycle integration (T6–T8)

## Landed

| Artifact | Location | Status |
|----------|----------|--------|
| `AttemptState` enum | `lifecycle/attempt_state.py` | **In repo** |
| Vectors CT-R4-011..013 | `vectors/core.yaml` | **In repo** |
| Lab executable membrane | `tenir-conformance-s1-g1` | **Validated (37 tests)** |

## Pending (runner.py)

`runner.py` must register `CT-R4-011`, `CT-R4-012`, `CT-R4-013` in `CORE_VECTORS` and expose
`_v_ct_r4_011` / `_012` / `_013` gap handlers on HTTP and native adapters
(pointing at lab validation in tenir-conformance-s1-g1).

Local workspace has a full patched `runner.py`; apply via PR if automated push of the 58KB file is blocked.

Until then, vector **catalog** (yaml) + **vocabulary** (lifecycle/) are authoritative;
native runner still reports 15 core vectors unless patched.

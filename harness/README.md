# Runtime-neutral harness

Vectors are written once, as scenarios over a small set of primitives. A
runtime is hooked by a *port* that implements only what the runtime really
does and declares it.

```
python -m harness --port harness.ports.reference:ReferencePort --probes
```

## Rules the harness enforces

- A scenario whose capability or intent the port does not declare is not run.
  It is reported `ADAPTER_REQUIRED`.
- A vector with no neutral scenario yet is reported `ADAPTER_REQUIRED` with a
  `HARNESS_GAP` note. That is a gap in this harness, not in the subject.
- A port cannot report evidence level 3, and cannot override a neutral scenario.
- A refusal by the runtime's own policy (`DENIED`) never satisfies a vector
  about REG structural admissibility (`INADMISSIBLE`).
- Effect probes (`HX-EFFECT-*`) are not REG vectors. They are reported apart
  and never enter a vector summary or `conformance_status`.

## What counts as an admission

RFC-0 §4 gives each disposition an execution instruction: `PASS` is ALLOW and
`FLAG` is ALLOW_WITH_MONITORING. Both let execution proceed, so a scenario
that needs an admitted action accepts either. `HOLD` and `HARD_VETO` never do.

A `FLAG` proceeds "only under an explicitly defined additional condition or
supervision". A port reports the condition it observes in
`Decision.conditions`. The run lists every check that went forward on a
`FLAG` and says for how many of them a condition was observed.

## Reading a run by property

After the vector list, a run prints a second reading of the same results,
grouped by candidate property family (`properties.yaml`):

```
EGP-06 A refusal or a suspension produces no governed effect   PASS 2  FAIL 0  not run 1
```

- The families are candidates. They are not part of the frozen RFCs.
- The view counts executed checks, vectors and probes alike, under the family
  each one exercises. It changes no result and no tally: the 56-vector summary
  is computed exactly as before.
- `not run` counts checks that exist and could not be run on this subject.
  `no vector` counts properties indexed in `VECTORS.md` that have no registered
  vector yet.
- A family with a passing check is not a family satisfied. One check observed
  one behaviour.

## Hooking a runtime

Copy `ports/template.py`. Implement one primitive, add it to `capabilities`,
run. The two mappings (native verdict to REG disposition, native refusal to
REG reason code) live in the port file, in the open, and belong to whoever
owns the runtime.

## Ports

| Port | Subject | Level |
|---|---|---|
| `ports/reference.py` | bundled reference kernel, not the TENIR-Gov runtime | 1 |
| `ports/tenir_gov.py` | installed `tenir-governance`, default governor path, in process | 2 |

`tests/test_harness.py` checks the instrument itself: each effect probe is run
against a deliberately faulty test double and must report `FAIL`.

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
  and never enter a summary or `conformance_status`.

## Hooking a runtime

Copy `ports/template.py`. Implement one primitive, add it to `capabilities`,
run. The two mappings (native verdict to REG disposition, native refusal to
REG reason code) live in the port file, in the open, and belong to whoever
owns the runtime.

## Ports

| Port | Subject | Level |
|---|---|---|
| `ports/reference.py` | bundled reference kernel, not the TENIR-Gov runtime | 1 |

`tests/test_harness.py` checks the instrument itself: each effect probe is run
against a deliberately faulty test double and must report `FAIL`.

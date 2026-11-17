# Runtime-neutral harness

Vectors are written once, as scenarios over a small set of primitives. A
runtime is hooked by a *port* that implements only what the runtime really
does and declares it.

```
python -m harness --port harness.ports.reference:ReferencePort --probes --checks
```

`--probes` adds the effect probes and `--checks` the property checks. Neither
is a REG vector, and neither changes the vector summary.

## Rules the harness enforces

- A scenario whose capability or intent the port does not declare is not run.
  It is reported `ADAPTER_REQUIRED`.
- A vector with no neutral scenario yet is reported `ADAPTER_REQUIRED` with a
  `HARNESS_GAP` note. That is a gap in this harness, not in the subject.
- A port cannot report evidence level 3, and cannot override a neutral scenario.
- A refusal by the runtime's own policy (`DENIED`) never satisfies a vector
  about REG structural admissibility (`INADMISSIBLE`).
- Effect probes (`HX-EFFECT-*`) and property checks (`PX-*`) are not REG
  vectors. They are reported apart and never enter a vector summary or
  `conformance_status`.

## What counts as an admission

RFC-0 §4 gives each disposition an execution instruction: `PASS` is ALLOW and
`FLAG` is ALLOW_WITH_MONITORING. Both let execution proceed, so a scenario
that needs an admitted action accepts either. `HOLD` and `HARD_VETO` never do.

A `FLAG` proceeds "only under an explicitly defined additional condition or
supervision". A port reports the condition it observes in
`Decision.conditions`. The run lists every check that went forward on a
`FLAG` and says for how many of them a condition was observed.

## Property checks

`VECTORS.md` indexes properties that have no executable vector. A property
check exercises one such row. It is named after the row (`PX-CT-R3-001`
exercises `CT-R3-001`), reported apart from the vectors, and counted by the
property view under the family of its row. Registering a check as a vector is
a ratification decision. Adding one is not.

| Check | Anchor in the index | What it observes | The port needs |
|---|---|---|---|
| `PX-CT-R0-005` | RFC-0 §4 | Two conditions that give different dispositions alone give, together, one at least as restrictive as the stricter. Both orders. | `combine`, one declared combination |
| `PX-CT-R3-001` | RFC-3 | A request with a malformed credential is rejected. Not observed: that the rejection comes before evaluation. | intent `malformed_credential` |
| `PX-CT-R3-002` | RFC-3 | Past the declared revocation bound, a revoked principal's new request is rejected and its earlier grant cannot be committed. | `revoke`, `clock`, bound `revocation` |
| `PX-CT-R3-003` | RFC-3, a proposal the RFCs do not specify | Revoking one principal leaves another's new request admitted and its earlier grant committable. | `revoke` |
| `PX-CT-R3-006` | RFC-3 | A time-limited credential is admitted while valid and rejected once its declared lifetime has passed. | intent `expiring_credential`, `clock`, bound `credential_validity` |
| `PX-CT-R3-007` | RFC-3 | A request outside the scope its caller holds is rejected. | intent `out_of_scope` |
| `PX-VEC-6-02` | RFC-6 §3.1, §6.2 | A key already used, presented again with another action, is rejected. | `nonce` |
| `PX-VEC-6-03` | RFC-6 §3.2, §6.2 | A request submitted outside the declared freshness window is rejected. | intent `stale_request`, bound `freshness` |
| `PX-VEC-6-04` | RFC-3 §4.2; RFC-6 §4.2, §6.2 | A credential signed by a key revoked for longer than the declared bound is rejected. | intent `revoked_key`, bound `revocation` |
| `PX-REG-STATE-014` | RFC-2 §3.3 | A hard invariant violation gets `HARD_VETO` on measurements that are admitted without it. | intent `invariant_violated` |
| `PX-REG-STATE-024` | RFC-5 §1–3 | A `HOLD` nobody answers within the declared window is rejected with `HARD_VETO`, and produces no effect. | intent `needs_approval`, `clock`, bound `tau_k` |

How a check concludes:

- It states an outcome, never a mechanism. `PX-REG-STATE-014` does not look
  for a bypass of the scoring. It looks for `HARD_VETO` where the score alone
  would admit.
- Where a rejection is expected, an outright refusal and a `HARD_VETO` both
  pass. An admission fails. A `HOLD` suspends without rejecting: the check is
  reported `INCONCLUSIVE`. `PX-REG-STATE-014` is the exception, because
  RFC-2 §3.3 names `HARD_VETO`.
- Each rejection check first sends the same request with nothing wrong. If
  that one is not admitted, the check does not conclude: a runtime that
  refuses everything passes none of them.
- A port declares an intent only if the runtime has the notion: a credential
  that can be malformed, a scope a caller can hold, an invariant that can be
  declared. Otherwise the check is not run on that subject.

## Declared bounds and the clock

Five checks depend on time. The harness sets no duration for any of them.

- The port declares, in `bounds`, the bounds the deployment under test
  declares: `revocation`, `credential_validity`, `freshness`, `tau_k`. It
  states them. It does not invent one. A check whose bound is not declared is
  not run, and the result says which bound is missing.
- A check never waits a number of seconds of its own. It calls
  `elapse_past(bound)`, and the port lets its own declared bound pass, by
  waiting (`clock_mode = "real"`) or by moving the clock the runtime reads
  (`"simulated"`). The run records which.
- `PX-REG-STATE-024` passes only on a rejection. A `HOLD` that is merely still
  suspended after its window is not executable either, and is not rejected:
  the check then reports `INCONCLUSIVE`.

The effect probes follow the same rule. A port whose runtime executes after it
replies declares `effect_window`, and "no effect" is read once that window has
passed. Read at once, an empty journal would only mean "none yet".

## What a result does not establish

Every scenario, vector, probe or property check, declares two things:

- `at`: where it observes, as one of the four phases of RFC-0 §5
  (pre-execution, conditional authorization, supervised execution, closure and
  proof), or the structural model alone for the two scenarios that call it
  directly;
- `not_observed`: what its result leaves open.

```
✓  PX-VEC-6-02  PASS  a used key presented again with a modified action was refused outright (NONCE_REPLAY)
   ↳ not observed: a replay with an identical payload; that the key is unique or random
```

The console prints the line for the probes and the property checks that gave
an observation. The report carries both fields for every scenario under
`observation`, with the conditions of the run: effect window, clock mode,
declared bounds, exhaustion policy. `verdict.json` keeps them for every result
that gave an observation.

## Reading a run by property

After the vector list, a run prints a second reading of the same results,
grouped by candidate property family (`properties.yaml`):

```
EGP-06 A refusal or a suspension produces no governed effect   PASS 2  FAIL 0  not run 1
```

- The families are candidates. They are not part of the frozen RFCs.
- The view counts executed checks, vectors, probes and property checks alike,
  under the family each one exercises. It changes no result and no tally: the
  56-vector summary is computed exactly as before.
- `not run` counts rows and probes that have a check and gave no observation
  on this subject. `no check` counts rows of `VECTORS.md` that have neither a
  registered vector nor a property check.
- A family with a failing check is reported as such, whatever else passes in it.
- A family with a passing check is not a family satisfied. One check observed
  one behaviour.

The last line reads the same run row by row:

```
84 indexed properties: 20 have an executable check in this harness; 17 gave an observation on this subject (PASS 16, FAIL 1)
```

## Hooking a runtime

Copy `ports/template.py`. Implement one primitive, add it to `capabilities`,
run. The two mappings (native verdict to REG disposition, native refusal to
REG reason code) live in the port file, in the open, and belong to whoever
owns the runtime. So do the bounds: they are the deployment's declared values,
written in the port by whoever can answer for them.

## Ports

| Port | Subject | Level |
|---|---|---|
| `ports/reference.py` | bundled reference kernel, not the TENIR-Gov runtime | 1 |
| `ports/tenir_gov.py` | installed `tenir-governance`, default governor path, in process | 2 |

`tests/test_harness.py` checks the instrument itself: each effect probe and
each property check is run against a deliberately faulty test double and must
report `FAIL`, and only the check aimed at that fault may do so.

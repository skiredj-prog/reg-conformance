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

## Rows no port can adapt (rule of 23 November 2026)

Standard author's decision of 23 November 2026, 15:07 UTC (option A), amended
on the owner's review of 17:37 UTC. The rule lives in `runner.py` and applies
to every adapter and every report this repository produces (`python -m
harness`, `runner.py --mode http|native`). It is dated; it reinterprets no
report produced before it. Every report lists what the rule took out of the
exit code, row by row with its reason, under `exit_code_rule`, and carries a
`scope` block with every `conformance_status`.

- A registered row no ratified text specifies, `RESERVED` in `VECTORS.md` or
  marked `superseded_by` in `vectors/*.yaml` (`CT-R4-004`, `CT-R4-014` to
  `CT-R4-016`), is reported `NOT_SPECIFIED` unless it was observed: a `PASS`,
  `FAIL` or `INCONCLUSIVE` on such a row is kept (the row keeps its text and
  results); a gap on it is not counted, the successor row carries the count.
  Both lists are read from the index and the vector files, not hard-coded.
- A registered row the implementer declares outside the runtime's perimeter,
  in the port's `not_in_perimeter` with a non-empty `declared_by` and
  `reason`, is reported `NOT_IN_PERIMETER`, as a property check already could
  be. Only the rows the standard allows can be declared (`PERIMETER_DECLARABLE`
  in `harness/adapter.py`: the credential layer of RFC-3, `CT-R3-001`, `-002`,
  `-006`, `-007`, `-008`); any other row is refused. A declaration is plain
  text, not a signature. A neutral scenario cannot be declared away.
- A row with no neutral scenario whose property check ran and passed in the
  same run is reported `EXERCISED_BY_CHECK`; the check carries the
  observation. A failing check fails the row; any other check status leaves
  the row `ADAPTER_REQUIRED` with the check's status noted. Without
  `--checks` nothing changes.

These statuses enter neither `conformance_status` nor the exit code, whose
formula is unchanged: `FAIL` → 1; else `INCONCLUSIVE` → 3; else
`IMPLEMENTATION_GAP` or `ADAPTER_REQUIRED` → 2; else 0. When nothing is
counted against a run but rows stay out of the count, `conformance_status`
is `CONFORMANT_ON_SPECIFIED_ROWS`, never a bare `CONFORMANT`: it speaks for
the specified rows, not for coverage. A declared gap on a specified row stays
`IMPLEMENTATION_GAP` and counts: on TENIR-Gov 5.7.6 and the 5.7.7 candidate,
the authorization bound (`CT-R4-004a`), the signed receipts (`CT-R4-007`) and
the revocation latency window (`CT-R3-002`) hold the code at 2 until 5.8.0.
Exit code 0 is not obtained by recounting.

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
| `PX-REG-STATE-001` | RFC-2 §2.5 | With a measurement unknown, the admissible attempt is never admitted. | `degrade`, state `unknown` |
| `PX-REG-STATE-002` | RFC-2 §2.5 | With a critical measurement stale, the admissible attempt is never admitted. | `degrade`, state `stale` |
| `PX-REG-STATE-004` | RFC-2 §2.5 | With two measurements that disagree, the admissible attempt gets `HOLD`. | `degrade`, state `contradictory` |
| `PX-REG-STATE-010` | RFC-2 §2.6 | With a measurement missing, the admissible attempt is never admitted: no value stands in for it. | `degrade`, state `missing` |
| `PX-REG-STATE-013` | RFC-2 §2.8 | From full confidence down, the disposition of the admissible attempt never becomes less restrictive. | `confidence` |
| `PX-REG-STATE-014` | RFC-2 §3.3 | A hard invariant violation gets `HARD_VETO` on measurements that are admitted without it. | intent `invariant_violated` |
| `PX-REG-STATE-015` | RFC-2 §3.4 | From full confidence down, an attempt that is restricted never gets a less restrictive disposition. | `confidence` |
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

## Degraded evidence

Six checks read what a runtime does when its evidence is degraded. They
submit the admissible attempt with one measurement unknown, stale, missing or
contradictory, or the same attempt at several levels of confidence, and read
the disposition. They do not look at how the runtime reached it.

- The port lists, in `degradations`, every measurement it can put in each
  state, under the runtime's own names. A check runs on all of them and its
  result names each one: `capacity (FLAG)`, `authority (HARD_VETO)`. A port
  that lists only the measurements the runtime guards hides what the check is
  for.
- Unknown, stale and missing evidence pass on `HOLD`, on `HARD_VETO` and on an
  outright refusal. An admission fails, `FLAG` included. Contradictory
  evidence passes on `HOLD` only, because RFC-2 §2.5 names it, and does not
  conclude where the deployment pre-declares a resolution.
- The two confidence checks pass when nothing widens. A disposition that does
  not change at all also passes, and the result says so.
- `PX-REG-STATE-025` (row `REG-STATE-025`, RESERVED: a proposal of the draft
  RFC-2 v0.2 of 23 November 2026, not ratified) reads a kernel against the
  admissible domain it declares, nothing else. The standard prescribes no
  domain: the port states, in `domains`, the `(low, high)` the kernel under
  test declares for each measurement, under the runtime's own names, and
  implements `evaluate_at_value`. The check submits one value just above and
  one just below each declared domain: an explicit rejection before any
  disposition passes, an admission fails, a `HOLD` or `HARD_VETO` does not
  conclude (closed, but not rejected as out of domain), and an edge of the
  domain rejected as out of it fails. A port that declares no domain gets
  `ADAPTER_REQUIRED`. Whether a value such as K = 1.5 is admissible is not a
  question this harness answers: it is whatever the kernel declares.

Three rows of the index have no check of their own. `REG-STATE-003`: what a
boundary can show of it is read by `PX-REG-STATE-001` and `-010`; the rest is
how the runtime labels its evidence. `REG-STATE-005` and `REG-STATE-012`
state the law of `-013` and `-015` as the mechanism that produces it, and a
disposition cannot show which mechanism produced it.

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
  vector summary is computed exactly as before.
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
| `ports/tenir_gov_576.py` | installed `tenir-governance` 5.7.6, default governor path, one FLAG condition declared and acknowledged at dispatch (candidate: mapping provisional, pending independent review) | 2 |

`tests/test_harness.py` checks the instrument itself: each effect probe and
each property check is run against a deliberately faulty test double and must
report `FAIL`, and only the check aimed at that fault may do so.

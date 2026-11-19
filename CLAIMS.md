# What a REG conformance result lets you say

Draft for the author's review. Two sections are in force: "What counts as an
admission" and "Third-party assessments", ratified by the author on
18 November 2026. The rest is not yet in force.

REG Conformance runs a fixed set of tests against a runtime and reports what
passed, what failed and what could not be tested. It tests behaviour. It does
not prove or certify anything.

## What a run establishes

One run covers one revision of one subject, reached in one way, on the cases
the suite contains. Three things are reported separately and must stay
separate when a result is quoted.

**How the subject was reached**

| Level | Name | Meaning |
|---|---|---|
| 1 | Semantic mapping | A documented correspondence. No product behaviour demonstrated. |
| 2 | Adapter-tested | Real product behaviour, observed through a port. |
| 3 | Native-conformant | The runtime satisfies the properties natively. No run reaches this today. |

**The outcome of each test**

| Outcome | Meaning |
|---|---|
| `PASS` | The behaviour was observed. |
| `FAIL` | The opposite behaviour was observed. |
| `INCONCLUSIVE` | The test could not reach a determinate result. |
| `NOT_APPLICABLE` | The property cannot apply to this runtime. |
| `ADAPTER_REQUIRED` | Not tested: the port or the harness cannot test it yet. |
| `IMPLEMENTATION_GAP` | The implementer declares the capability missing. |

Only `PASS` counts as a pass.

**Which set the test belongs to.** REG vectors test properties specified by
the REG RFCs. Effect probes (`HX-EFFECT-*`) check that a refusal matches zero
downstream effects and an allowed call exactly one. Property checks (`PX-*`)
each exercise one property that the index lists and that has no executable
vector yet. Probes and property checks are listed apart and are never counted
among the vectors.

**The reading by property.** A run also groups its results by candidate
property family: the vectors, the probes and the property checks that exercise
the same property are counted together, each under its own kind. The families
are candidates and are not part of the frozen RFCs. The grouping changes no
outcome and no vector count. It shows which properties were observed on a
subject whose shape does not fit the vectors as written.

**What a result does not establish.** Each test declares where it observes,
as a phase of RFC-0 §5, and what its result leaves open. A test submits one
case: a pass is a pass on that case. Tests that depend on time use the bound
the subject declares and none of their own; when the subject declares no
bound, the test does not run. "No effect" is read from one journal, after the
effect window the port declares. `verdict.json` carries all of this for every
result that gave an observation.

**What counts as an admission.** RFC-0 §4 lets execution proceed on `PASS`
and on `FLAG`, the latter only under an explicit condition or supervision.
A test that needs an admitted action accepts either. The run lists the tests
that went forward on a `FLAG` and says whether the condition was observed.

As ratified in [RN-001](reg-standards-baseline/notes/RN-001-flag-time-drift.md)
§1: a `FLAG` that carries an explicit condition counts as an admission. A
`FLAG` that carries none does not satisfy RFC-0 §4; it is recorded as an
implementation gap, and a quote of a test that went forward on it says so.

## How to quote a result

A statement about a result names all of the following:

1. the subject and its exact revision (commit),
2. the `reg-conformance` commit that ran,
3. the evidence level,
4. the counts per outcome, with vectors, probes and property checks apart,
5. where the evidence bundle is, with its checksums.

Example:

> `<subject>` `<version>` at commit `<commit>`, run with reg-conformance at
> `<commit>`, evidence level 2: 0 of 59 REG vectors executed (59 adapter
> required); 4 of 4 effect probes passed. By property: 2 of 14 candidate
> families with a passing check, none with a failing check, 12 not exercised.
> Bundle: `<link>`.

A count of families is quoted with the words "candidate families" and with
the number not exercised. If a test went forward on a `FLAG` whose condition
was not observed, the quote says so. A quote that rests on one test's result
gives what that test does not establish.

## What must not be said

- That a subject is "REG-conformant", "REG-certified" or "REG-compliant" on the
  strength of a run. `verdict.json` always carries `certifying: false`.
- That a result at level 1 describes a product. The 15 passes of the bundled
  reference kernel are not results of any runtime.
- That a result holds for another revision of the subject. Another commit is
  another run.
- That a pass count is a score. Tests that were not executed are not passes
  and are not failures.
- That a result maps to a regulation or to another framework. The crosswalk
  states such relations one by one, each with its limit.
- That an effect probe or a property check is a REG vector, or the reverse.
- That a row of the index is "covered" or "implemented" because a property
  check exists for it. The row keeps its status in `VECTORS.md`.
- That a property holds "at the declared bound" for a subject that declares
  none. The test did not run.
- That no observed effect means no effect. The journal is one channel, read
  after one declared window.
- That a family with a passing check is satisfied, or that a subject
  "satisfies" a number of families. One check observed one behaviour.

## Mappings written by someone other than the runtime's owner

A port translates a runtime's verdicts and refusals into REG terms. When the
port was not written or reviewed by the runtime's owner, the result is
provisional and is quoted as such until the owner has confirmed or corrected
the mapping.

## Third-party assessments

A third party may run the suite and report its results under the terms above.
A third party's own requirement identifiers, scoring or labels are that
party's work. REG neither defines nor endorses them. An assessment report
keeps the two apart: what the REG run observed, and what the assessor
concluded from it.

What an assessment says about REG is limited to this sentence:

> Assessed against REG Conformance `<version>` at commit `<commit>`,
> evidence level `<N>`.

followed by the quote described in "How to quote a result", and nothing more.

- A readiness, maturity or assurance rating defined by the assessor is not a
  REG conformance level, and is not presented as one. In particular, a
  "readiness" result says nothing about conformance.
- Using the REG name in a commercial offer, product or service name requires
  the licensor's written agreement. Apache-2.0 covers the files, not the name
  (see below).

## Name and licence

The code and the vectors are under the Apache License 2.0. That licence covers
use, modification and redistribution of the files. It does not grant permission
to use the licensor's trade names, trademarks, service marks or product names,
except to describe the origin of the work (Apache-2.0, section 6).

Questions about a wording not covered here: open an issue.

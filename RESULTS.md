# Published runs

Draft for the author's review.

Each line is one run: one subject revision, one `reg-conformance` commit, one
evidence bundle. Read [`CLAIMS.md`](CLAIMS.md) before quoting any of it. No
line here is a certification.

REG vectors, effect probes and property checks are counted apart. The suite
has 61 REG vectors, 4 effect probes and 17 property checks. Each line says
which of the three sets the run executed and gives the reading by candidate
property family described in `CLAIMS.md`, computed from those sets only. The
workflow at `v0.7.0` runs the vectors and the probes, not the property checks:
the run below has none. Property checks will appear in a published run once
the workflow runs them.

| Subject | Revision | Level | REG vectors | Effect probes | Property checks | Run |
|---|---|---|---|---|---|---|
| Reference kernel bundled in this repository | `reg-conformance` `20016d2` (tag `v0.7.0`) | 1, semantic mapping | 15 PASS, 1 not applicable, 1 adapter required, 44 implementation gaps | 4 adapter required: the port declares no effects | not run: the workflow at `v0.7.0` does not pass `--checks` | [Run 44797748660](https://github.com/skiredj-prog/reg-conformance/actions/runs/44797748660), 20 Nov 2026, on the tag; harness exit code 2 (gaps, no FAIL); artifact `reg-evidence-reference`, `sha256:4ae00693…a30c1879` |

By property, from the vectors and the probes only: 9 of 14 candidate families
with a passing check, none with a failing check, 5 not exercised. This reading
leaves out the property checks. One of them, `PX-CT-R3-001`, fails on this
kernel (see [Run it yourself](#run-it-yourself)) and counts under family
EGP-01, valid authority for every effect. The run therefore does not show that
no family has a failing check.

Quote it as:

> Reference kernel bundled in `reg-conformance`, run with `reg-conformance` at
> `20016d2` (tag `v0.7.0`), evidence level 1: 15 of 61 REG vectors passed
> (1 not applicable, 1 adapter required, 44 implementation gaps); 0 of 4
> effect probes executed (4 adapter required); property checks not run. By
> property, from vectors and probes only: 9 of 14 candidate families with a
> passing check, none with a failing check, 5 not exercised; the property
> checks, one of which fails on this kernel, are not counted. Bundle:
> https://github.com/skiredj-prog/reg-conformance/actions/runs/44797748660,
> artifact `reg-evidence-reference`,
> `sha256:4ae006939221d0cb3d18a95a6cf7d52b34b6a3ff5ca7fae2fd49c303a30c1879`.

The line above stays as it was recorded at `v0.7.0`. Since the change of
23 November 2026 (pull request #83, not yet released), `CT-R4-004a` gives
`ADAPTER_REQUIRED` on this port: the vector now needs an effect observer
independent of the runtime, and the port declares none. A run of the same
kernel after that change gives 14 PASS, 1 not applicable, 2 adapter required
and 44 implementation gaps, through this port as through the runner's native
mode; the reading by property does not change. The line
will be replaced by the next published run, not edited.

The reference kernel is a teaching implementation. Its passes are not results
of the TENIR-Gov runtime or of any product. The run above replaces the one of
16 November 2026 at `3023045`, made on a branch outside the release.

## Runs awaiting confirmation

A run enters the table above once the owner of the subject has confirmed the
port's mapping.

| Subject | State |
|---|---|
| TENIR-Gov 5.7.0 (`47ef67e`), default governor path | Run locally at level 2. The mapping of intents and refusals is provisional. Not yet run in CI. |

## Where a bundle comes from

The workflow `REG Conformance - Run` produces five files per run:
`report.json` (every test and its outcome), `run.log`, `environment.json`,
`verdict.json` (the summary for machines, always `certifying: false`) and
`SHA256SUMS`, which gives the SHA-256 of the other four. The run's summary
page repeats `SHA256SUMS`. The `sha256` in the table is the digest of the
artifact's zip, as GitHub records it.

Workflow artifacts expire after 90 days: the bundle of the run above is
available until 18 February 2027. Bundles will be attached to a tagged release
so that they stay available; `v0.7.0` has no release page yet.

## Run it yourself

```
git clone https://github.com/skiredj-prog/reg-conformance
cd reg-conformance
pip install -r requirements.txt pytest
python -m harness --port harness.ports.reference:ReferencePort --probes --checks
python -m pytest tests/test_harness.py
```

The first command should print `PASS: 15  NOT_APPLICABLE: 1  ADAPTER_REQUIRED: 1  IMPLEMENTATION_GAP: 44`
for the vectors. Unlike the published run, it also runs the property checks.
Of the seventeen property checks, five run on the reference
kernel: four pass and one fails. `PX-CT-R3-001`: the kernel admits a blank
credential, a gap its own register declares. `PX-REG-STATE-001` passes since
v0.7.0: a measurement that is not a finite number (None, NaN, inf) is held as
insufficient evidence, never admitted. The five checks that depend on a
declared bound do not run: the kernel declares none. The reading by candidate
property family follows. The second command checks the instrument: each
effect probe and each property check is run against a deliberately faulty
test double and must report `FAIL`.

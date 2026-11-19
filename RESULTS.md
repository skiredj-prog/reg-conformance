# Published runs

Draft for the author's review.

Each line is one run: one subject revision, one `reg-conformance` commit, one
evidence bundle. Read [`CLAIMS.md`](CLAIMS.md) before quoting any of it. No
line here is a certification.

REG vectors, effect probes and property checks are counted apart. The suite
has 61 REG vectors, 4 effect probes and 17 property checks. From the next
published run on, each line will also give the property checks and the
reading by candidate property family described in `CLAIMS.md`. The run below
predates both.

| Subject | Revision | Level | REG vectors | Effect probes | Run |
|---|---|---|---|---|---|
| Reference kernel bundled in this repository | `reg-conformance` `3023045` | 1, semantic mapping | 14 PASS, 1 not applicable, 41 implementation gaps | not testable: the kernel exposes no observable effect | 16 Nov 2026, on a branch outside this release; artifact `reg-evidence-reference`, `sha256:a6c770d6…f220de`. To be replaced by a run on the v0.7.0 commit. |

The reference kernel is a teaching implementation. Its passes are not results
of the TENIR-Gov runtime or of any product.

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
`SHA256SUMS`.

Workflow artifacts expire after 90 days: the bundle of the run above is
available until 14 February 2027. Bundles will be attached to a tagged release
so that they stay available.

## Run it yourself

```
git clone https://github.com/skiredj-prog/reg-conformance
cd reg-conformance
pip install -r requirements.txt pytest
python -m harness --port harness.ports.reference:ReferencePort --probes --checks
python -m pytest tests/test_harness.py
```

The first command should print `PASS: 15  NOT_APPLICABLE: 1  ADAPTER_REQUIRED: 1  IMPLEMENTATION_GAP: 44`
for the vectors. Of the seventeen property checks, five run on the reference
kernel: three pass and two fail. `PX-CT-R3-001`: the kernel admits a blank
credential, a gap its own register declares. `PX-REG-STATE-001`: it admits an
attempt whose measurement is not a number. The five checks that depend on a
declared bound do not run: the kernel declares none. The reading by candidate
property family follows. The second command checks the instrument: each
effect probe and each property check is run against a deliberately faulty
test double and must report `FAIL`.

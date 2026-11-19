# Reading notes for manuscript v7.2 — vocabulary shared with the REG suite

Status: draft for the author's review, 19 November 2026. Not in force until ratified.

Applies to: *Governing the Unobserved*, manuscript v7.2 (GitHub Release `7.2`,
commit `98bf685`; DOI 10.5281/zenodo.24249646 as stated in this repository).

This note does not edit the manuscript. It changes no result, no count and no
claim of v7.2. It records five items where v7.2 uses a word that the REG
suite and the frozen RFCs use for another object, and says how to read them.
The canonical terms are in [`glossary/glossary-v1.yaml`](../glossary/glossary-v1.yaml).
A later manuscript version may adopt these readings in its own text.

Each item states what was checked. *Verified* means read in the file at the
revision named above; *inferred* means reasoned from the text.

## ERR-7.2-01 — τ_K names two different bounds

**Where.** l.86 (§2.2, fault S2), l.229–230 (§4.4, `admit and await`, `timeout`),
l.383 (§6.1, "clock advance by τ_K"), l.485 (§7.1, S2).

**Text.** In these places τ_K is the time an admitted attempt waits in
`AWAITING` for a qualifying receipt; at t ≥ τ_K the attempt becomes `UNKNOWN`.

**Reading.** Read τ_K at these four places as **τ_R, the receipt qualification
window** (glossary `GL-TAU-R`). In RFC-0 §6, RFC-5 §1 and RN-001 §2a, τ_K is the
organizational veto window, the bound on human resolution of a `HOLD`
(glossary `GL-TAU-K`). The two bounds have different sources and different
exhaustion behaviour: τ_R expiry yields `UNKNOWN`; τ_K exhaustion applies the
pre-declared exhaustion policy.

**Unaffected.** §3.1 (τ_K as a component of Ω) and §9 ("τ_K is a supplied
input" to the composition simulator) use τ_K in the RFC sense. §9 is verified
against `composition/simulator.py`; §3.1 is inferred, since Ω is not exercised
in the paper.

**Effect on results.** None. The S2 scenario and the E1/E2 explorations use one
bound and do not involve a `HOLD` window.

## ERR-7.2-02 — `CT-R4-005` names the harness commit binding, not the suite vector

**Where.** l.10 (changelog 7.1, item 5), l.61 (§1.1, traceability list),
l.647 (§10.1).

**Text.** "`CT-R4-005` (state at verdict). The implemented check binds the
transition and payload hashes at verdict and at commit. Drift of the external
environment between verdict and commit is not captured."

**Reading.** Read `CT-R4-005` here as **the harness commit binding of S11**
(§7.9; glossary `GL-MEM-COMMIT-BINDING`). In the REG suite, vector `CT-R4-005`
tests a change of governance state (`policy_epoch`) between verdict and commit,
and requires no effect under the changed state, with either a terminal refusal
or a suspension carrying a declared resumption condition (RN-001 §4). The
binding of transition and payload is closer to suite vectors `CT-R4-001` and
`CT-R4-002` (inferred).

**Effect on results.** None. The declared limit (environmental drift not
captured) stands as written.

## ERR-7.2-03 — "REG" as a TENIR concern

**Where.** l.120 (§3): "TENIR separates four concerns: … an independent proof
lifecycle (REG) …".

**Reading.** REG is an open, independent standard that describes required
outcomes and does not prescribe a mechanism (glossary `GL-REG`). It is not a
component of TENIR. Read l.120 as: TENIR has a proof-lifecycle concern, which
REG is used to test. The companion "REG Core Protocol" working paper (l.114) is
unaffected.

**Effect on results.** None.

## ERR-7.2-04 — I8 in older suite material

**Where.** §4.5a, §5.3 (I8, attempt-history permanence). No error in v7.2.

**Note for readers of the suite.** Until catalogue v1.1.0 (tag v0.6.2
included), the suite and `tenir_governance` used `I8` for aggregate budget
conservation. The suite now calls that invariant `BUD` (glossary `GL-INV-BUD`).
In any suite file, evidence log or `tenir_governance` text written before the
rename, `I8` means `BUD`, not the manuscript's I8. No suite vector exercises the
manuscript's I8 today.

## ERR-7.2-05 — `FAILED` is a runtime label

**Where.** §4.1 (σ), §4.2, §4.3 (admission guard), §4.4 (transitions), §4.5a
(I3, I5, I7), §5.

**Text.** v7.2 uses `FAILED`, with `RESOLVED`, `PENDING`, `AWAITING`,
`UNKNOWN` and `ESCALATED`, as states of its model.

**Reading.** These are labels of the modelled membrane, not terms of REG's
canonical vocabulary (v6.3, as cited by the author; decision of 19 November
2026). A REG report maps them before stating a recorded state (glossary
`GL-RUNTIME-LABEL`, `GL-STATE-RECORDED`): an attempt never dispatched is
recorded as `CONFIRMED_NONEXECUTION`; an attempt that may have been dispatched
is recorded as `UNKNOWN`, with reconciliation required. Within the paper's own
argument (§4–§5), `FAILED` keeps the meaning the paper gives it, including the
`NEA` condition.

**Open.** v7.2 also reaches `FAILED` after a dispatch, on a verified
non-execution attestation (§4.4, `declare failed (T7)` and `reconcile,
FAILED`). Whether that attestation counts as the reconciliation that allows
`CONFIRMED_NONEXECUTION`, or the record stays `UNKNOWN`, is not decided. This
note does not map that case.

**Effect on results.** None on the paper's results. A REG result quoted from
the paper's runs states its mapped state, or says the label is unmapped.

## Not an erratum: transitions T6 and T8

v7.2 §4.4 names only T7 (`declare failed`). Suite vectors `CT-R4-011` and
`CT-R4-013` cite "manuscript v7.2 §4.4, transition T6 / T8". The fault is in the
suite citations, which will point to `tenir-conformance-s1-g1@8bc0e5e`
(glossary `GL-LIFECYCLE-T`). Likewise, `CT-R4-013` treats `retry_eligible` as an
admission condition, as at revision `8bc0e5e`; v7.2 §4.4 states it is an audit
annotation at `d42499b` and a condition from `8bc0e5e`. Both are correct for
their revision. The labels these transitions use (`RESOLVED`, `FAILED`) are
runtime labels; see ERR-7.2-05.
